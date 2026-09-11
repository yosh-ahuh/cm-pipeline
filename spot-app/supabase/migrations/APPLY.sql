-- APPLY.sql — 002_plans_credits + 003_profile + 004_extra_credits を一括適用（冪等）。SQL Editor に貼って Run。

-- 既存 DB 向け差分。新規は schema.sql をそのまま実行すれば含まれる。

-- ============================================================ plans / credits (002)
-- 課金単位を「スポット」に固定: 1 credit = 1 spot = 完成CM 1本（3パターン×3フォーマット=9ファイル）。
-- 料金設計は ../../spot-marketing.html §09、公開価格は site/content/common.py PLANS と一致させる。
create table if not exists public.plans (
  id              text primary key,             -- free/starter/team/business/enterprise
  name            text not null,
  price_usd       int  not null default 0,
  price_jpy       int  not null default 0,
  spots_per_month numeric not null default 0,   -- 月次付与クレジット（=スポット数）
  seats           int  not null default 1,      -- 0 = 無制限
  brands          int  not null default 1,      -- 0 = 無制限
  extra_spot_usd  numeric not null default 19,  -- 追加スポット単価
  premium_models  boolean not null default false,
  sort            int  not null default 0
);
insert into public.plans (id, name, price_usd, price_jpy, spots_per_month, seats, brands, extra_spot_usd, premium_models, sort) values
  ('free',       'Free',       0,    0,      1,  1, 1,  19, false, 0),
  ('starter',    'Starter',    99,   14800,  6,  2, 1,  19, false, 1),
  ('team',       'Team',       399,  59800,  25, 5, 3,  19, false, 2),
  ('business',   'Business',   1199, 178000, 80, 0, 10, 15, true,  3),
  ('enterprise', 'Enterprise', 2500, 380000, 0,  0, 0,  12, true,  4)
on conflict (id) do update set
  name = excluded.name, price_usd = excluded.price_usd, price_jpy = excluded.price_jpy,
  spots_per_month = excluded.spots_per_month, seats = excluded.seats, brands = excluded.brands,
  extra_spot_usd = excluded.extra_spot_usd, premium_models = excluded.premium_models, sort = excluded.sort;

-- 操作ごとのクレジット消費（UI の定数と一致させる）。
create table if not exists public.credit_costs (
  action  text primary key,                     -- generate / rerender_pattern / regenerate_shot
  credits numeric not null
);
insert into public.credit_costs (action, credits) values
  ('generate', 1), ('rerender_pattern', 0.25), ('regenerate_shot', 0.1)
on conflict (action) do update set credits = excluded.credits;

alter table public.profiles add column if not exists plan text not null default 'free' references public.plans(id);
alter table public.profiles alter column credits set default 1;   -- 旧: 40。新規は free の付与量
alter table public.profiles add column if not exists credits_reset_at timestamptz not null default now();

-- 新規ユーザー: free プランの付与量でスタート（旧 handle_new_user を置換）。
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, display_name, plan, credits)
  values (new.id,
          coalesce(new.raw_user_meta_data->>'display_name', split_part(new.email, '@', 1)),
          'free',
          (select spots_per_month from public.plans where id = 'free'))
  on conflict (id) do nothing;
  return new;
end; $$;

-- profiles.credits / plan はクライアントから直接書き換え不可（RLS の "own profile" が update を許すため、トリガで保護）。
-- 内部関数は set_config('spot.internal','1',true) を立ててから更新する。
create or replace function public.protect_profile_fields()
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
drop trigger if exists protect_profile_fields on public.profiles;
create trigger protect_profile_fields
  before update on public.profiles
  for each row execute function public.protect_profile_fields();

-- 台帳 insert → 残高減算（内部フラグを立てて保護トリガを通す）。
create or replace function public.apply_credit()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  perform set_config('spot.internal', '1', true);
  update public.profiles set credits = credits - coalesce(new.credits, 0) where id = new.owner;
  return new;
end; $$;

-- apply_credit を呼ぶトリガ。旧 002_credits.sql で drop 済みの環境があるため必ず作り直す。
drop trigger if exists on_ledger_insert on public.credit_ledger;
create trigger on_ledger_insert
  after insert on public.credit_ledger
  for each row execute function public.apply_credit();

-- 残高ガード付きの消費 RPC。プロジェクト所有者のみ、行ロックで原子的に判定。
-- 戻り値: true = 消費した / false = 残高不足。
create or replace function public.spend_credits(p_project uuid, p_amount numeric default 1)
returns boolean language plpgsql security definer set search_path = public as $$
declare
  v_owner uuid;
  v_bal   numeric;
