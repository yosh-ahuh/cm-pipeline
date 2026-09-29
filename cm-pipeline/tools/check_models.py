#!/usr/bin/env python3
"""モデル鮮度チェッカー — 常に最新モデルを使うための"都度確認"を自動化する。

fal.ai の公開モデル一覧API（https://fal.ai/api/models?keywords=...）を叩き、
SPOT が現在使っているモデル（styles/model-casting.yaml / cm/adapters/registry.py 由来）に対して
「同じ系統でより新しい版が出ていないか」を照合して表示する。

- FALキー不要・読み取りのみ（課金なし）。
- "新しい版が出ている" と判断したら終了コード 1（cron/CIでアラート可能）。
- 採用は人間が判断する前提（新しい=常に最善ではない。casting.yaml は品質で使い分けている）。

使い方:
  python3 tools/check_models.py           # 表形式で表示
  python3 tools/check_models.py --json     # JSON 出力（通知連携用）
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request

API = "https://fal.ai/api/models?keywords="

# SPOT が現在使っている系統（family）。configured=今の fal ルート、category=fal のカテゴリ。
# 新モデル追加時はここも1行更新すれば追従できる。
TRACKED = [
    {"family": "kling",       "category": "image-to-video", "configured": "fal-ai/kling-video/v3/turbo/pro/image-to-video"},
    {"family": "veo",         "category": "image-to-video", "configured": "fal-ai/veo3.1/image-to-video"},
    {"family": "seedance",    "category": "image-to-video", "configured": "bytedance/seedance-2.5/image-to-video"},
    {"family": "seedream",    "category": "text-to-image",  "configured": "bytedance/seedream/v5/pro/text-to-image"},
    {"family": "nano-banana", "category": "image-to-image", "configured": "fal-ai/nano-banana-pro/edit"},
    {"family": "minimax",     "category": "text-to-speech", "configured": "fal-ai/minimax/speech-2.8-hd"},
    {"family": "lyria",       "category": "text-to-audio",  "configured": "fal-ai/lyria3/pro"},
]

_VER = re.compile(r"(?:v|o)?(\d+(?:\.\d+)?)")


def _fetch(keyword: str) -> list[dict]:
    req = urllib.request.Request(API + urllib.parse.quote(keyword), headers={"accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode()).get("items", [])


def _version_score(model_id: str) -> float:
    """id 内の最大バージョン番号をざっくり数値化（v3 > v2.5、seedream v5 > v4 等）。"""
    nums = [float(m) for m in _VER.findall(model_id.replace("kling-video", "").replace("seedream", ""))]
    return max(nums) if nums else 0.0


import urllib.parse  # noqa: E402  (after helpers for clarity)


def check() -> list[dict]:
    out = []
    for t in TRACKED:
        try:
            items = _fetch(t["family"])
        except Exception as e:  # noqa: BLE001
            out.append({**t, "error": str(e), "candidates": [], "stale": False})
            continue
        # 同カテゴリの候補だけ（image-to-video / text-to-image 等）
        cands = [it["id"] for it in items if it.get("category") == t["category"]]
        conf = t["configured"]
        conf_score = _version_score(conf) if conf else -1.0
        # configured より高いバージョンが出ているか
        newer = sorted({c for c in cands if _version_score(c) > conf_score}, key=_version_score, reverse=True)
        stale = bool(newer)
        out.append({**t, "candidates": cands[:8], "newer": newer[:6], "stale": stale})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    rows = check()
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        any_stale = False
        for r in rows:
            mark = "⚠ 新版あり" if r.get("stale") else ("— 監視のみ" if not r.get("configured") else "✓ 最新")
            print(f"\n[{r['family']}] ({r['category']})  {mark}")
            print(f"  現在: {r.get('configured') or '(未採用)'}")
            if r.get("error"):
                print(f"  取得失敗: {r['error']}")
            if r.get("newer"):
                print("  より新しい候補:")
                for c in r["newer"]:
                    print(f"    - {c}")
            if r.get("stale"):
                any_stale = True
        print("\n" + ("⚠ 新しいモデルが見つかりました。採用可否を検討し、casting.yaml/registry を更新してください（採用前に参照カットで品質確認）。"
                       if any_stale else "✓ すべて最新です。"))
    return 1 if any(r.get("stale") for r in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
