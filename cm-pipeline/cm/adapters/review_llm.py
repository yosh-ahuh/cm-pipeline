"""検品アダプタ (Vision LLM)。

quality-rules.md のチェックリストを視覚LLMに注入し、スチルの破綻・AI感を判定する。
NG（手の指・小道具の形状・光のフレア等）は動画化前にスチル段階で潰す。
実装は薄い：フレーム画像＋チェックリスト → 各項目 pass/fail と理由。

実接続: Anthropic SDK（Claude の画像入力・JSON schema 出力）。
  - ANTHROPIC_API_KEY があれば Claude（既定 claude-opus-5-5、SPOT_REVIEW_MODEL で変更）で判定。
  - 無ければ全項目 pass（reason に "skipped" を残す）＝フローを止めない。ドライランも全 pass。
"""
from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Verdict:
    check: str
    ok: bool
    reason: str = ""


SYSTEM = (
    "あなたは日本のテレビCM制作会社の検品担当です。AI生成スチル1枚を、与えられたチェック項目ごとに"
    "合格/不合格で判定します。判定は厳しすぎず、放送に出せるかの実務基準で。"
    "明らかな破綻（指の本数・関節、物体の形状崩れ、化けた文字、不自然な光の塊、分割パネル化）だけを不合格にし、"
    "好みや軽微な違和感は合格にしてください。各項目の reason は日本語で短く（20字程度）。"
)

