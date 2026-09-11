-- 006_orgs.sql — マルチシート基盤（organizations / members / invites / brands）。
-- 設計: docs/multi-seat-design.md（確定版）。冪等。既存DB（005までの profiles/plans/credits）に対する差分。
-- 適用: Supabase Studio → SQL Editor に貼って Run（前回 APPLY.sql と同じ手順）。
--
-- 要点:
--  ・課金主体とクレジット残高を profiles(個人) → organizations(組織) に移す（プール化）。
--  ・projects/generations/jobs/renders/credit_ledger に org_id を付与し、RLS を「所属orgのメンバー」に切替。
--  ・ロールは owner/member/viewer の3段。viewer は席数カウント外（無料・無制限）。
--  ・spend_credits / log_cost はシグネチャ維持（project 起点）＝フロント無改修。中身を org 基準に置換。
--  ・既存ユーザーには個人 org を自動生成してデータをバックフィル（壊さない）。

-- ============================================================ 1. テーブル
create table if not exists public.organizations (
  id               uuid primary key default gen_random_uuid(),
  name             text not null default 'My workspace',
  plan             text not null default 'free' references public.plans(id),
  credits          numeric not null default 1,
  credits_reset_at timestamptz not null default now(),
  owner_user_id    uuid not null references auth.users(id) on delete cascade,
  is_personal      boolean not null default false,
  created_at       timestamptz not null default now()
);
-- 1ユーザー1個の個人org（バックフィル冪等化の要）。
create unique index if not exists organizations_personal_uk
  on public.organizations(owner_user_id) where is_personal;

create table if not exists public.org_members (
  org_id   uuid not null references public.organizations(id) on delete cascade,
  user_id  uuid not null references auth.users(id) on delete cascade,
  role     text not null default 'member' check (role in ('owner','member','viewer')),
  added_at timestamptz not null default now(),
  primary key (org_id, user_id)
);
create index if not exists org_members_user_idx on public.org_members(user_id);

create table if not exists public.org_invites (
  id          uuid primary key default gen_random_uuid(),
  org_id      uuid not null references public.organizations(id) on delete cascade,
  email       text,                                   -- 招待先（任意。リンク招待は null 可）
  role        text not null default 'member' check (role in ('member','viewer')),
  token       text not null unique,                   -- 推測不能トークン（リンク用）
  invited_by  uuid references auth.users(id),
  expires_at  timestamptz not null default now() + interval '7 days',
  accepted_at timestamptz,
  created_at  timestamptz not null default now()
);
create index if not exists org_invites_org_idx on public.org_invites(org_id);

create table if not exists public.brands (
  id         uuid primary key default gen_random_uuid(),
  org_id     uuid not null references public.organizations(id) on delete cascade,
  name       text not null,
  assets     jsonb not null default '{}'::jsonb,      -- app_icon / logo / colors 等
  created_at timestamptz not null default now()
);
create index if not exists brands_org_idx on public.brands(org_id);

-- 既存テーブルに org_id（+ projects.brand_id）を付与。
alter table public.projects      add column if not exists org_id uuid references public.organizations(id) on delete cascade;
alter table public.projects      add column if not exists brand_id uuid references public.brands(id) on delete set null;
alter table public.generations   add column if not exists org_id uuid references public.organizations(id) on delete cascade;
alter table public.jobs          add column if not exists org_id uuid references public.organizations(id) on delete cascade;
alter table public.renders       add column if not exists org_id uuid references public.organizations(id) on delete cascade;
alter table public.credit_ledger add column if not exists org_id uuid references public.organizations(id) on delete set null;
create index if not exists projects_org_idx      on public.projects(org_id);
create index if not exists generations_org_idx   on public.generations(org_id);
create index if not exists jobs_org_idx          on public.jobs(org_id);
create index if not exists renders_org_idx        on public.renders(org_id);
create index if not exists ledger_org_idx        on public.credit_ledger(org_id);

-- ============================================================ 2. ヘルパ関数（SECURITY DEFINER＝RLS再帰回避）
create or replace function public.is_member(p_org uuid)
returns boolean language sql security definer stable set search_path = public as $$
  select exists(select 1 from public.org_members where org_id = p_org and user_id = auth.uid());
$$;

