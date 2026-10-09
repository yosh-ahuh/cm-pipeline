#!/usr/bin/env bash
# spot-landing.html（1 ページ版ランディング）を Vercel プロジェクト `spot-landing` に上げる。
#   使い方: bash site/deploy_landing.sh        → 本番（vercel.app の URL。Deployment Protection はプロジェクト設定に従う）
#   アプリ（spot-app → プロジェクト `spot`）と同じチーム creative-punx。カスタムドメインはまだ付けない（docs/hosting.md §3 は保留中）。
#   同梱物: ファビコン・ロゴ（site/static）と OGP 画像（site/build.py が生成する site/dist/og/*.png、英日）。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$ROOT/site/build.py" >/dev/null          # OGP 画像を最新のロゴ・コピーで再生成
STAGE="$(mktemp -d)/spot-landing"      # ディレクトリ名 = 初回に作られるプロジェクト名
mkdir -p "$STAGE/og"
cp "$ROOT/spot-landing.html" "$STAGE/index.html"
for f in favicon-16.png favicon-32.png icon-192.png icon-512.png apple-touch-icon.png spot-mark.png spot-logo.png; do
  cp "$ROOT/site/static/$f" "$STAGE/$f"
done
cp "$ROOT/site/dist/og/"*.png "$STAGE/og/"
cat > "$STAGE/vercel.json" <<'JSON'
{
  "headers": [
    { "source": "/(.*)", "headers": [
      { "key": "X-Robots-Tag", "value": "noindex, nofollow" },
      { "key": "X-Content-Type-Options", "value": "nosniff" },
      { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
    ] },
    { "source": "/(og/.*|.*\\.png)", "headers": [ { "key": "Cache-Control", "value": "public, max-age=604800" } ] }
  ]
}
JSON
# ※ X-Robots-Tag noindex は vercel.app の仮 URL が検索に載らないため。本番ドメインで公開するときに外す。
cd "$STAGE"
vercel deploy --prod --yes --scope creative-punx
