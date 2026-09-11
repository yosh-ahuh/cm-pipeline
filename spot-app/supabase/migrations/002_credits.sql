-- 002_credits.sql — クレジット消費モデルの確定＋改ざん耐性化
-- 適用: Supabase Studio → SQL Editor に貼って Run（schema.sql 適用済みが前提）。
--
-- 方針:
--   ・クレジット消費は「生成1回につき定額」（呼び出し側が amount を渡す。既定1）。
--   ・実コスト(USD)は credit_ledger.usd に別途記録（credits=0 の行＝残高に影響しない）。
--   ・残高の増減は spend_credits() RPC（SECURITY DEFINER・原子的）に一本化。
--   ・profiles はクライアントから読み取り専用（credits 改ざん防止）。

-- 1) 台帳insertの自動減算トリガを撤去（消費は spend_credits に一本化）
drop trigger if exists on_ledger_insert on public.credit_ledger;
drop function if exists public.apply_credit();

-- 2) profiles をクライアント「本人SELECTのみ」に制限
--    （INSERTは handle_new_user トリガ=definer、増減は spend_credits=definer のみ）
drop policy if exists "own profile" on public.profiles;
create policy "read own profile" on public.profiles
  for select using (id = auth.uid());

-- 3) クレジット消費RPC（原子的・改ざん耐性）
--    残高が足りれば減算して charge を台帳に記録し true、足りなければ false。
create or replace function public.spend_credits(p_project uuid, p_amount numeric)
returns boolean
language plpgsql
security definer
set search_path = public
as $$
declare ok boolean := false;
begin
  update public.profiles
     set credits = credits - p_amount
   where id = auth.uid() and credits >= p_amount
  returning true into ok;

  if ok then
    insert into public.credit_ledger(owner, project_id, stage, model, usd, credits)
    values (auth.uid(), p_project, 'charge', 'credit', 0, p_amount);
    return true;
  end if;
  return false;
end;
$$;

grant execute on function public.spend_credits(uuid, numeric) to authenticated;

-- 4) （任意）テスト中にマイナスへ振れた残高のリセット。開発時のみ実行推奨。
-- update public.profiles set credits = 40 where credits < 0;
