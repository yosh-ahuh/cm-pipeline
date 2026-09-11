"""生成物の配置と .done 冪等マーカー.

生成物は generated/<name>.<ext>、隣に <name>.<ext>.done を置く（JSON: model/usd/ts/dry）。
再開時は .done があればスキップし、課金APIの二重実行を防ぐ（architecture.md #1、実証済み）。
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from .project import Project


def artifact(proj: Project, name: str, ext: str) -> Path:
    """generated/ 配下の生成物パス。name は 'cut01.still' のように種別を含めてよい。"""
    return proj.generated / f"{name}.{ext}"


def marker(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".done")


def is_done(path: Path) -> bool:
    return marker(path).is_file()


def mark_done(path: Path, *, model: str, usd: float, dry: bool, provider: dict | None = None,
              **meta) -> None:
    rec = {"model": model, "usd": round(usd, 4), "dry": dry,
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "provider": provider or {}, **meta}
    marker(path).write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")


def read_done(path: Path) -> dict | None:
    m = marker(path)
    if not m.is_file():
        return None
    return json.loads(m.read_text(encoding="utf-8"))


def clear(proj: Project, *, keep_out: bool = True) -> int:
    """全 .done マーカーを削除して再生成可能にする（生成物本体は残す）。件数を返す。"""
    n = 0
    if proj.generated.is_dir():
        for m in proj.generated.rglob("*.done"):
            m.unlink()
            n += 1
    return n
