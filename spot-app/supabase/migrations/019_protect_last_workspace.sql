-- 019_protect_last_workspace.sql — 「最後のワークスペースは削除できない」不変条件を追加。
--   案X（018）で複数ワークスペースの作成/削除が可能になった結果、組織アカウント（is_personal=false）や
--   OAuth補完で組織化したユーザーは“唯一のワークスペース”を削除して、どこにも所属しない状態に陥りうる。
--   delete_organization を拡張し、(1)個人WS基点は従来どおり削除不可、(2)所有WSが1つだけなら削除不可、とする。
--   これで全ユーザーが常に最低1つのワークスペースを保持する。冪等。適用: SQL Editor（018 の後）。

create or replace function public.delete_organization(p_org uuid)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  v_owned int;
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
  -- 最後の1つは削除させない（常に最低1つのワークスペースを残す）
  select count(*) into v_owned from public.organizations where owner_user_id = auth.uid();
  if v_owned <= 1 then
    raise exception 'You must keep at least one workspace';
  end if;
  delete from public.organizations where id = p_org;   -- 関連は FK cascade で連鎖削除
end;
$$;

grant execute on function public.delete_organization(uuid) to authenticated;
