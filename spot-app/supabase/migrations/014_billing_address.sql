-- 014_billing_address.sql — 会社プロフィールの請求情報（VAT/税ID・請求先住所）。012 適用後。冪等。
--   org 単位で billing_prefs に列追加（参照=is_member, 更新=is_owner は 012 のポリシーを流用）。
--   請求書・税計算に使う任意情報。個人アカウントでも列は存在するが UI では組織のみ表示。

alter table public.billing_prefs add column if not exists legal_name  text;   -- 会社名義（請求書表記）
alter table public.billing_prefs add column if not exists tax_id      text;   -- VAT / 税ID / 適格請求書番号
alter table public.billing_prefs add column if not exists country     text;   -- 国（ISO or 表示名）
alter table public.billing_prefs add column if not exists postal_code text;   -- 郵便番号
alter table public.billing_prefs add column if not exists address     text;   -- 住所（番地・建物）
alter table public.billing_prefs add column if not exists city        text;   -- 市区町村
alter table public.billing_prefs add column if not exists state       text;   -- 都道府県 / State
