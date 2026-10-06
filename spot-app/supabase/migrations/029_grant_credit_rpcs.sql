-- 029: クレジット RPC の実行権限復旧（2026-10-07）
-- 本番で authenticated に spend_credits の EXECUTE 権限が無く、生成開始が
-- 「permission denied for function spend_credits」で止まっていた（028 の projects INSERT と同種＝GRANT の欠落）。
-- 006 で grant 済みのはずだが本番に無い。冪等。

grant execute on function public.spend_credits(uuid, numeric) to authenticated;
grant execute on function public.log_cost(uuid, text, text, numeric) to authenticated;

-- 診断: アプリが呼ぶ RPC のうち authenticated に EXECUTE が無いものを列挙（空なら OK）。
-- ※ get_invite は anon も必要（006）。
with app_rpcs(name) as (values
  ('accept_invite'),('complete_onboarding'),('create_brand'),('create_invite'),('create_share'),('create_workspace'),
  ('delete_brand'),('delete_organization'),('enforce_session_cap'),('get_invite'),('is_device_trusted'),('list_members'),
  ('log_cost'),('login_device_count'),('record_login'),('remove_member'),('revoke_share'),('set_avatar_url'),
  ('set_brand_frozen'),('set_member_brands'),('spend_credits'),('trust_device'),('update_display_name'),('update_notify_prefs'),
  ('is_member'),('member_role'),('can_write'),('is_owner'),('brand_visible'),('project_visible'))
select a.name,
       exists (select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace
               where n.nspname = 'public' and p.proname = a.name) as defined,
       coalesce(bool_or(has_function_privilege('authenticated', p.oid, 'EXECUTE')), false) as authenticated_can_execute
from app_rpcs a
left join pg_proc p on p.proname = a.name and p.pronamespace = 'public'::regnamespace
group by a.name order by authenticated_can_execute, defined, a.name;