create or replace function public.member_role(p_org uuid)
returns text language sql security definer stable set search_path = public as $$
  select role from public.org_members where org_id = p_org and user_id = auth.uid();
$$;

-- 生成・編集ができる（viewer 以外）。
create or replace function public.can_write(p_org uuid)
returns boolean language sql security definer stable set search_path = public as $$
  select exists(select 1 from public.org_members
                where org_id = p_org and user_id = auth.uid() and role in ('owner','member'));
$$;

-- 個人 org を返す（自動 org_id 補完に使用）。
create or replace function public.personal_org(p_user uuid)
returns uuid language sql security definer stable set search_path = public as $$
  select id from public.organizations where owner_user_id = p_user and is_personal limit 1;
$$;

grant execute on function public.is_member(uuid)     to authenticated;
grant execute on function public.member_role(uuid)   to authenticated;
grant execute on function public.can_write(uuid)     to authenticated;

-- ============================================================ 3. 既存ユーザーの移行（個人org生成＋バックフィル）
-- 3-1. 各 profile に個人 org を作成（未作成のみ）。plan/credits を profiles から引き継ぐ。
insert into public.organizations (name, plan, credits, credits_reset_at, owner_user_id, is_personal)
select coalesce(p.display_name, 'My workspace'),
       coalesce(p.plan, 'free'),
       coalesce(p.credits, (select spots_per_month from public.plans where id = 'free')),
       coalesce(p.credits_reset_at, now()),
       p.id, true
from public.profiles p
where not exists (select 1 from public.organizations o where o.owner_user_id = p.id and o.is_personal);

-- 3-2. owner メンバーシップ。
insert into public.org_members (org_id, user_id, role)
select o.id, o.owner_user_id, 'owner'
from public.organizations o where o.is_personal
on conflict (org_id, user_id) do nothing;

-- 3-3. 既存データの org_id を所有者の個人 org でバックフィル。
update public.projects      t set org_id = personal_org(t.owner) where t.org_id is null;
update public.generations   t set org_id = personal_org(t.owner) where t.org_id is null;
update public.jobs          t set org_id = personal_org(t.owner) where t.org_id is null;
update public.renders       t set org_id = personal_org(t.owner) where t.org_id is null;
update public.credit_ledger t set org_id = personal_org(t.owner) where t.org_id is null;

-- ============================================================ 4. org_id 自動補完トリガ（後方互換）
-- クライアント/ワーカーが org_id を渡さない場合、owner の個人 org を補完（既存フロント無改修で動く）。
create or replace function public.fill_org_id()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if new.org_id is null then
    new.org_id := personal_org(coalesce(new.owner, auth.uid()));
  end if;
  return new;
end; $$;
do $$ declare t text;
begin
  foreach t in array array['projects','generations','jobs','renders'] loop
    execute format('drop trigger if exists fill_org_id on public.%I', t);
    execute format('create trigger fill_org_id before insert on public.%I for each row execute function public.fill_org_id()', t);
  end loop;
end $$;

-- ============================================================ 5. 新規ユーザー: profiles＋個人org＋ownerメンバー
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
declare v_org uuid; v_name text;
begin
  v_name := coalesce(new.raw_user_meta_data->>'display_name', split_part(new.email, '@', 1));
  insert into public.profiles (id, display_name, plan, credits)
  values (new.id, v_name, 'free', (select spots_per_month from public.plans where id = 'free'))
  on conflict (id) do nothing;

  if not exists (select 1 from public.organizations where owner_user_id = new.id and is_personal) then
    insert into public.organizations (name, plan, credits, credits_reset_at, owner_user_id, is_personal)
    values (v_name, 'free', (select spots_per_month from public.plans where id = 'free'), now(), new.id, true)
    returning id into v_org;
    insert into public.org_members (org_id, user_id, role) values (v_org, new.id, 'owner')
    on conflict (org_id, user_id) do nothing;
  end if;
  return new;
end; $$;

-- ============================================================ 6. クレジットは org 残高を減算
-- 6-1. organizations.credits/plan の保護（クライアント直更新不可。内部フラグ経由のみ）。
create or replace function public.protect_org_fields()
returns trigger language plpgsql as $$
begin
  if coalesce(current_setting('spot.internal', true), '') <> '1'
     and (new.credits is distinct from old.credits
          or new.plan is distinct from old.plan
          or new.credits_reset_at is distinct from old.credits_reset_at) then
    raise exception 'credits/plan are managed by the server' using errcode = '42501';
  end if;
  return new;
