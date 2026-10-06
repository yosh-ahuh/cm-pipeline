#!/usr/bin/env sh
# SPOT ワーカーのコンテナ起動スクリプト。
#   - WORKER_MODE=live（既定）: 実生成（fal / Claude）。dry にするとドライラン（素材を作らずジョブだけ進める）
#   - STRIPE_WEBHOOK=1（既定）: stripe_webhook.py を同居させる。0 で止める
set -eu
cd /app/spot-app/worker
PY=/app/.venv/bin/python

mode="${WORKER_MODE:-live}"
if [ "$mode" = "live" ]; then
  echo "[entrypoint] worker mode = LIVE (fal 実課金)"
  live="--live"
else
  echo "[entrypoint] worker mode = DRY-RUN"
  live=""
fi

: "${SUPABASE_URL:?SUPABASE_URL が未設定です}"
: "${SUPABASE_SERVICE_ROLE_KEY:?SUPABASE_SERVICE_ROLE_KEY が未設定です}"
if [ "$mode" = "live" ] && [ -z "${FAL_KEY:-}" ]; then
  echo "[entrypoint] WARN: FAL_KEY が未設定。live 生成は失敗します"
fi
[ -n "${ANTHROPIC_API_KEY:-}" ] || echo "[entrypoint] NOTE: ANTHROPIC_API_KEY なし → 台本はテンプレート、検品は通過、ブランド要約はヒューリスティック"

if [ "${STRIPE_WEBHOOK:-1}" = "1" ]; then
  "$PY" stripe_webhook.py &
fi

echo "[entrypoint] starting worker (--watch $live)"
# shellcheck disable=SC2086
exec "$PY" worker.py --watch --interval "${WORKER_INTERVAL:-5}" $live