SCHEMA = {
    "type": "object",
    "properties": {
        "verdicts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "check": {"type": "string"},
                    "ok": {"type": "boolean"},
                    "reason": {"type": "string"},
                },
                "required": ["check", "ok", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["verdicts"],
    "additionalProperties": False,
}


def _image_block(path: str) -> dict:
    raw = Path(path).read_bytes()
    # 拡張子ではなく中身で判定（fal の出力は .png 名でも JPEG のことがある）
    if raw[:3] == b"\xff\xd8\xff":
        media = "image/jpeg"
    elif raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        media = "image/webp"
    elif raw[:6] in (b"GIF87a", b"GIF89a"):
        media = "image/gif"
    else:
        media = "image/png"
    data = base64.standard_b64encode(raw).decode("ascii")
    return {"type": "image", "source": {"type": "base64", "media_type": media, "data": data}}


CLIP_CHECKS = [
    "物の出現・増殖: 元のスチルに無い物が現れる、同じ物が重なる・増える・二重になる",
    "手・指: 本数や関節の破綻、手が溶ける・貫通する",
    "人物の一貫性: 元のスチルと別人・別の服・別の髪型になっていない",
    "構図の一貫性: 場所・家具・小道具の配置が元のスチルから変わっていない",
    "不自然な動作: めくる・貼る・書くなどの手作業が破綻、物が勝手に動く・浮く",
    "文字: 看板・書類・画面の文字が変化する・化ける",
]

CLIP_SYSTEM = (
    "あなたは日本のテレビCM制作会社の検品担当です。1 枚目は元のスチル、2 枚目以降は AI で動画化したクリップの冒頭・中間・末尾のフレームです。"
    "動画化で起きた破綻だけを、与えられたチェック項目ごとに合格/不合格で判定します。放送に出せるかの実務基準で、"
    "明らかな破綻（物が増える・重なる、手指の崩れ、別人化、物が勝手に動く、文字が化ける）だけを不合格にし、軽微なブレや画質は合格にしてください。"
    "各項目の reason は日本語で短く（20字程度）。"
)


class VisionReview:
    model = "vision-review"
    kind = "review"

    def check_clip(self, still_path: str, frame_paths: list[str], *, key: str | None, dry_run: bool,
                   checklist: list[str] | None = None) -> list[Verdict]:
        """動画クリップの検品。元スチルと 3 フレームを並べて、動画化で起きた破綻を判定する。"""
        checklist = checklist or CLIP_CHECKS
        if dry_run or not key:
            return [Verdict(c, True, "dry-run: assumed pass") for c in checklist]
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return [Verdict(c, True, "skipped: ANTHROPIC_API_KEY 未設定（検品なしで通過）") for c in checklist]
        try:
            import anthropic  # noqa: WPS433
        except ImportError:
            return [Verdict(c, True, "skipped: anthropic SDK 未導入（検品なしで通過）") for c in checklist]
        model = os.environ.get("SPOT_REVIEW_MODEL", "claude-opus-5-5")
        self.model = model
        items = "\n".join(f"{i + 1}. {c}" for i, c in enumerate(checklist))
        content: list[dict] = [{"type": "text", "text": "元のスチル:"}, _image_block(still_path)]
        labels = ["クリップ冒頭", "クリップ中間", "クリップ末尾"]
        for i, fp in enumerate(frame_paths[:3]):
            content += [{"type": "text", "text": f"{labels[i] if i < 3 else 'フレーム'}:"}, _image_block(fp)]
        content.append({"type": "text", "text": "次のチェック項目について判定してください。項目名は与えられた文字列をそのまま check に入れ、すべての項目について 1 つずつ返してください。\n\n" + items})
        client = anthropic.Anthropic()
        try:
            res = client.beta.messages.create(
                model=model, max_tokens=2048,
                betas=["server-side-fallback-2026-07-01"], fallbacks="default",
                system=CLIP_SYSTEM, messages=[{"role": "user", "content": content}],
                output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
            )
        except TypeError:
            res = client.messages.create(
                model=model, max_tokens=2048, system=CLIP_SYSTEM,
                messages=[{"role": "user", "content": content}],
                output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
            )
        text = "".join(b.text for b in res.content if getattr(b, "type", "") == "text")
        data = json.loads(text)
        by = {v.get("check"): v for v in data.get("verdicts", []) if isinstance(v, dict)}
        out: list[Verdict] = []
        for c in checklist:
            v = by.get(c) or next((x for k, x in by.items() if k and (k in c or c in k)), None)
            out.append(Verdict(c, True, "判定なし（通過）") if v is None else Verdict(c, bool(v.get("ok", True)), str(v.get("reason", ""))[:80]))
        return out

    def check(self, frame_path: str, checklist: list[str], *, key: str | None,
              dry_run: bool) -> list[Verdict]:
        if dry_run or not key:
            # ドライランでは全項目 pass（原価だけ計上される）。
            return [Verdict(c, True, "dry-run: assumed pass") for c in checklist]
        if not checklist:
            return []
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return [Verdict(c, True, "skipped: ANTHROPIC_API_KEY 未設定（検品なしで通過）") for c in checklist]
        try:
            import anthropic  # noqa: WPS433  遅延 import（キー無し環境で依存を強制しない）
        except ImportError:
            return [Verdict(c, True, "skipped: anthropic SDK 未導入（検品なしで通過）") for c in checklist]

        model = os.environ.get("SPOT_REVIEW_MODEL", "claude-opus-5-5")
        self.model = model
        items = "\n".join(f"{i + 1}. {c}" for i, c in enumerate(checklist))
        prompt = (
            "次のチェック項目について、この画像を判定してください。項目名は与えられた文字列をそのまま check に入れ、"
            "すべての項目について1つずつ返してください。\n\n" + items
        )
        content = [_image_block(frame_path), {"type": "text", "text": prompt}]
        client = anthropic.Anthropic()
        try:
            res = client.beta.messages.create(
                model=model, max_tokens=2048,
                betas=["server-side-fallback-2026-07-01"], fallbacks="default",
                system=SYSTEM,
                messages=[{"role": "user", "content": content}],
                output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
            )
        except TypeError:   # 古い SDK（fallbacks 未対応）
            res = client.messages.create(
                model=model, max_tokens=2048, system=SYSTEM,
                messages=[{"role": "user", "content": content}],
                output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
            )
        text = "".join(b.text for b in res.content if getattr(b, "type", "") == "text")
        data = json.loads(text)
        by = {v.get("check"): v for v in data.get("verdicts", []) if isinstance(v, dict)}
        out: list[Verdict] = []
        for c in checklist:
            v = by.get(c)
            if v is None:   # モデルが項目名を変えた場合は部分一致で救済、無ければ pass 扱い（検品の失敗で止めない）
                v = next((x for k, x in by.items() if k and (k in c or c in k)), None)
            if v is None:
                out.append(Verdict(c, True, "判定なし（通過）"))
            else:
                out.append(Verdict(c, bool(v.get("ok", True)), str(v.get("reason", ""))[:80]))
        return out
