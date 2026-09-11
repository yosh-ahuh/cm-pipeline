-- 009_org_content.sql — 共同制作を成立させる仕上げ（A項目）。
--   A1: 生成物/ジョブ/レンダーの org_id を「プロジェクトの org」から継承（個人org誤割当を修正）。
--   A2: Storage をorgメンバーがアクセスできるように（新パス <org_id>/... 用のRLSを追加。旧 <user_id>/... は温存）。
-- 006/007/008 適用後に。冪等。

-- ============================================================ A1. org_id はプロジェクトから継承
-- 子テーブル（project_id を持つ）は project.org_id を継承。無ければ owner の個人org。
create or replace function public.fill_org_id()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if new.org_id is null then
    if tg_table_name in ('generations', 'jobs', 'renders') and new.project_id is not null then
      select org_id into new.org_id from public.projects where id = new.project_id;
    end if;
    if new.org_id is null then
      new.org_id := personal_org(coalesce(new.owner, auth.uid()));
    end if;
  end if;
  return new;
end; $$;
-- トリガ自体は 006 で projects/generations/jobs/renders に付与済み（関数差し替えのみでOK）。

-- ============================================================ A2. Storage: orgメンバー許可
-- 不正uuid（旧 <user_id> パス等）でも例外にしないための安全キャスト。
create or replace function public.safe_uuid(t text)
returns uuid language plpgsql immutable as $$
begin return t::uuid; exception when others then return null; end; $$;

-- 新パス規約: <org_id>/<project_id>/<file>。folder[1]=org_id がメンバー（読取）/can_write（書込）。
drop policy if exists "assets read member"   on storage.objects;
drop policy if exists "assets write member"  on storage.objects;
drop policy if exists "assets update member" on storage.objects;
drop policy if exists "assets delete member" on storage.objects;
create policy "assets read member" on storage.objects for select
  using (bucket_id = 'assets' and public.is_member(public.safe_uuid((storage.foldername(name))[1])));
create policy "assets write member" on storage.objects for insert
  with check (bucket_id = 'assets' and public.can_write(public.safe_uuid((storage.foldername(name))[1])));
create policy "assets update member" on storage.objects for update
  using (bucket_id = 'assets' and public.can_write(public.safe_uuid((storage.foldername(name))[1])));
create policy "assets delete member" on storage.objects for delete
  using (bucket_id = 'assets' and public.can_write(public.safe_uuid((storage.foldername(name))[1])));
-- 旧 "assets *** own"（<user_id> 一致）は 006 以前のファイル用に温存（複数ポリシーは OR）。
