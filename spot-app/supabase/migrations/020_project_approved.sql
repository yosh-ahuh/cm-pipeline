-- 020_project_approved.sql — プロジェクトに「お手本（採用）」フラグを追加。ブランドメモリ／将来の学習の教師信号。
--   ユーザーが「このCMはこのブランドのお手本」と印を付けたものを、ブランドメモリが優先的に学ぶ（Phase1で参照、Phase2/3で学習素材）。
--   更新権限は projects の既存 update ポリシー（can_write＝owner/member）に従う（010）。冪等。適用: SQL Editor（019 の後）。

alter table public.projects add column if not exists approved boolean not null default false;

-- 部分インデックス（org 単位でお手本を素早く引く）
create index if not exists projects_approved_idx
  on public.projects (org_id) where approved;