end; $$;
drop trigger if exists protect_org_fields on public.organizations;
create trigger protect_org_fields before update on public.organizations
  for each row execute function public.protect_org_fields();

-- 6-2. 台帳 insert → org 残高を減算（org_id 基準に置換）。
create or replace function public.apply_credit()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  perform set_config('spot.internal', '1', true);
  if new.org_id is not null then
    update public.organizations set credits = credits - coalesce(new.credits, 0) where id = new.org_id;
  end if;
  return new;
end; $$;
drop trigger if exists on_ledger_insert on public.credit_ledger;
create trigger on_ledger_insert after insert on public.credit_ledger
  for each row execute function public.apply_credit();

-- ============================================================ 7. RPC（org 基準に置換。spend/log はシグネチャ維持）
-- 7-1. 消費（project 起点）。呼び出し者が can_write のメンバーであること＋org残高で判定。
create or replace function public.spend_credits(p_project uuid, p_amount numeric default 1)
returns boolean language plpgsql security definer set search_path = public as $$
declare v_org uuid; v_bal numeric;
begin
  if p_amount is null or p_amount <= 0 then
    raise exception 'invalid amount' using errcode = '22023';
  end if;
  select org_id into v_org from public.projects where id = p_project;
  if v_org is null or not public.can_write(v_org) then
    raise exception 'not allowed for this project' using errcode = '42501';
  end if;
  select credits into v_bal from public.organizations where id = v_org for update;
  if v_bal is null or v_bal < p_amount then
    return false;
  end if;
  insert into public.credit_ledger (owner, org_id, project_id, stage, model, usd, credits)
  values (auth.uid(), v_org, p_project, 'spend', 'spot', 0, p_amount);   -- apply_credit が減算
  return true;
end; $$;
grant execute on function public.spend_credits(uuid, numeric) to authenticated;

-- 7-2. 実コスト記録（credits=0）。
create or replace function public.log_cost(p_project uuid, p_stage text, p_model text, p_usd numeric)
returns void language plpgsql security definer set search_path = public as $$
declare v_org uuid;
begin
  select org_id into v_org from public.projects where id = p_project;
  if v_org is null or not public.can_write(v_org) then
    raise exception 'not allowed for this project' using errcode = '42501';
  end if;
  insert into public.credit_ledger (owner, org_id, project_id, stage, model, usd, credits)
  values (auth.uid(), v_org, p_project, p_stage, p_model, coalesce(p_usd, 0), 0);
end; $$;
grant execute on function public.log_cost(uuid, text, text, numeric) to authenticated;

-- 7-3. 月次リセット / プラン変更 / 追加クレジット は org 基準（service_role 専用）。
create or replace function public.reset_monthly_credits()
returns int language plpgsql security definer set search_path = public as $$
declare n int;
begin
  perform set_config('spot.internal', '1', true);
  update public.organizations o set credits = pl.spots_per_month, credits_reset_at = now()
    from public.plans pl where pl.id = o.plan and pl.spots_per_month > 0;
  get diagnostics n = row_count;
  return n;
end; $$;
revoke execute on function public.reset_monthly_credits() from public, authenticated, anon;

-- 旧 set_plan(p_user uuid, ...) と同シグネチャで引数名が変わるため drop してから作り直す。
drop function if exists public.set_plan(uuid, text);
create or replace function public.set_plan(p_org uuid, p_plan text)
returns void language plpgsql security definer set search_path = public as $$
begin
  perform set_config('spot.internal', '1', true);
  update public.organizations set plan = p_plan,
         credits = (select spots_per_month from public.plans where id = p_plan),
         credits_reset_at = now()
   where id = p_org;
end; $$;
revoke execute on function public.set_plan(uuid, text) from public, authenticated, anon;

