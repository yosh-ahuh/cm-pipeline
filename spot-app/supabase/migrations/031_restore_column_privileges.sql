-- 031: 028_grant_projects / 029_grant_credit_rpcs（モノレポ側・2026-10-07）で戻してしまった正本の権限設計を再適用
--
-- 経緯: 本番で「projects に INSERT できない」「spend_credits が permission denied」を GRANT 欠落と誤認して
--       テーブル単位の INSERT と spend_credits/log_cost の EXECUTE を authenticated に付与した。
--       実際は正本 yosh-ahuh/spot の 026_server_generation（生成開始はサーバ RPC start_generation に一本化）と
--       028_column_privileges（projects は列単位の権限）による意図した制限だった。真因はモノレポ版アプリが
--       projects.insert に status 列を含めていたこと（列権限に status が無い）。
-- 内容: 正本 026/028 の該当行をそのまま再適用（冪等）。モノレポ版アプリの生成開始（クライアント spend_credits）は
--       これで動かなくなるが、正本への移植（docs/port-to-spot-2026-10.md §4）で start_generation に置き換える。

-- projects: テーブル単位の INSERT/UPDATE を剥がし、列単位に戻す（正本 028 と同一）
revoke insert, update, truncate on public.projects from anon, authenticated;
grant insert (name, product, spec, org_id, brand_id, collection_id)          on public.projects to authenticated;
grant update (name, product, spec, org_id, brand_id, collection_id, approved) on public.projects to authenticated;
revoke delete on public.projects from anon;

-- 金額・原価をクライアントが決める RPC は封鎖（正本 026 と同一）
revoke execute on function public.spend_credits(uuid, numeric)           from public, authenticated, anon;
revoke execute on function public.log_cost(uuid, text, text, numeric)    from public, authenticated, anon;

-- 確認: projects の列権限と RPC の実行権限
select table_name, column_name, string_agg(privilege_type, ',' order by privilege_type) as privs
from information_schema.column_privileges
where grantee = 'authenticated' and table_schema = 'public' and table_name = 'projects'
group by table_name, column_name order by column_name;
select p.proname, has_function_privilege('authenticated', p.oid, 'EXECUTE') as authenticated_can_execute
from pg_proc p where p.pronamespace = 'public'::regnamespace and p.proname in ('spend_credits', 'log_cost', 'start_generation');
