-- 016_delete_org.sql — 組織（ワークスペース）の削除。オーナーのみ。個人ワークスペースは削除不可。冪等。
--   organizations を消すと org_members / brands / projects（→ jobs/renders/generations）/ org_invites が
--   FK on delete cascade で連鎖削除される。credit_ledger は org_id が set null。
--   RLS で organizations の直接 delete は許可していないため、SECURITY DEFINER の RPC 経由で行う。
--   適用: Supabase Studio → SQL Editor に貼って Run（既存 006〜015 適用後）。

create or replace function public.delete_organization(p_org uuid)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  -- オーナー本人以外は不可
  if not exists (select 1 from public.organizations
                 where id = p_org and owner_user_id = auth.uid()) then
    raise exception 'Only the owner can delete this workspace';
  end if;
  -- 個人ワークスペース（アカウントの基点）は削除させない
  if exists (select 1 from public.organizations where id = p_org and is_personal) then
    raise exception 'The personal workspace cannot be deleted';
  end if;
  delete from public.organizations where id = p_org;   -- 関連は FK cascade で連鎖削除
end;
$$;

grant execute on function public.delete_organization(uuid) to authenticated;
