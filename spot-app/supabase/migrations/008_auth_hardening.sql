-- 008_auth_hardening.sql — 新デバイスOTP（信頼デバイス）＋同時セッション上限の強制。
-- 設計: docs/multi-seat-design.md §4層C・§6。006/007 適用後に。冪等。
--
-- 方針: Edge Function 無しで完結させる。
--   ・新デバイスOTP … Supabase 標準の「メールOTP」(signInWithOtp/verifyOtp) をクライアントで使い、
--       検証済み端末を trusted_devices に記録。判定/記録の RPC をここで用意。
--   ・同時セッション上限 … auth.sessions を SECURITY DEFINER RPC で自分の分だけ最古から間引く。
--
-- 注意: enforce_session_cap は auth.sessions を DELETE する。SQL Editor 実行者(postgres)に
--   auth.sessions への権限が無い環境では作成/実行時に権限エラーになり得る。その場合は
--   docs/auth-hardening.md の「Edge Function 版」に切り替える（手順あり）。

-- ============================================================ 1. 信頼デバイス（新デバイスOTP）
create table if not exists public.trusted_devices (
  user_id    uuid not null references auth.users(id) on delete cascade,
  device_id  text not null,
  trusted_at timestamptz not null default now(),
  primary key (user_id, device_id)
);
alter table public.trusted_devices enable row level security;
drop policy if exists "own trusted devices" on public.trusted_devices;
create policy "own trusted devices" on public.trusted_devices for select using (user_id = auth.uid());

create or replace function public.is_device_trusted(p_device text)
returns boolean language sql security definer stable set search_path = public as $$
  select exists(select 1 from public.trusted_devices where user_id = auth.uid() and device_id = p_device);
$$;
grant execute on function public.is_device_trusted(text) to authenticated;

-- メールOTP検証に成功したクライアントが呼ぶ（＝この端末を信頼登録）。
create or replace function public.trust_device(p_device text)
returns void language plpgsql security definer set search_path = public as $$
begin
  if p_device is null or btrim(p_device) = '' then
    raise exception 'device required' using errcode = '22023';
  end if;
  insert into public.trusted_devices (user_id, device_id) values (auth.uid(), p_device)
  on conflict (user_id, device_id) do update set trusted_at = now();
end; $$;
grant execute on function public.trust_device(text) to authenticated;

-- ============================================================ 2. 同時セッション上限の強制（自分の分のみ）
-- 最新 p_keep 件を残し、それ以前のセッションを失効（refresh token 無効化）。
-- クライアントがログイン直後に呼ぶ。戻り値 = 失効させた件数。
create or replace function public.enforce_session_cap(p_keep int default 2)
returns int language plpgsql security definer set search_path = auth, public as $$
declare n int;
begin
  with keep as (
    select id from auth.sessions
    where user_id = auth.uid()
    order by coalesce(updated_at, created_at) desc
    limit greatest(1, p_keep)
  )
  delete from auth.sessions
  where user_id = auth.uid() and id not in (select id from keep);
  get diagnostics n = row_count;
  return n;
end; $$;
grant execute on function public.enforce_session_cap(int) to authenticated;
