-- 013_account_type.sql — サインアップの「個人 / 組織」種別に対応。006〜012 適用後。冪等。
--   auth のユーザー metadata（account_type / company_name / display_name）を読み、
--   個人=個人org(is_personal=true)、組織=会社org(is_personal=false)＋brands を1つ作成する。
--   ※ 既存ユーザーには影響なし（新規サインアップ時のトリガ動作のみ変更）。

create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
declare
  v_org uuid; v_name text; v_type text; v_company text; v_free numeric;
begin
  v_name    := coalesce(new.raw_user_meta_data->>'display_name', split_part(new.email, '@', 1));
  v_type    := lower(coalesce(new.raw_user_meta_data->>'account_type', 'personal'));
  v_company := nullif(btrim(coalesce(new.raw_user_meta_data->>'company_name', '')), '');
  select spots_per_month into v_free from public.plans where id = 'free';

  insert into public.profiles (id, display_name, plan, credits)
  values (new.id, v_name, 'free', v_free)
  on conflict (id) do nothing;

  -- 既に何らかの org を持っていれば作らない（再実行・招待経由の安全策）
  if not exists (select 1 from public.organizations where owner_user_id = new.id) then
    if v_type = 'org' and v_company is not null then
      -- 組織アカウント：会社ワークスペース（is_personal=false）＋ブランド
      insert into public.organizations (name, plan, credits, credits_reset_at, owner_user_id, is_personal)
      values (v_company, 'free', v_free, now(), new.id, false)
      returning id into v_org;
      insert into public.brands (org_id, name, assets) values (v_org, v_company, '{}'::jsonb)
      on conflict do nothing;
    else
      -- 個人アカウント：個人ワークスペース（is_personal=true）
      insert into public.organizations (name, plan, credits, credits_reset_at, owner_user_id, is_personal)
      values (v_name, 'free', v_free, now(), new.id, true)
      returning id into v_org;
    end if;
    insert into public.org_members (org_id, user_id, role) values (v_org, new.id, 'owner')
    on conflict (org_id, user_id) do nothing;
  end if;
  return new;
end; $$;
