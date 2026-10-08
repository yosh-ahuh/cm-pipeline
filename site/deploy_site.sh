#!/usr/bin/env bash
# 多ページ版サイト（site/dist）をビルドして Vercel プロジェクト `spot-site` に上げる。
#   使い方: bash site/deploy_site.sh            → ビルド → 本番デプロイ（vercel.app の URL、noindex 付き）
#           PUBLIC=1 bash site/deploy_site.sh   → noindex を付けない（本番ドメインで公開するとき）
#   アプリ `spot`・1 ページ LP `spot-landing` と同じチーム creative-punx。Deployment Protection はプロジェクト設定に従う。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$ROOT/site/build.py"
STAGE="$(mktemp -d)/spot-site"         # ディレクトリ名 = 初回に作られるプロジェクト名
mkdir -p "$STAGE"
cp -R "$ROOT/site/dist/." "$STAGE/"
if [ "${PUBLIC:-0}" != "1" ]; then
  # 仮 URL が検索に載らないよう、static/vercel.json のヘッダに X-Robots-Tag: noindex を足す
  python3 - "$STAGE/vercel.json" <<'PY'
import json, sys
p = sys.argv[1]; cfg = json.load(open(p))
cfg["headers"][0]["headers"].insert(0, {"key": "X-Robots-Tag", "value": "noindex, nofollow"})
json.dump(cfg, open(p, "w"), ensure_ascii=False, indent=2)
PY
fi
cd "$STAGE"
vercel deploy --prod --yes --scope creative-punx
