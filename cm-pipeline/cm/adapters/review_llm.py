"""検品アダプタ (Vision LLM)。

quality-rules.md のチェックリストを視覚LLMに注入し、スチルの破綻・AI感を判定する。
NG（手の指・小道具の形状・光のフレア等）は動画化前にスチル段階で潰す。
実装は薄い：フレーム画像＋チェックリスト → 各項目 pass/fail と理由。
NOTE: 実キー接続時に vision LLM エンドポイントをここで差し込む。ドライランは全pass。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Verdict:
    check: str
    ok: bool
    reason: str = ""


class VisionReview:
    model = "vision-review"
    kind = "review"

    def check(self, frame_path: str, checklist: list[str], *, key: str | None,
              dry_run: bool) -> list[Verdict]:
        if dry_run or not key:
            # ドライランでは全項目 pass（原価だけ計上される）。
            return [Verdict(c, True, "dry-run: assumed pass") for c in checklist]
        # 実接続時: フレームとチェックリストを vision LLM に渡し、
        # {check, ok, reason}[] を得る。ここに実エンドポイント呼び出しを差し込む。
        raise NotImplementedError(
            "live vision review not wired yet — plug the vision LLM endpoint here"
        )
