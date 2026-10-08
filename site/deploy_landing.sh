#!/usr/bin/env bash
# spot-landing.html（1 ページ版ランディング）を Vercel プロジェクト `spot-landing` に上げる。
#   使い方: bash site/deploy_landing.sh        → 本番（vercel.app の URL。Deployment Protection はプロジェクト設定に従う）
#   アプリ（spot-app → プロジェクト `spot`）と同じチーム creative-punx。カスタムドメインはまだ付けない（docs/hosting.md §3 は保留中）。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAGE="$(mktemp -d)/spot-landing"      # ディレクトリ名 = 初回に作られるプロジェクト名
mkdir -p "$STAGE"
cp "$ROOT/spot-landing.html" "$STAGE/index.html"
cat > "$STAGE/vercel.json" <<'JSON'
{
  "headers": [
    { "source": "/(.*)", "headers": [
      { "key": "X-Robots-Tag", "value": "noindex, nofollow" },
      { "key": "X-Content-Type-Options", "value": "nosniff" },
      { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
    ] }
  ]
}
JSON
# ※ X-Robots-Tag noindex は vercel.app の仮 URL が検索に載らないため。本番ドメインで公開するときに外す。
cd "$STAGE"
vercel deploy --prod --yes --scope creative-punx
