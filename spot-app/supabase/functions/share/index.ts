// Supabase Edge Function: share
//   共有リンク（share.html?t=<token>）の裏側。トークンを検証し、書き出し済み動画の署名 URL（1 時間）を返す。
//   サインイン不要。トークンは project_shares（025）。失効/取消は空で返す。
//   デプロイ: supabase functions deploy share --no-verify-jwt
//   ※ --no-verify-jwt が必要（共有先はサインインしていない）。認可はトークンそのもので行う。
import { createClient } from "jsr:@supabase/supabase-js@2";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
};

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  const json = (body: unknown, status = 200) =>
    new Response(JSON.stringify(body), { status, headers: { ...cors, "Content-Type": "application/json", "Cache-Control": "no-store" } });
  try {
    const token = new URL(req.url).searchParams.get("t") || "";
    if (!/^[0-9a-f]{64}$/.test(token)) return json({ error: "invalid" }, 400);
    const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);

    const { data: share, error: serr } = await admin
      .from("project_shares").select("project_id, expires_at, revoked_at").eq("token", token).maybeSingle();
    if (serr) throw serr;
    if (!share || share.revoked_at || new Date(share.expires_at).getTime() < Date.now()) return json({ error: "expired" }, 404);

    const { data: project } = await admin.from("projects").select("name, product, status").eq("id", share.project_id).maybeSingle();
    const { data: renders } = await admin
      .from("renders").select("variant, format, storage_path, created_at").eq("project_id", share.project_id).not("storage_path", "is", null)
      .order("created_at", { ascending: true });

    const files = [] as { variant: string; format: string; url: string; download: string }[];
    for (const r of renders || []) {
      if (!r.storage_path || !/\.mp4$/i.test(r.storage_path)) continue;
      const { data: v } = await admin.storage.from("assets").createSignedUrl(r.storage_path, 3600);
      const { data: d } = await admin.storage.from("assets").createSignedUrl(r.storage_path, 3600, { download: true });
      if (v?.signedUrl) files.push({ variant: r.variant, format: r.format, url: v.signedUrl, download: d?.signedUrl || v.signedUrl });
    }
    return json({ name: project?.name || "", product: project?.product || "", expires_at: share.expires_at, files });
  } catch (e) {
    return json({ error: String((e as Error)?.message || e) }, 500);
  }
});
