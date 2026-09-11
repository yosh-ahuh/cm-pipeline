"""project.yaml → Remotion `SpotAd` の props（ad-prototype/src/SpotAd.tsx と同形）.

案件ごとに TSX を書かずに済ませるための写像層。MiraiCM（1件目の手作り）で確立した
タイムライン（カバー1f → スプラッシュ → 本編 → CTA）を、カット表から機械的に組む。

- 素材は ad-prototype/public/projects/<name>/ に staging（Remotion の staticFile 制約）。
  generated/<cut>.mp4 / <cut>.still.png / audio/*.mp3 / assets/** を対象。
  cut.src 等が public/ 直下の既存パス（例: mirai/cut01_veo.mp4）ならそのまま使う。
- 尺: cut.from/dur があればそれを、無ければ本編を均等割り。narration は cut の頭に置く。
"""
from __future__ import annotations

import shutil
from pathlib import Path

from .project import Project

COVER_FRAMES = 1
SPLASH_FRAMES = 60
DEFAULT_TOTAL = 961


def _stage(proj: Project, prototype: Path, rel: str | None, *, search: list[Path] | None = None) -> str | None:
    """素材を public/projects/<name>/ にコピーして、staticFile 用の相対パスを返す。"""
    if not rel:
        return None
    public = prototype / "public"
    if (public / rel).is_file():           # 既に public 配下にある参照はそのまま
        return rel
    cands = [Path(rel)] + [d / rel for d in (search or [proj.generated, proj.assets, proj.root])]
    src = next((c for c in cands if c.is_file()), None)
    if src is None or _is_dry_placeholder(src):
        return None            # DRY-RUN のプレースホルダは staging しない（実レンダで壊れる）
    dst_dir = public / "projects" / proj.name
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    if not dst.is_file() or dst.stat().st_mtime < src.stat().st_mtime:
        shutil.copy2(src, dst)
    return f"projects/{proj.name}/{src.name}"


