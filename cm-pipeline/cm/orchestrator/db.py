"""状態の永続化（JSON）.

architecture.md「project状態 = DB(JSON)」の Phase 1b 版。ローカルでは
cm-pipeline/.runtime/<project>.json に最新スナップショットを書く。
Phase 2 で実DBのJSON列に載せ替える前提の薄い層。
"""
from __future__ import annotations

import json
from pathlib import Path

from ..project import REPO

RUNTIME = REPO / ".runtime"


def save(name: str, snapshot: dict) -> None:
    RUNTIME.mkdir(exist_ok=True)
    (RUNTIME / f"{name}.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")


def load(name: str) -> dict | None:
    p = RUNTIME / f"{name}.json"
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))
