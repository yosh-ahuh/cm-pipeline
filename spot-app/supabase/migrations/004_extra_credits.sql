-- 004_extra_credits.sql — 追加スポット購入でクレジットを加算する RPC（service_role 専用）
-- Stripe Webhook（worker/stripe_webhook.py）から呼ぶ。適用: SQL Editor で Run（APPLY.sql に同梱済み）。

create or replace function public.add_credits(p_user uuid, p_amount numeric)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  if p_amount is null or p_amount <= 0 then
    raise exception 'invalid amount' using errcode = '22023';
  end if;
  perform set_config('spot.internal', '1', true);   -- 保護トリガを通す
  update public.profiles set credits = credits + p_amount where id = p_user;
end;
$$;

revoke execute on function public.add_credits(uuid, numeric) from public, authenticated, anon;
