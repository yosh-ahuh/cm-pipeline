-- 028: projects テーブルの権限復旧（2026-10-06）
-- 本番で authenticated に projects の INSERT 権限が無く、案件作成が
-- 「permission denied for table projects (42501)」で失敗していた（RLS ではなく GRANT の欠落）。
-- 他テーブル（collections / generations / renders / jobs / brand_sources）は INSERT 可を確認済み。
-- RLS は 024 のポリシー（writer inserts projects 等）がそのまま効く。冪等。

grant select, insert, update, delete on public.projects to authenticated;

-- 念のため: 主要テーブルの権限一覧（SQL Editor で結果を確認。各テーブルに INSERT/SELECT/UPDATE が並べば OK）
select table_name, string_agg(privilege_type, ', ' order by privilege_type) as privs
from information_schema.role_table_grants
where grantee = 'authenticated' and table_schema = 'public'
  and table_name in ('projects','jobs','collections','generations','renders','brands','brand_sources','organizations','memberships')
group by table_name order by table_name;
