"""project.yaml のロード・検証・スタイル解決.

project.yaml が「単一の真実」(architecture.md #3)。CLI各コマンドはこの Project を読んで動く。
styles/*.yaml と model-casting.yaml をここでマージし、cut に配役表デフォルトを補う。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent          # cm-pipeline/
STYLES = REPO / "styles"
PROJECTS = REPO / "projects"


@dataclass
class Project:
    name: str
    root: Path                 # projects/<name>/
    spec: dict                 # project.yaml の中身
    styles: dict = field(default_factory=dict)   # tone/grade/casting/quality

    # --- paths ---
    @property
    def generated(self) -> Path: return self.root / "generated"
    @property
    def out(self) -> Path: return self.root / "out"
    @property
    def assets(self) -> Path: return self.root / "assets"

    # --- convenience accessors ---
    @property
    def cuts(self) -> list[dict]: return self.spec.get("cuts", [])
    @property
    def formats(self) -> list[dict]: return self.spec.get("output", {}).get("formats", [])
    @property
    def variants(self) -> list[dict]: return self.spec.get("output", {}).get("variants", [])

    @cached_property
    def narration(self) -> dict[str, str]:
        return {n["id"]: n["text"] for n in self.spec.get("script", {}).get("narration", [])}

    @cached_property
    def quality_checklist(self) -> list[str]:
        return self.styles.get("quality", [])

    def live_cuts(self) -> list[dict]:
        return [c for c in self.cuts if c.get("type") == "live-action"]


# ---------------------------------------------------------------- loading
def load(project: str) -> Project:
    """プロジェクト名 or project.yaml パスから Project を構築する。"""
    p = Path(project)
    if p.is_file():
        yaml_path, root = p, p.parent
    else:
        root = p if p.is_dir() else PROJECTS / project
        yaml_path = root / "project.yaml"
    if not yaml_path.is_file():
        raise FileNotFoundError(f"project.yaml が見つかりません: {yaml_path}")

    spec = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    name = spec.get("meta", {}).get("name") or root.name
    proj = Project(name=name, root=root, spec=spec, styles=_load_styles(spec))
    _apply_casting_defaults(proj)
    return proj


def _load_styles(spec: dict) -> dict:
    styles: dict = {}
    tone = spec.get("style", {}).get("tone")
    grade = spec.get("style", {}).get("grade")
    casting = _read_yaml(STYLES / "model-casting.yaml")
    styles["casting"] = casting
    if tone:
        styles["tone"] = _read_yaml(STYLES / f"{tone}.yaml")
    grades = _read_yaml(STYLES / "grades.yaml")
    styles["grade"] = (grades or {}).get(grade, {})
    styles["quality"] = _parse_checklist(STYLES / "quality-rules.md")
    return styles


def _read_yaml(path: Path) -> dict:
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _parse_checklist(path: Path) -> list[str]:
    """quality-rules.md から検品項目を抽出。

    スチル1枚で判定できる項目だけを拾う: A 表（破綻検出 A1〜A6）、C（日本考証）、D3（実在人物との類似）、
    D4（偽UI）。B（後処理で対応）や末尾の「プロセス教訓」の箇条書きは検品項目ではないので含めない。
    形式は「項目: 検出内容」。"""
    if not path.is_file():
        return []
    items: list[str] = []
    strip = lambda t: re.sub(r"`([^`]*)`", r"\1", t.replace("**", "")).strip()   # noqa: E731
    section = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        h = re.match(r"^##\s+([A-Z])\.", line)
        if h:
            section = h.group(1)
            continue
        if section == "C":
            m = re.match(r"^\s*[-*]\s+(.*\S)", line)
            if m:
                items.append("日本考証: " + strip(m.group(1)))
            continue
        row = re.match(r"^\|\s*([AD]\d)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", line)
        if row and (row.group(1).startswith("A") or row.group(1) in ("D3", "D4")):
            items.append(f"{strip(row.group(2))}: {strip(row.group(3))}")
    # フォールバック：ミライ工事で実証した最重要チェック（UI「品質チェック」と対応）。
    return items or [
        "手・指の破綻", "小道具の形状", "光のフレア", "文字化け・偽UI",
        "人物の一貫性", "日本考証", "背景モーション",
    ]


def _apply_casting_defaults(proj: Project) -> None:
    """cut に motion.model / still.model が無ければ配役表のデフォルトを補う。"""
    casting = proj.styles.get("casting", {})
    still_default = (casting.get("still_generation", {}) or {}).get("default", "imagen4")
    anim = casting.get("animation", {}) or {}
    veo_default = (anim.get("veo", {}) or {}).get("model", "veo3.1")
    for cut in proj.cuts:
        if cut.get("type") == "live-action":
            cut.setdefault("still", {}).setdefault("model", still_default)
            cut.setdefault("motion", {}).setdefault("model", veo_default)


# ---------------------------------------------------------------- validation
def validate(proj: Project) -> list[str]:
    """schema 準拠を軽量チェック。問題点の文字列リストを返す（空なら合格）。"""
    issues: list[str] = []
    spec = proj.spec

    for key in ("meta", "output", "cuts"):
        if key not in spec:
            issues.append(f"必須トップレベルキー '{key}' がありません")

    out = spec.get("output", {})
    if not out.get("formats"):
        issues.append("output.formats が空です（少なくとも1形式が必要）")
    for f in out.get("formats", []):
        if not all(k in f for k in ("id", "w", "h")):
            issues.append(f"format に id/w/h が不足: {f}")

    ids = [c.get("id") for c in proj.cuts]
    if len(ids) != len(set(ids)):
        dup = {i for i in ids if ids.count(i) > 1}
        issues.append(f"cut id が重複: {sorted(dup)}")
    for c in proj.cuts:
        if not c.get("id"):
            issues.append(f"id の無い cut があります: {c}")
        if not c.get("type"):
            issues.append(f"cut '{c.get('id')}' に type がありません")

    nar_ids = set(proj.narration)
    for c in proj.cuts:
        ref = c.get("narration")
        if ref and ref not in nar_ids:
            issues.append(f"cut '{c.get('id')}' の narration '{ref}' が script.narration に不在")

    return issues
