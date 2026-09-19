-- 012_billing_prefs.sql — 自動チャージ（オートトップアップ）と低残高メール通知の設定。006〜011 適用後。冪等。
--   org 単位。参照=メンバー、更新=オーナーのみ（課金設定はオーナー限定という既存方針に合わせる）。
--   ※実際の自動課金の「実行」には保存済みのお支払い方法＋Stripe 側の連携が必要（別途）。本テーブルは設定の保持のみ。

create table if not exists public.billing_prefs (
  org_id           uuid primary key references public.organizations(id) on delete cascade,
  topup_enabled    boolean not null default false,   -- 自動チャージ ON/OFF
  topup_threshold  numeric not null default 10,      -- 残高がこの数を下回ったら
  topup_amount     numeric not null default 30,      -- このクレジットを補充
  notify_enabled   boolean not null default false,   -- 低残高メール通知 ON/OFF
  notify_threshold numeric not null default 5,        -- 残高がこの数を下回ったら通知
  updated_at       timestamptz not null default now()
);

alter table public.billing_prefs enable row level security;

drop policy if exists "member reads billing_prefs" on public.billing_prefs;
create policy "member reads billing_prefs" on public.billing_prefs for select
  using (public.is_member(org_id));

drop policy if exists "owner writes billing_prefs" on public.billing_prefs;
create policy "owner writes billing_prefs" on public.billing_prefs for all
  using (public.is_owner(org_id)) with check (public.is_owner(org_id));
