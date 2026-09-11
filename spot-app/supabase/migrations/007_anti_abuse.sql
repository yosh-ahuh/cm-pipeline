-- 007_anti_abuse.sql — アカウント共有の検知（Phase C）＋ドメイン参加/brands実効化（Phase D）。
-- 設計: docs/multi-seat-design.md。006_orgs.sql を先に適用しておくこと。冪等。
--
-- ここで“コードで完結する”のは: ログイン記録 / 共有検知（デバイス数）/ ソフト誘導の材料 /
--   メール確認(OTP)の判定材料 / ドメイン自動参加 / brands 上限の実効化。
-- ★コードで完結しない（Supabase コンソール or Edge Function 側の作業。設計書 §4層C/§6 参照）:
--   ・新デバイス“強制”OTP … Supabase Auth の設定 or Edge Function（本SQLは「新デバイス判定」までを提供）。
--   ・同時セッションの“強制失効” … service_role の Admin API（worker/Edge）で実施。
--   ・SAML SSO … Supabase の Enterprise 設定。

-- ============================================================ 1. ログイン記録（共有検知の源）
create table if not exists public.login_events (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references auth.users(id) on delete cascade,
  device_id  text,                    -- クライアント生成の端末id（localStorage 永続）
  user_agent text,
  created_at timestamptz not null default now()
);
create index if not exists login_events_user_idx on public.login_events(user_id, created_at desc);
alter table public.login_events enable row level security;
drop policy if exists "own login events" on public.login_events;
create policy "own login events" on public.login_events for select using (user_id = auth.uid());

-- サインイン時にクライアントから呼ぶ。戻り値 = その端末が「新規デバイスか」。
create or replace function public.record_login(p_device text, p_ua text default null)
returns boolean language plpgsql security definer set search_path = public as $$
declare v_seen boolean;
begin
  select exists(select 1 from public.login_events
                where user_id = auth.uid() and device_id = p_device) into v_seen;
  insert into public.login_events (user_id, device_id, user_agent) values (auth.uid(), p_device, p_ua);
  return not v_seen;   -- true = 新デバイス（＝OTP等ステップアップの判定材料）
end; $$;
grant execute on function public.record_login(text, text) to authenticated;

-- 直近30日の distinct デバイス数（共有の主要シグナル）。ソフト誘導バナーの判定に使う。
create or replace function public.login_device_count(p_days int default 30)
returns int language sql security definer stable set search_path = public as $$
  select count(distinct device_id)::int from public.login_events
  where user_id = auth.uid() and device_id is not null
    and created_at > now() - make_interval(days => greatest(1, p_days));
$$;
grant execute on function public.login_device_count(int) to authenticated;

-- ============================================================ 2. ドメイン自動参加（Phase D の SSO 簡易版）
alter table public.organizations add column if not exists email_domain text;   -- 例: 'company.com'（小文字）
create unique index if not exists organizations_domain_uk
  on public.organizations(email_domain) where email_domain is not null;

-- オーナーが自組織のメール・ドメインを設定/解除（同ドメインの新規サインアップが member 参加になる）。
create or replace function public.set_org_domain(p_org uuid, p_domain text)
returns void language plpgsql security definer set search_path = public as $$
begin
  if public.member_role(p_org) <> 'owner' then
    raise exception 'only owner can set domain' using errcode = '42501';
  end if;
  update public.organizations set email_domain = nullif(btrim(lower(p_domain)), '') where id = p_org;
end; $$;
grant execute on function public.set_org_domain(uuid, text) to authenticated;

-- 新規ユーザー: 個人org生成に加え、メールのドメインが一致する org があれば member 参加（席数内のみ）。
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
declare v_org uuid; v_name text; v_domain text; v_dorg uuid; v_seats int; v_used int;
begin
  v_name := coalesce(new.raw_user_meta_data->>'display_name', split_part(new.email, '@', 1));
  insert into public.profiles (id, display_name, plan, credits)
  values (new.id, v_name, 'free', (select spots_per_month from public.plans where id = 'free'))
  on conflict (id) do nothing;

  -- 個人org（未作成のみ）
  if not exists (select 1 from public.organizations where owner_user_id = new.id and is_personal) then
    insert into public.organizations (name, plan, credits, credits_reset_at, owner_user_id, is_personal)
    values (v_name, 'free', (select spots_per_month from public.plans where id = 'free'), now(), new.id, true)
    returning id into v_org;
    insert into public.org_members (org_id, user_id, role) values (v_org, new.id, 'owner')
    on conflict (org_id, user_id) do nothing;
  end if;

  -- ドメイン自動参加（席が空いていれば member として）
  v_domain := lower(split_part(new.email, '@', 2));
  if v_domain <> '' then
    select id into v_dorg from public.organizations where email_domain = v_domain limit 1;
    if v_dorg is not null then
      select pl.seats into v_seats from public.organizations o join public.plans pl on pl.id = o.plan where o.id = v_dorg;
      select count(*) into v_used from public.org_members where org_id = v_dorg and role in ('owner','member');
      if coalesce(v_seats,1) = 0 or v_used < v_seats then
        insert into public.org_members (org_id, user_id, role) values (v_dorg, new.id, 'member')
        on conflict (org_id, user_id) do nothing;
      end if;
    end if;
  end if;
  return new;
end; $$;

-- ============================================================ 3. brands 上限の実効化（Phase D）
create or replace function public.create_brand(p_org uuid, p_name text, p_assets jsonb default '{}'::jsonb)
returns uuid language plpgsql security definer set search_path = public as $$
declare v_max int; v_used int; v_id uuid;
begin
  if not public.can_write(p_org) then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  select pl.brands into v_max from public.organizations o join public.plans pl on pl.id = o.plan where o.id = p_org;
  if coalesce(v_max, 1) <> 0 then    -- 0 = 無制限
    select count(*) into v_used from public.brands where org_id = p_org;
    if v_used >= v_max then
      raise exception 'brand limit reached' using errcode = '53400';
    end if;
  end if;
  insert into public.brands (org_id, name, assets) values (p_org, p_name, coalesce(p_assets, '{}'::jsonb))
  returning id into v_id;
  return v_id;
end; $$;
grant execute on function public.create_brand(uuid, text, jsonb) to authenticated;