-- 旧 add_credits(p_user uuid, ...) と同シグネチャで引数名が変わるため drop してから作り直す。
drop function if exists public.add_credits(uuid, numeric);
create or replace function public.add_credits(p_org uuid, p_amount numeric)
returns void language plpgsql security definer set search_path = public as $$
begin
  if p_amount is null or p_amount <= 0 then
    raise exception 'invalid amount' using errcode = '22023';
  end if;
  perform set_config('spot.internal', '1', true);
  update public.organizations set credits = credits + p_amount where id = p_org;
end; $$;
revoke execute on function public.add_credits(uuid, numeric) from public, authenticated, anon;

-- ============================================================ 8. 招待 / メンバー管理 RPC
-- 8-1. 招待作成（owner のみ）。トークンを返す＝招待リンク末尾に使う。
create or replace function public.create_invite(p_org uuid, p_email text default null, p_role text default 'member')
returns text language plpgsql security definer set search_path = public as $$
declare v_token text;
begin
  if public.member_role(p_org) <> 'owner' then
    raise exception 'only owner can invite' using errcode = '42501';
  end if;
  if p_role not in ('member','viewer') then
    raise exception 'invalid role' using errcode = '22023';
  end if;
  -- 推測不能トークン（pgcrypto 非依存: uuid 2連結 = 64 hex）。
  v_token := replace(gen_random_uuid()::text, '-', '') || replace(gen_random_uuid()::text, '-', '');
  insert into public.org_invites (org_id, email, role, token, invited_by)
  values (p_org, nullif(btrim(lower(p_email)), ''), p_role, v_token, auth.uid());
  return v_token;
end; $$;
grant execute on function public.create_invite(uuid, text, text) to authenticated;

-- 8-2. 招待の内容表示（accept 画面用。メンバーでなくても token で org 名/役割を見られる）。
create or replace function public.get_invite(p_token text)
returns table(org_id uuid, org_name text, role text, expired boolean, accepted boolean)
language sql security definer stable set search_path = public as $$
  select i.org_id, o.name, i.role, (i.expires_at < now()), (i.accepted_at is not null)
  from public.org_invites i join public.organizations o on o.id = i.org_id
  where i.token = p_token;
$$;
grant execute on function public.get_invite(text) to authenticated, anon;

-- 8-3. 招待受諾（席数を原子的にチェック。viewer はカウント外）。
create or replace function public.accept_invite(p_token text)
returns uuid language plpgsql security definer set search_path = public as $$
declare v_inv public.org_invites; v_seats int; v_used int;
begin
  select * into v_inv from public.org_invites where token = p_token for update;
  if v_inv.id is null then raise exception 'invite not found' using errcode = 'P0002'; end if;
  if v_inv.accepted_at is not null then raise exception 'invite already used' using errcode = '22023'; end if;
  if v_inv.expires_at < now() then raise exception 'invite expired' using errcode = '22023'; end if;

  -- owner/member は席を消費。viewer は無制限。
  if v_inv.role <> 'viewer' then
    select pl.seats into v_seats from public.organizations o join public.plans pl on pl.id = o.plan
      where o.id = v_inv.org_id;
    if coalesce(v_seats, 1) <> 0 then    -- 0 = 無制限
      select count(*) into v_used from public.org_members
        where org_id = v_inv.org_id and role in ('owner','member');
      if v_used >= v_seats then
        raise exception 'seat limit reached' using errcode = '53400';
      end if;
    end if;
  end if;

  insert into public.org_members (org_id, user_id, role)
  values (v_inv.org_id, auth.uid(), v_inv.role)
  on conflict (org_id, user_id) do update set role = excluded.role;
  update public.org_invites set accepted_at = now() where id = v_inv.id;
  return v_inv.org_id;
end; $$;
grant execute on function public.accept_invite(text) to authenticated;

-- 8-4. メンバー削除（owner のみ。最後の owner は消せない）。
create or replace function public.remove_member(p_org uuid, p_user uuid)
returns void language plpgsql security definer set search_path = public as $$
begin
  if public.member_role(p_org) <> 'owner' then
    raise exception 'only owner can remove members' using errcode = '42501';
  end if;
  if (select role from public.org_members where org_id = p_org and user_id = p_user) = 'owner'
     and (select count(*) from public.org_members where org_id = p_org and role = 'owner') <= 1 then
    raise exception 'cannot remove the last owner' using errcode = '42501';
  end if;
  delete from public.org_members where org_id = p_org and user_id = p_user;
