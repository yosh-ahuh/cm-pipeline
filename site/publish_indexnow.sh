#!/usr/bin/env bash
# Submit all built URLs to IndexNow (Bing / Copilot / Yandex / Naver share the endpoint).
# Prereq: site/indexnow.key exists and dist/<key>.txt is deployed at the site root.
set -euo pipefail
cd "$(dirname "$0")"
KEY=$(cat indexnow.key)
SITE=$(python3 -c "import sys; sys.path.insert(0,'.'); from content.common import SITE; print(SITE)")
HOST=${SITE#https://}
python3 - "$HOST" "$KEY" "$SITE" <<'EOF'
import json, sys, urllib.request, pathlib
host, key, site = sys.argv[1:4]
urls = [u for u in pathlib.Path('dist/urls.txt').read_text().split() if u]
body = json.dumps({"host": host, "key": key, "keyLocation": f"{site}/{key}.txt", "urlList": urls}).encode()
req = urllib.request.Request("https://api.indexnow.org/IndexNow", data=body, headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req) as r:
    print("IndexNow:", r.status, len(urls), "urls")
EOF