def _is_dry_placeholder(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return f.read(24).startswith(b"CM-PIPELINE DRY-RUN")
    except OSError:
        return True


def _brand(proj: Project, prototype: Path) -> dict:
    b = proj.spec.get("brand", {}) or {}
    meta = proj.spec.get("meta", {}) or {}
    colors = b.get("colors", {}) or {}
    wm = b.get("watermark") or {}
    return {
        "name": (wm.get("text") if isinstance(wm, dict) else None) or b.get("name") or meta.get("product") or meta.get("client") or proj.name,
        "primary": colors.get("primary", "#2846D9"),
        "accent": colors.get("accent"),
        "dark": colors.get("dark"),
        "appIcon": _stage(proj, prototype, b.get("app_icon")),
        "logo": _stage(proj, prototype, b.get("logo")),
        "watermark": wm is not False and wm != {"enabled": False},
        "tagline": b.get("tagline"),
    }


def timeline(proj: Project) -> tuple[int, int, list[tuple[dict, int, int]]]:
    """(total_frames, body_start, [(cut, from, dur)])。from/dur 未指定のカットは残りを均等割り。"""
    out = proj.spec.get("output", {}) or {}
    total = int(out.get("duration_frames") or DEFAULT_TOTAL)
    splash = int(out.get("splash_frames") or SPLASH_FRAMES)
    body_start = COVER_FRAMES + splash
    cuts = [c for c in proj.cuts if c.get("type") in ("live-action", "ui", "graphic", "cta")]
    fixed = sum(int(c["dur"]) for c in cuts if c.get("dur"))
    free = [c for c in cuts if not c.get("dur")]
    remain = max(0, total - body_start - fixed)
    per = (remain // len(free)) if free else 0
    rows: list[tuple[dict, int, int]] = []
    cursor = body_start
    for i, c in enumerate(cuts):
        dur = int(c["dur"]) if c.get("dur") else (per + (remain - per * len(free)) if (free and c is free[-1]) else per)
        start = int(c["from"]) + body_start if c.get("from") is not None else cursor
        rows.append((c, start, max(1, dur)))
        cursor = start + max(1, dur)
    return total, body_start, rows


def _cut_props(proj: Project, prototype: Path, cut: dict, start: int, dur: int) -> dict:
    t = cut.get("type")
    base = {"id": cut["id"], "type": t, "from": start, "dur": dur, "telop": cut.get("telop") or []}
    if t == "live-action":
        crop = cut.get("crop", {}) or {}
        cid = cut["id"]
        src = _stage(proj, prototype, cut.get("src") or f"{cid}.mp4")
        srcv = _stage(proj, prototype, cut.get("src_vertical") or (f"{crop['portrait_native']}.mp4" if crop.get("portrait_native") else None))
        still = _stage(proj, prototype, cut.get("still_src") or f"{cid}.still.png")
        base.update({"src": src, "srcVertical": srcv, "still": still,
                     "anchorX": crop.get("anchor_x", 50),
                     "subject": (cut.get("still", {}) or {}).get("subject") or cut.get("role"),
                     "rate": (cut.get("motion", {}) or {}).get("rate", 1)})
    elif t == "ui":
        assets = cut.get("assets") or {}
        vals = list(assets.values()) if isinstance(assets, dict) else list(assets)
        screens = [s for s in (_stage(proj, prototype, _guess_ext(proj, v)) for v in vals) if s]
        base.update({"screens": screens, "caption": cut.get("caption")})
    elif t == "graphic":
        v = cut.get("value", {}) or {}
        base.update({"label": v.get("label") or cut.get("role"), "number": v.get("number"), "unit": v.get("unit"),
                     "note": v.get("note"), "background": _stage(proj, prototype, cut.get("background_src"))})
    elif t == "cta":
        base.update({"badges": cut.get("badges") or [], "button": cut.get("button"),
                     "search": cut.get("search"), "note": cut.get("note")})
    return base


def _guess_ext(proj: Project, name: str) -> str:
    """assets の値が拡張子なし（ui2_camera 等）なら png/jpg を探す。"""
    if "." in Path(name).name:
        return name
    for ext in ("png", "jpg", "jpeg", "webp"):
        for d in (proj.assets, proj.generated, proj.root):
            if (d / f"{name}.{ext}").is_file():
                return f"{name}.{ext}"
    return f"{name}.png"


def _audio(proj: Project, prototype: Path, rows: list[tuple[dict, int, int]], variant: str, total: int) -> dict:
    na = []
    for cut, start, dur in rows:
        ref = cut.get("narration")
        if ref:
            src = _stage(proj, prototype, f"audio/{ref}.mp3") or _stage(proj, prototype, f"{ref}.mp3")
            if src:
                na.append({"src": src, "from": start, "dur": min(dur + 30, total - start)})
    audio_spec = proj.spec.get("audio", {}) or {}
    bgm = []
    for tr in audio_spec.get("bgm", []) or []:
        src = _stage(proj, prototype, f"audio/bgm_{tr.get('id', 'bgm')}.mp3") or _stage(proj, prototype, tr.get("src"))
        if src:
            bgm.append({"src": src, "from": tr.get("from", COVER_FRAMES), "volume": tr.get("volume", 0.35)})
    sl = _stage(proj, prototype, f"audio/sound_logo_{variant}.mp3") or _stage(proj, prototype, (audio_spec.get("sound_logo") or {}).get("src"))
    return {"narration": na, "bgm": bgm, "soundLogo": sl}


def spot_props(proj: Project, variant: dict, prototype: Path) -> dict:
    """SpotAd の props（compliance は delivery.render_props 側で付与）。"""
    total, body_start, rows = timeline(proj)
    out = proj.spec.get("output", {}) or {}
    return {
        "durationInFrames": total,
        "brand": _brand(proj, prototype),
        "splash": {"variant": variant["id"] if variant["id"] in ("A", "B", "C") else "A",
                   "from": COVER_FRAMES, "dur": int(out.get("splash_frames") or SPLASH_FRAMES)},
        "cuts": [_cut_props(proj, prototype, c, s, d) for c, s, d in rows],
        "audio": _audio(proj, prototype, rows, variant["id"], total),
        "grain": "spot/grain.png",
    }
