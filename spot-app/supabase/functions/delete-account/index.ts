// Supabase Edge Function: delete-account
//   呼び出したユーザー自身のアカウントを削除する。
//   auth.users を消すと profiles / organizations(owner) / projects / jobs / renders …が
//   FK on delete cascade で連鎖削除される（schema.sql / 006_orgs.sql 参照）。
//   デプロイ: supabase functions deploy delete-account
//   ※ SUPABASE_URL / SUPABASE_ANON_KEY / SUPABASE_SERVICE_ROLE_KEY は Edge Functions の既定環境変数。
import { createClient } from "jsr:@supabase/supabase-js@2";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  const json = (body: unknown, status = 200) =>
    new Response(JSON.stringify(body), { status, headers: { ...cors, "Content-Type": "application/json" } });
  try {
    const url = Deno.env.get("SUPABASE_URL")!;
    const anon = Deno.env.get("SUPABASE_ANON_KEY")!;
    const service = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

    // 呼び出し元の本人確認（JWT）
    const authHeader = req.headers.get("Authorization") || "";
    const userClient = createClient(url, anon, { global: { headers: { Authorization: authHeader } } });
    const { data: { user }, error: uerr } = await userClient.auth.getUser();
    if (uerr || !user) return json({ error: "Unauthorized" }, 401);

    // サービスロールで本人のアカウントを削除（関連データは FK cascade）
    const admin = createClient(url, service);
    const { error: derr } = await admin.auth.admin.deleteUser(user.id);
    if (derr) throw derr;

    return json({ ok: true });
  } catch (e) {
    return json({ error: String((e as Error)?.message || e) }, 500);
  }
});
