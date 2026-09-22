-- 018_create_workspace.sql — ユーザーが新しいワークスペース（＝ブランド／会社／組織：単一概念）を作成できるようにする。
--   これまで所有ワークスペースはサインアップ時の1つのみで、「ワークスペースを追加する」導線は実体が無かった。
--   本RPCで owner として新規ワークスペースを作成し、org_members に owner を張り、付属のブランド資産行(brands)を1つ用意する。
--   ※ workspace=brand の単一概念に整合。brands はワークスペースのロゴ等の“見た目”を保持する1:1の付属テーブルとして残す。
--   ※ 作成数の上限（plans.brands の実効）は課金モデル確定後に別マイグレーションで足す。ここでは上限を設けない。
--   適用: Supabase Studio → SQL Editor（006〜017 適用後）。冪等。

create or replace function public.create_workspace(p_name text)
returns uuid
language plpgsql security definer set search_path = public as $$
declare
  v_uid  uuid := auth.uid();
  v_name text := nullif(btrim(coalesce(p_name, '')), '');
  v_org  uuid;
  v_free numeric;
begin
  if v_uid is null  then raise exception 'Not authenticated'; end if;
  if v_name is null then raise exception 'Workspace name is required'; end if;

  select spots_per_month into v_free from public.plans where id = 'free';
  insert into public.organizations (name, plan, credits, credits_reset_at, owner_user_id, is_personal)
  values (v_name, 'free', coalesce(v_free, 1), now(), v_uid, false)   -- 追加WSは常に is_personal=false（個人WSは基点の1つのみ）
  returning id into v_org;

  insert into public.org_members (org_id, user_id, role)
  values (v_org, v_uid, 'owner') on conflict (org_id, user_id) do nothing;

  insert into public.brands (org_id, name, assets)
  values (v_org, v_name, '{}'::jsonb);

  return v_org;
end; $$;

grant execute on function public.create_workspace(text) to authenticated;
