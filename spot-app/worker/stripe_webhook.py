#!/usr/bin/env python3
"""Stripe Webhook ハンドラ — 支払い完了を Supabase に反映する。

Stripe の checkout.session.completed / payment_link を受け、署名を検証してから
service_role RPC を呼ぶ:
  - session.metadata.plan があれば set_plan(org, plan)（プラン変更）
  - session.metadata.extra_spots があれば add_credits(org, N)（追加スポット）
課金は「組織」単位。Payment Link に付与した client_reference_id（＝organizations.id）で特定する。

必要な環境変数:
  STRIPE_WEBHOOK_SECRET        Stripe ダッシュボード → Developers → Webhooks の署名シークレット（whsec_...）
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY    サーバ専用（絶対に公開しない）

Payment Link 側の設定（Stripe ダッシュボード）:
  - 各プランのリンクに metadata: plan = starter|team|business|enterprise
  - 追加スポットのリンクに metadata: extra_spots = 1（買う本数）
  - リンクは client_reference_id を引き継ぐ（アプリが URL に付与する）

使い方:
  export STRIPE_WEBHOOK_SECRET=whsec_... SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=...
  python3 stripe_webhook.py            # 0.0.0.0:8790 で待受
  # Stripe の Webhook エンドポイントを https://<your-host>/stripe/webhook に向ける
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import time
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        sys.exit(f"環境変数 {name} が未設定です。")
    return v


WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
TOLERANCE = 300  # 署名タイムスタンプの許容秒


def verify_signature(payload: bytes, sig_header: str) -> bool:
    """Stripe-Signature ヘッダ（t=...,v1=...）を検証する。"""
    if not WEBHOOK_SECRET or not sig_header:
        return False
    parts = dict(p.split("=", 1) for p in sig_header.split(",") if "=" in p)
    t, v1 = parts.get("t"), parts.get("v1")
    if not t or not v1:
        return False
    if abs(time.time() - int(t)) > TOLERANCE:
        return False
    signed = f"{t}.".encode() + payload
    expected = hmac.new(WEBHOOK_SECRET.encode(), signed, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, v1)


def rpc(fn: str, body: dict) -> None:
    """service_role で PostgREST RPC を呼ぶ。"""
    req = urllib.request.Request(
        SUPABASE_URL.rstrip("/") + f"/rest/v1/rpc/{fn}",
        data=json.dumps(body).encode(),
        headers={"apikey": SERVICE_KEY, "Authorization": f"Bearer {SERVICE_KEY}",
                 "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            r.read()
    except urllib.error.HTTPError as e:
        print("RPC error", fn, e.code, e.read().decode()[:200], flush=True)


def handle_event(event: dict) -> None:
    if event.get("type") != "checkout.session.completed":
        return
    session = event.get("data", {}).get("object", {})
    org = session.get("client_reference_id")   # = organizations.id
    meta = session.get("metadata", {}) or {}
    if not org:
        print("no client_reference_id in session", flush=True)
        return
    if meta.get("plan"):
        print(f"set_plan {org} -> {meta['plan']}", flush=True)
        rpc("set_plan", {"p_org": org, "p_plan": meta["plan"]})
    if meta.get("extra_spots"):
        try:
            n = float(meta["extra_spots"])
        except ValueError:
            n = 0
        if n > 0:
            print(f"add_credits {org} += {n}", flush=True)
            rpc("add_credits", {"p_org": org, "p_amount": n})


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _reply(self, code: int, msg: str = "ok") -> None:
        b = msg.encode()
        self.send_response(code)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):   # コンテナのヘルスチェック用（Railway の healthcheckPath=/healthz）
        if self.path.split("?")[0] in ("/healthz", "/health", "/"):
            return self._reply(200, "ok")
        return self._reply(404, "not found")

    def do_POST(self):
        if self.path.rstrip("/") not in ("/stripe/webhook", "/webhook", ""):
            return self._reply(404, "not found")
        length = int(self.headers.get("Content-Length", 0))
        payload = self.rfile.read(length)
        if not verify_signature(payload, self.headers.get("Stripe-Signature", "")):
            return self._reply(400, "bad signature")
        try:
            handle_event(json.loads(payload))
        except Exception as e:  # noqa: BLE001
            print("handler error:", e, flush=True)
        self._reply(200, "ok")   # 署名OKなら常に200（Stripe の再送を止める）


def main() -> int:
    env("SUPABASE_URL"); env("SUPABASE_SERVICE_ROLE_KEY")
    if not os.environ.get("STRIPE_WEBHOOK_SECRET"):
        print("WARN: STRIPE_WEBHOOK_SECRET 未設定 — 待機はしますが署名検証に失敗するため全イベントを拒否します（Stripe接続後に設定）", flush=True)
    port = int(os.environ.get("PORT", "8790"))
    print(f"stripe webhook listening on 0.0.0.0:{port}  (POST /stripe/webhook)", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
