-- 011_collections.sql — コレクション（フォルダ式）。006〜010 適用後。冪等。
--   1 動画(project) は 0/1 コレクションに所属（projects.collection_id, nullable）。
--   コレクション削除時は動画は残り collection_id=null（＝未分類）に戻る。
--   org 単位。参照=メンバー、作成/リネーム/削除=can_write(owner/member)。移動は projects の更新RLSで担保。

create table if not exists public.collections (
  id         uuid primary key default gen_random_uuid(),
  org_id     uuid not null references public.organizations(id) on delete cascade,
  name       text not null,
  created_at timestamptz not null default now()
);
create index if not exists collections_org_idx on public.collections(org_id);

alter table public.projects add column if not exists collection_id uuid references public.collections(id) on delete set null;
create index if not exists projects_collection_idx on public.projects(collection_id);

alter table public.collections enable row level security;
drop policy if exists "member reads collections" on public.collections;
create policy "member reads collections" on public.collections for select
  using (public.is_member(org_id));
drop policy if exists "writer writes collections" on public.collections;
create policy "writer writes collections" on public.collections for all
  using (public.can_write(org_id)) with check (public.can_write(org_id));
