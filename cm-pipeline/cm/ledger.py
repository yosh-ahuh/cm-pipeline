"""クレジット台帳 — 各生成の実コストを積む (architecture.md #4).

generated/ledger.jsonl に1生成1行で追記。cm cost が集計して USD/JPY/クレジットに換算し、
UI「クレジット残」「生成原価」に対応する数値を出す。
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from . import prices
from .project import Project


def _path(proj: Project) -> Path:
    return proj.generated / "ledger.jsonl"


def record(proj: Project, *, stage: str, cut: str, model: str, usd: float,
           dry: bool, ts: str) -> None:
    proj.generated.mkdir(parents=True, exist_ok=True)
    line = json.dumps({"stage": stage, "cut": cut, "model": model,
                       "usd": round(usd, 4), "dry": dry, "ts": ts}, ensure_ascii=False)
    with _path(proj).open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def read(proj: Project) -> list[dict]:
    p = _path(proj)
    if not p.is_file():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def summary(records: list[dict]) -> dict:
    by_stage: dict[str, float] = defaultdict(float)
    by_model: dict[str, float] = defaultdict(float)
    total = 0.0
    dry_total = 0.0
    for r in records:
        by_stage[r["stage"]] += r["usd"]
        by_model[r["model"]] += r["usd"]
        total += r["usd"]
        if r.get("dry"):
            dry_total += r["usd"]
    return {
        "count": len(records),
        "usd": round(total, 3),
        "jpy": round(prices.to_jpy(total)),
        "credits": round(prices.to_credits(total), 2),
        "dry_usd": round(dry_total, 3),
        "by_stage": {k: round(v, 3) for k, v in sorted(by_stage.items())},
        "by_model": {k: round(v, 3) for k, v in sorted(by_model.items(), key=lambda x: -x[1])},
    }
