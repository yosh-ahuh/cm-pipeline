-- 031: projects の列単位権限を戻す（028_grant_projects で戻してしまった、正本 028_column_privileges の再適用）
--
-- 経緯: 10/7 の実環境通しで「projects に INSERT できない（42501）」を GRANT 欠落と誤認し、テーブル単位の INSERT/UPDATE/DELETE を
--       authenticated に付与した。実際は 028_column_privileges（別系列、同じ本番 DB に適用済み）が projects を列単位に限定しており、
--       真因はアプリが projects.insert に status 列を送っていたこと。アプリ側は status を送らないよう修正済み（DB 既定 'draft'）。
-- 影響: 案件の作成・更新は列単位の権限で引き続き可能。status / poster_path はサーバ（worker / RPC）のみ。冪等。

revoke insert, update, truncate on public.projects from anon, authenticated;
grant insert (name, product, spec, org_id, brand_id, collection_id)          on public.projects to authenticated;
grant update (name, product, spec, org_id, brand_id, collection_id, approved) on public.projects to authenticated;
revoke delete on public.projects from anon;   -- 削除は RLS "owner deletes projects"（authenticated）のみ

-- 確認
select column_name, string_agg(privilege_type, ',' order by privilege_type) as privs
from information_schema.column_privileges
where grantee = 'authenticated' and table_schema = 'public' and table_name = 'projects'
group by column_name order by column_name;
