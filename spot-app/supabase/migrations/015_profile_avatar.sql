-- 015_profile_avatar.sql — プロフィールアイコン（アバター）。冪等。
--   profiles は直接 UPDATE を保護しているため、表示名(003)と同様に SECURITY DEFINER RPC で更新する。
--   画像は assets バケットの `<uid>/avatar.<ext>` に置き、avatar_url にそのパスを保存する。
--   適用: Supabase Studio → SQL Editor に貼って Run（既存の 006〜014 適用後）。

alter table public.profiles add column if not exists avatar_url text;   -- assets 内のパス or 外部URL

create or replace function public.set_avatar_url(p_url text)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.profiles
     set avatar_url = nullif(btrim(p_url), '')
   where id = auth.uid();
end;
$$;

grant execute on function public.set_avatar_url(text) to authenticated;
