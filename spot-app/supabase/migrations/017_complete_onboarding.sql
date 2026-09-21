-- 017_complete_onboarding.sql — OAuth（Google 等）サインイン後のプロフィール補完。006〜016 適用後。冪等。
--   OAuth ではサインアップ時に「利用形態（個人/組織）」を取得できず、handle_new_user トリガは
--   既定値（personal）で個人ワークスペースを作ってしまう。ユーザーが補完フローで「組織」を選んだら、
--   その個人ワークスペースを会社ワークスペース（is_personal=false）へ転換し、ブランドを1つ用意する。
--   「個人」を選んだ場合は表示名の更新のみ。RLS で organizations を直接更新させないため SECURITY DEFINER。
--   適用: Supabase Studio → SQL Editor に貼って Run。

create or replace function public.complete_onboarding(p_name text, p_type text, p_company text)
returns void
language plpgsql security definer set search_path = public as $$
declare
  v_uid     uuid := auth.uid();
  v_type    text := lower(coalesce(p_type, 'personal'));
  v_name    text := nullif(btrim(coalesce(p_name, '')), '');
  v_company text := nullif(btrim(coalesce(p_company, '')), '');
  v_org     uuid;
  v_free    numeric;
begin
  if v_uid is null then raise exception 'Not authenticated'; end if;

  -- 表示名（プロフィール）を更新
  if v_name is not null then
    update public.profiles set display_name = v_name where id = v_uid;
  end if;

  -- 「組織」を選んだ場合のみワークスペースを転換/作成
  if v_type = 'org' and v_company is not null then
    -- 既に会社ワークスペース（is_personal=false）を持っていれば何もしない（再実行の安全策）
    if not exists (select 1 from public.organizations
                   where owner_user_id = v_uid and not is_personal) then
      select id into v_org from public.organizations
        where owner_user_id = v_uid and is_personal limit 1;
      if v_org is not null then
        -- 個人ワークスペース → 会社ワークスペースへ転換（所有者・クレジットを引き継ぐ）
        update public.organizations
           set is_personal = false, name = v_company
         where id = v_org;
      else
        -- 個人ワークスペースが無い異常系：会社ワークスペースを新規作成
        select spots_per_month into v_free from public.plans where id = 'free';
        insert into public.organizations (name, plan, credits, credits_reset_at, owner_user_id, is_personal)
        values (v_company, 'free', coalesce(v_free, 1), now(), v_uid, false)
        returning id into v_org;
        insert into public.org_members (org_id, user_id, role)
        values (v_org, v_uid, 'owner') on conflict (org_id, user_id) do nothing;
      end if;
      -- ブランドが無ければ1つ用意（直接の組織サインアップと同じ最終状態に）
      if not exists (select 1 from public.brands where org_id = v_org) then
        insert into public.brands (org_id, name, assets) values (v_org, v_company, '{}'::jsonb);
      end if;
    end if;
  end if;
end; $$;

grant execute on function public.complete_onboarding(text, text, text) to authenticated;
