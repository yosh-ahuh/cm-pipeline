"""スチル生成プロンプトの合成.

documentary.yaml の学び「subject + 語彙群を合成」を実装。
cinematic/golden hour は付けない（AI感の主因）。cut.scene で光・シーン断片を選ぶ。
"""
from __future__ import annotations

from .project import Project


def still_prompt(proj: Project, cut: dict) -> tuple[str, str]:
    """(positive, negative) を返す。"""
    tone = proj.styles.get("tone", {}) or {}
    base = tone.get("base_vocab", {}) or {}
    scene = cut.get("scene")
    still = cut.get("still", {}) or {}

    parts: list[str] = []
    frag = (tone.get("scene_fragments", {}) or {}).get(scene)
    if frag:
        parts.append(frag)
    if still.get("subject"):
        parts.append(still["subject"])
    props = still.get("props") or []
    if props:
        parts.append("props: " + ", ".join(map(str, props)))
    light = (tone.get("light_design", {}) or {}).get("templates", {}).get(scene)
    if light:
        parts.append(light)
    parts += list(base.get("positive", []))
    parts += list(tone.get("japan_check", []))

    positive = ". ".join(p.strip().rstrip(".") for p in parts if p) + "."
    negative = ", ".join(base.get("negative", []))
    # 光の禁則（耳フレア等）を negative に畳み込む。
    forbid = (tone.get("light_design", {}) or {}).get("forbid", [])
    if forbid:
        negative = ", ".join(filter(None, [negative, ", ".join(forbid)]))
    return positive, negative
