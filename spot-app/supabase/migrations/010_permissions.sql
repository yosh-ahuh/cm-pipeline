-- 010_permissions.sql — 権限の是正（決定事項）。006〜009 適用後。冪等。
--   ・プロジェクト削除は「オーナーのみ」（従来は member も可だった）。
--   ・生成物ファイルの可視性（レガシー問題）を解決：Storage 読取を「行(generations/renders)の org」で判定
--     → パスが旧 <user_id>/ でも、その行の org のメンバーなら開ける（org が唯一の真実）。

-- ============================================================ 1. is_owner ヘルパ
create or replace function public.is_owner(p_org uuid)
returns boolean language sql security definer stable set search_path = public as $$
  select exists(select 1 from public.org_members where org_id = p_org and user_id = auth.uid() and role = 'owner');
$$;
grant execute on function public.is_owner(uuid) to authenticated;

-- ============================================================ 2. projects: 削除はオーナーのみ
-- 従来の "writer writes projects"(FOR ALL=can_write) を粒度分割する。
drop policy if exists "writer writes projects" on public.projects;
drop policy if exists "writer inserts projects" on public.projects;
drop policy if exists "writer updates projects" on public.projects;
drop policy if exists "owner deletes projects" on public.projects;
create policy "writer inserts projects" on public.projects for insert
  with check (public.can_write(org_id));
create policy "writer updates projects" on public.projects for update
  using (public.can_write(org_id)) with check (public.can_write(org_id));
create policy "owner deletes projects" on public.projects for delete
  using (public.is_owner(org_id));
-- 参照は 006 の "member reads projects"(SELECT=is_member) をそのまま使用。

-- ============================================================ 3. Storage: 行(org)ベースの読取でレガシー可視化
-- 出力物(generations/renders)は storage_path で行に紐づく。行の org のメンバーなら、
-- パスの先頭が旧 <user_id> でも読める。個人orgのファイルは org_id=個人org なので他人には見えない（漏洩なし）。
drop policy if exists "assets read via row" on storage.objects;
create policy "assets read via row" on storage.objects for select
  using (
    bucket_id = 'assets' and (
      exists (select 1 from public.generations g where g.storage_path = name and public.is_member(g.org_id))
      or exists (select 1 from public.renders r where r.storage_path = name and public.is_member(r.org_id))
    )
  );
-- 既存の "assets read own"(<user_id>一致) と "assets read member"(<org_id>パス) も温存（複数ポリシーは OR）。
