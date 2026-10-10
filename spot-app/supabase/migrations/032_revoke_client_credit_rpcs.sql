-- 032: spend_credits / log_cost をクライアントから呼べなくする（029_grant_credit_rpcs の取り消し＝026_server_generation の再適用）
--
-- ⚠ 適用条件: アプリの生成開始が start_generation(uuid, boolean) RPC（本番 DB に 026 で存在）に切り替わってから。
--    現行アプリ（index.html の onGenerate）はクライアントから spend_credits → jobs insert で開始するため、先に当てると「つくる」が止まる。
--    切替時は start_generation 側に script ジョブ（stage='script' を先頭、他ジョブの deps に 'script'）を組み込むこと。
-- 冪等。

revoke execute on function public.spend_credits(uuid, numeric)           from public, authenticated, anon;
revoke execute on function public.log_cost(uuid, text, text, numeric)    from public, authenticated, anon;

select p.proname, has_function_privilege('authenticated', p.oid, 'EXECUTE') as authenticated_can_execute
from pg_proc p where p.pronamespace = 'public'::regnamespace and p.proname in ('spend_credits', 'log_cost', 'start_generation');
