-- 021_brand_model_foundation.sql — 「アカウント＞ブランド＞コレクション＞動画」モデルの土台（安全な追加のみ）。
--   確定事項（docs/brand-plan-limits-proposal.md）：ブランド＝1製品、org＝アカウント、brands層＝ブランド。
--   本ファイルは【非破壊・追加のみ】：新列と既定値だけ。RLS変更・データ再割当・create_brand・brand_members・
--   collections の org→brand 移行などの“作り替え”は、DB検証ができる段階で別マイグレーションで行う。冪等。
--   ⚠ 適用は Supabase 直アクセス整備後（または SQL Editor）。020 の後。

-- 1) プラン別「コレクション上限」列（0=無制限）。方針：有料は無制限、Freeのみ軽い頭打ち。
alter table public.plans add column if not exists collections int not null default 0;   -- 0 = 無制限
update public.plans set collections = case id
  when 'free' then 12        -- 月3種×約4か月で頭打ち（アップグレードの軽い後押し）
  else 0 end;                -- starter/team/business/enterprise = 無制限

-- 2) ブランドの凍結フラグ（ダウングレード超過時に“読取のみ”へ。凍結対象はユーザーが選択）。
alter table public.brands add column if not exists frozen boolean not null default false;

-- 3) コレクションをブランドに紐付ける列（当面 NULL 可・バックフィルは後日）。
--    現状 collections は org 直下。将来 brand 直下へ寄せるための受け皿だけ用意する。
alter table public.collections add column if not exists brand_id uuid references public.brands(id) on delete cascade;
create index if not exists collections_brand_idx on public.collections(brand_id);

-- （projects.brand_id は 006 で既存。brands テーブルも既存で org あたり複数行を許容＝追加スキーマ不要。）