begin
  if p_amount is null or p_amount <= 0 then
    raise exception 'invalid amount' using errcode = '22023';
  end if;
  select owner into v_owner from public.projects where id = p_project;
  if v_owner is null or v_owner <> auth.uid() then
    raise exception 'not your project' using errcode = '42501';
  end if;
  select credits into v_bal from public.profiles where id = v_owner for update;
  if v_bal is null or v_bal < p_amount then
    return false;
  end if;
  insert into public.credit_ledger (owner, project_id, stage, model, usd, credits)
  values (v_owner, p_project, 'spend', 'spot', 0, p_amount);   -- apply_credit が減算
  return true;
end; $$;
grant execute on function public.spend_credits(uuid, numeric) to authenticated;

-- 実コスト記録（credits=0）。クライアントは台帳へ直接 insert できないので RPC 経由。
create or replace function public.log_cost(p_project uuid, p_stage text, p_model text, p_usd numeric)
returns void language plpgsql security definer set search_path = public as $$
declare v_owner uuid;
begin
  select owner into v_owner from public.projects where id = p_project;
  if v_owner is null or v_owner <> auth.uid() then
    raise exception 'not your project' using errcode = '42501';
  end if;
  insert into public.credit_ledger (owner, project_id, stage, model, usd, credits)
  values (v_owner, p_project, p_stage, p_model, coalesce(p_usd, 0), 0);
end; $$;
grant execute on function public.log_cost(uuid, text, text, numeric) to authenticated;

-- 月次付与（service_role から cron / 課金 webhook で呼ぶ）。プランの付与量に「リセット」する（繰越なし）。
create or replace function public.reset_monthly_credits()
returns int language plpgsql security definer set search_path = public as $$
declare n int;
begin
  perform set_config('spot.internal', '1', true);
  update public.profiles p set credits = pl.spots_per_month, credits_reset_at = now()
    from public.plans pl where pl.id = p.plan and pl.spots_per_month > 0;
  get diagnostics n = row_count;
  return n;
end; $$;
revoke execute on function public.reset_monthly_credits() from public, authenticated, anon;

-- プラン変更（service_role 専用。課金 webhook から）。残高は新プランの付与量に合わせる。
create or replace function public.set_plan(p_user uuid, p_plan text)
returns void language plpgsql security definer set search_path = public as $$
begin
  perform set_config('spot.internal', '1', true);
  update public.profiles set plan = p_plan, credits = (select spots_per_month from public.plans where id = p_plan),
         credits_reset_at = now() where id = p_user;
end; $$;
revoke execute on function public.set_plan(uuid, text) from public, authenticated, anon;

-- RLS: plans / credit_costs は誰でも閲覧、台帳はクライアント閲覧のみ（書き込みは関数経由）。
alter table public.plans enable row level security;
alter table public.credit_costs enable row level security;
drop policy if exists "plans readable" on public.plans;
create policy "plans readable" on public.plans for select using (true);
drop policy if exists "costs readable" on public.credit_costs;
create policy "costs readable" on public.credit_costs for select using (true);
drop policy if exists "own ledger" on public.credit_ledger;
drop policy if exists "own ledger read" on public.credit_ledger;
create policy "own ledger read" on public.credit_ledger for select using (owner = auth.uid());

-- ==================== 003_profile ====================
-- 003_profile.sql — 表示名の更新用 RPC
-- profiles はクライアントからの直接 UPDATE を許可していない（credits/plan 保護）ため、
-- 表示名だけを安全に更新する SECURITY DEFINER 関数を用意する。
-- 適用: Supabase Studio → SQL Editor に貼って Run。

create or replace function public.update_display_name(p_name text)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.profiles
     set display_name = nullif(btrim(p_name), '')
   where id = auth.uid();
end;
$$;

grant execute on function public.update_display_name(text) to authenticated;

-- ==================== 004_extra_credits ====================
-- 004_extra_credits.sql — 追加スポット購入でクレジットを加算する RPC（service_role 専用）
-- Stripe Webhook（worker/stripe_webhook.py）から呼ぶ。適用: SQL Editor で Run（APPLY.sql に同梱済み）。

create or replace function public.add_credits(p_user uuid, p_amount numeric)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  if p_amount is null or p_amount <= 0 then
    raise exception 'invalid amount' using errcode = '22023';
  end if;
  perform set_config('spot.internal', '1', true);   -- 保護トリガを通す
  update public.profiles set credits = credits + p_amount where id = p_user;
end;
$$;

revoke execute on function public.add_credits(uuid, numeric) from public, authenticated, anon;
