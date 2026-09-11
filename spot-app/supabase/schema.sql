-- SPOT — Supabase スキーマ（Phase 2 データ層）
-- architecture.md のデータモデルを Postgres + RLS で表現。
-- project.yaml は projects.spec(jsonb) に「単一の真実」として持つ。
-- 適用: Supabase Studio の SQL Editor に貼り付けて実行（または supabase db push）。

-- ============================================================ profiles
-- auth.users を拡張。表示名とクレジット残を持つ。
create table if not exists public.profiles (
  id           uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  credits      numeric not null default 40,          -- 初期付与（UIの 18.5/40 と対応）
  created_at   timestamptz not null default now()
);

-- 新規ユーザー作成時に profiles を自動生成（starter クレジット付き）。
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, display_name)
  values (new.id, coalesce(new.raw_user_meta_data->>'display_name', split_part(new.email, '@', 1)))
  on conflict (id) do nothing;
  return new;
end; $$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ============================================================ projects
-- 1 CM = 1 project。spec に project.yaml 相当の JSON を持つ。
create table if not exists public.projects (
  id         uuid primary key default gen_random_uuid(),
  owner      uuid not null default auth.uid() references auth.users(id) on delete cascade,
  name       text not null,
  product    text,
  status     text not null default 'draft',   -- draft/generating/review/done
  spec       jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists projects_owner_idx on public.projects(owner);

-- ============================================================ generations
-- スチル/クリップ/音声の生成物（version 付き）。実体は Storage、ここは台帳。
create table if not exists public.generations (
  id           uuid primary key default gen_random_uuid(),
  project_id   uuid not null references public.projects(id) on delete cascade,
  owner        uuid not null default auth.uid() references auth.users(id) on delete cascade,
  cut          text,
  kind         text,                            -- still/clip/audio/render
  version      int not null default 1,
  storage_path text,                            -- assets バケット内のパス
  model        text,
  usd          numeric not null default 0,
  status       text not null default 'pending', -- pending/done/failed
  created_at   timestamptz not null default now()
);
create index if not exists generations_project_idx on public.generations(project_id);

-- ============================================================ jobs
-- 非同期ジョブ（Realtime 進捗の源）。cm-pipeline の DAG と対応。
create table if not exists public.jobs (
  id         uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  owner      uuid not null default auth.uid() references auth.users(id) on delete cascade,
  stage      text not null,                     -- still/review/animate/audio/build
  cut        text,
  status     text not null default 'pending',   -- pending/running/done/skipped/failed/blocked
  usd        numeric not null default 0,
  retries    int not null default 0,
  deps       text[] not null default '{}',
  detail     jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists jobs_project_idx on public.jobs(project_id);
create index if not exists jobs_status_idx on public.jobs(status);

-- ============================================================ renders
-- 最終書き出し（variant × format）の mp4。
create table if not exists public.renders (
  id           uuid primary key default gen_random_uuid(),
  project_id   uuid not null references public.projects(id) on delete cascade,
  owner        uuid not null default auth.uid() references auth.users(id) on delete cascade,
  variant      text,
  format       text,
  storage_path text,
  created_at   timestamptz not null default now()
);
create index if not exists renders_project_idx on public.renders(project_id);

-- ============================================================ credit_ledger
-- 各生成の実コストを積む → profiles.credits を減算。
create table if not exists public.credit_ledger (
  id         uuid primary key default gen_random_uuid(),
  owner      uuid not null default auth.uid() references auth.users(id) on delete cascade,
  project_id uuid references public.projects(id) on delete set null,
  stage      text,
  model      text,
  usd        numeric not null default 0,
  credits    numeric not null default 0,
  created_at timestamptz not null default now()
);
create index if not exists ledger_owner_idx on public.credit_ledger(owner);

-- 台帳 insert でクレジット残を減算（ライブ残高）。
create or replace function public.apply_credit()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  update public.profiles set credits = credits - coalesce(new.credits, 0) where id = new.owner;
  return new;
end; $$;
drop trigger if exists on_ledger_insert on public.credit_ledger;
create trigger on_ledger_insert
  after insert on public.credit_ledger
  for each row execute function public.apply_credit();

-- ============================================================ updated_at
create or replace function public.touch_updated_at()
returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end; $$;
drop trigger if exists projects_touch on public.projects;
create trigger projects_touch before update on public.projects
  for each row execute function public.touch_updated_at();
drop trigger if exists jobs_touch on public.jobs;
create trigger jobs_touch before update on public.jobs
  for each row execute function public.touch_updated_at();

-- ============================================================ RLS
-- 所有者だけが自分の行を読み書き。ワーカーは service_role で RLS を貫通。
alter table public.profiles      enable row level security;
alter table public.projects      enable row level security;
alter table public.generations   enable row level security;
alter table public.jobs          enable row level security;
alter table public.renders       enable row level security;
alter table public.credit_ledger enable row level security;

create policy "own profile"      on public.profiles      for all using (id = auth.uid())    with check (id = auth.uid());
create policy "own projects"     on public.projects      for all using (owner = auth.uid()) with check (owner = auth.uid());
create policy "own generations"  on public.generations   for all using (owner = auth.uid()) with check (owner = auth.uid());
create policy "own jobs"         on public.jobs          for all using (owner = auth.uid()) with check (owner = auth.uid());
create policy "own renders"      on public.renders       for all using (owner = auth.uid()) with check (owner = auth.uid());
create policy "own ledger"       on public.credit_ledger for all using (owner = auth.uid()) with check (owner = auth.uid());

-- ============================================================ Realtime
-- jobs / generations の変更をクライアントが購読できるように公開。
alter publication supabase_realtime add table public.jobs;
alter publication supabase_realtime add table public.generations;

-- ============================================================ Storage
-- 生成物バケット（非公開）。パス規約: <owner_id>/<project_id>/<file>
insert into storage.buckets (id, name, public)
values ('assets', 'assets', false)
on conflict (id) do nothing;

create policy "assets read own"   on storage.objects for select
  using (bucket_id = 'assets' and (storage.foldername(name))[1] = auth.uid()::text);
create policy "assets write own"  on storage.objects for insert
  with check (bucket_id = 'assets' and (storage.foldername(name))[1] = auth.uid()::text);
create policy "assets update own" on storage.objects for update
  using (bucket_id = 'assets' and (storage.foldername(name))[1] = auth.uid()::text);
create policy "assets delete own" on storage.objects for delete
  using (bucket_id = 'assets' and (storage.foldername(name))[1] = auth.uid()::text);

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