end; $$;
grant execute on function public.remove_member(uuid, uuid) to authenticated;

-- 8-5. メンバー一覧（表示名つき）。org メンバーのみ閲覧可。
create or replace function public.list_members(p_org uuid)
returns table(user_id uuid, display_name text, role text, added_at timestamptz)
language sql security definer stable set search_path = public as $$
  select m.user_id, p.display_name, m.role, m.added_at
  from public.org_members m left join public.profiles p on p.id = m.user_id
  where m.org_id = p_org and public.is_member(p_org)
  order by (m.role = 'owner') desc, m.added_at;
$$;
grant execute on function public.list_members(uuid) to authenticated;

-- ============================================================ 9. RLS 切替（owner=auth.uid → org メンバー）
alter table public.organizations enable row level security;
alter table public.org_members   enable row level security;
alter table public.org_invites   enable row level security;
alter table public.brands        enable row level security;

drop policy if exists "member reads org" on public.organizations;
create policy "member reads org" on public.organizations for select using (public.is_member(id));
drop policy if exists "owner renames org" on public.organizations;
create policy "owner renames org" on public.organizations for update
  using (public.member_role(id) = 'owner') with check (public.member_role(id) = 'owner');

drop policy if exists "member reads members" on public.org_members;
create policy "member reads members" on public.org_members for select using (public.is_member(org_id));
-- 追加/削除は RPC（security definer）経由のみ。直接 insert/delete/update は不可（ポリシー無し＝拒否）。

drop policy if exists "owner reads invites" on public.org_invites;
create policy "owner reads invites" on public.org_invites for select using (public.member_role(org_id) = 'owner');
-- 作成/受諾は RPC 経由。

drop policy if exists "member reads brands" on public.brands;
create policy "member reads brands" on public.brands for select using (public.is_member(org_id));
drop policy if exists "writer writes brands" on public.brands;
create policy "writer writes brands" on public.brands for all
  using (public.can_write(org_id)) with check (public.can_write(org_id));

-- projects/generations/jobs/renders: 参照=メンバー、書込=can_write（viewer は読取専用）。
drop policy if exists "own projects" on public.projects;
drop policy if exists "member reads projects" on public.projects;
drop policy if exists "writer writes projects" on public.projects;
create policy "member reads projects" on public.projects for select using (public.is_member(org_id));
create policy "writer writes projects" on public.projects for all
  using (public.can_write(org_id)) with check (public.can_write(org_id));

drop policy if exists "own generations" on public.generations;
drop policy if exists "member reads generations" on public.generations;
drop policy if exists "writer writes generations" on public.generations;
create policy "member reads generations" on public.generations for select using (public.is_member(org_id));
create policy "writer writes generations" on public.generations for all
  using (public.can_write(org_id)) with check (public.can_write(org_id));

drop policy if exists "own jobs" on public.jobs;
drop policy if exists "member reads jobs" on public.jobs;
drop policy if exists "writer writes jobs" on public.jobs;
create policy "member reads jobs" on public.jobs for select using (public.is_member(org_id));
create policy "writer writes jobs" on public.jobs for all
  using (public.can_write(org_id)) with check (public.can_write(org_id));

drop policy if exists "own renders" on public.renders;
drop policy if exists "member reads renders" on public.renders;
drop policy if exists "writer writes renders" on public.renders;
create policy "member reads renders" on public.renders for select using (public.is_member(org_id));
create policy "writer writes renders" on public.renders for all
  using (public.can_write(org_id)) with check (public.can_write(org_id));

-- credit_ledger: 参照はメンバー（書込は RPC のみ）。
drop policy if exists "own ledger" on public.credit_ledger;
drop policy if exists "own ledger read" on public.credit_ledger;
drop policy if exists "member reads ledger" on public.credit_ledger;
create policy "member reads ledger" on public.credit_ledger for select using (public.is_member(org_id));

-- ============================================================ 10. Realtime
-- jobs/generations は既に publication 済み。org_members を追加（招待受諾の即時反映）。
do $$ begin
  if not exists (select 1 from pg_publication_tables
                 where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'org_members') then
    alter publication supabase_realtime add table public.org_members;
  end if;
end $$;
