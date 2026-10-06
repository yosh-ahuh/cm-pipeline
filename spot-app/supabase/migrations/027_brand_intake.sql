-- 027_brand_intake.sql — ブランド取り込み（Brand Intake）: brands.profile ＋ brand_sources。設計 = docs/brand-intake.md。
--   ・brands.profile: AI が学んだ／ユーザーが確認した「ブランドの理解」（JSONB、§3.1）。確定時に assets.logo/colors へ同期（アプリ側）。
--   ・brand_sources: 取り込み元（URL / 自由記述 / ファイル）。status がそのままキュー（worker の brand_ingest が pending を拾う＝P3）。
--   RLS: org メンバー＝読取（ブランド範囲 brand_visible に従う）、owner/member＝作成・更新・削除。Realtime 公開（読み込み中の進捗表示）。
--   前提: 006〜026 適用済み。冪等。

-- 1) brands.profile
alter table public.brands add column if not exists profile jsonb not null default '{}'::jsonb;

-- 2) brand_sources
create table if not exists public.brand_sources (
  id           uuid primary key default gen_random_uuid(),
  brand_id     uuid not null references public.brands(id) on delete cascade,
  org_id       uuid not null references public.organizations(id) on delete cascade,
  kind         text not null check (kind in ('url', 'text', 'file')),
  url          text,                                   -- kind=url
  text         text,                                   -- kind=text（自由記述）
  storage_path text,                                   -- kind=file（assets バケット: <org_id>/brand/<brand_id>/sources/…）
  file_name    text,
  status       text not null default 'pending' check (status in ('pending', 'running', 'done', 'failed')),
  step         text,                                   -- fetch / extract / summarize（進捗表示用）
  error        text,                                   -- 平易な失敗理由
  extracted    jsonb not null default '{}'::jsonb,     -- 要約・構造化結果のみ（原文は保存しない）
  created_by   uuid references auth.users(id) on delete set null,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);
create index if not exists brand_sources_brand_idx  on public.brand_sources(brand_id);
create index if not exists brand_sources_status_idx on public.brand_sources(status);
drop trigger if exists brand_sources_touch on public.brand_sources;
create trigger brand_sources_touch before update on public.brand_sources
  for each row execute function public.touch_updated_at();

-- org_id は brand から補完（クライアントが省略しても整合する）
create or replace function public.fill_brand_source_org()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if new.org_id is null then select b.org_id into new.org_id from public.brands b where b.id = new.brand_id; end if;
  if new.created_by is null then new.created_by = auth.uid(); end if;
  return new;
end; $$;
drop trigger if exists brand_sources_fill_org on public.brand_sources;
create trigger brand_sources_fill_org before insert on public.brand_sources
  for each row execute function public.fill_brand_source_org();

-- 3) RLS
alter table public.brand_sources enable row level security;
drop policy if exists "member reads brand_sources"   on public.brand_sources;
drop policy if exists "writer inserts brand_sources" on public.brand_sources;
drop policy if exists "writer updates brand_sources" on public.brand_sources;
drop policy if exists "writer deletes brand_sources" on public.brand_sources;
create policy "member reads brand_sources" on public.brand_sources for select
  using (public.is_member(org_id) and public.brand_visible(brand_id));
create policy "writer inserts brand_sources" on public.brand_sources for insert
  with check (public.can_write(org_id) and public.brand_visible(brand_id));
create policy "writer updates brand_sources" on public.brand_sources for update
  using (public.can_write(org_id) and public.brand_visible(brand_id))
  with check (public.can_write(org_id) and public.brand_visible(brand_id));
create policy "writer deletes brand_sources" on public.brand_sources for delete
  using (public.can_write(org_id) and public.brand_visible(brand_id));
grant select, insert, update, delete on public.brand_sources to authenticated;

-- 4) Realtime（読み込み中の進捗）
do $$ begin
  if not exists (select 1 from pg_publication_tables where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'brand_sources') then
    alter publication supabase_realtime add table public.brand_sources;
  end if;
end $$;

-- 5) Storage: 取り込み元ファイルは <org_id>/brand/<brand_id>/sources/… に置く。
--    既存の "assets * member" ポリシー（009）は第1セグメント=org_id で判定するため追加設定は不要。
