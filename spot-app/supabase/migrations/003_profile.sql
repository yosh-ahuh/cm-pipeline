-- 003_profile.sql — 表示名の更新用 RPC
-- profiles はクライアントからの直接 UPDATE を許可していない（credits/plan 保護）ため、
-- 表示名だけを安全に更新する SECURITY DEFINER 関数を用意する。
-- 適用: Supabase Studio → SQL Editor に貼って Run。

create or replace function public.update_display_name(p_name text)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.profiles
     set display_name = nullif(btrim(p_name), '')
   where id = auth.uid();
end;
$$;

grant execute on function public.update_display_name(text) to authenticated;
