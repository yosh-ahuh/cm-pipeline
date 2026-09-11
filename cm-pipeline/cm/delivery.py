"""配信仕様（delivery）と法務（compliance）の適用 — build 段階の出口.

styles/platform-specs.yaml を読み、project.yaml の `delivery` / `compliance` を解決して
  (1) Remotion に渡す props（AI利用開示テロップ・セーフゾーン・字幕方針）
  (2) レンダ後の後処理（ラウドネス正規化・無音化・尺チェック・C2PA マニフェスト）
を担う。競合調査の結論「同じ企画を全媒体の入稿仕様で一括納品」「法務を武器に」の実装。

省略時の compliance は **全て ON**（安全側デフォルト）。spot-app の projects.spec.compliance と同形。
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

import yaml

from . import ledger, state
from .project import Project, STYLES

SPECS_PATH = STYLES / "platform-specs.yaml"

COMPLIANCE_DEFAULTS: dict = {
    "ai_disclosure": True,
    "disclosure_lang": "ja",
    "content_credentials": True,
    "likeness_check": True,
    "real_ui_only": True,
    "claims_evidence": [],
}

# spot-app の媒体名 / 別名 → platform-specs.yaml のキー
MEDIA_ALIASES: dict[str, str] = {
    "youtube": "youtube", "yt": "youtube",
    "reels_shorts": "reels_shorts", "reels": "reels_shorts", "shorts": "reels_shorts",
    "tiktok": "reels_shorts", "リール/ショート": "reels_shorts", "リール": "reels_shorts",
    "timeline": "timeline", "feed": "timeline", "SNSタイムライン": "timeline", "sns": "timeline",
    "signage": "signage", "店頭サイネージ": "signage",
}
# delivery 未指定時: 形式から媒体を推定
FORMAT_DEFAULT_PLATFORM = {"wide": "youtube", "vertical": "reels_shorts", "square": "timeline"}
# 形式 id → Remotion composition のサフィックス（Root.tsx の命名規約）
FORMAT_SUFFIX = {"wide": "", "vertical": "-V", "square": "-SQ"}


# ---------------------------------------------------------------- resolve
def load_specs() -> dict:
    if not SPECS_PATH.is_file():
        return {}
    return yaml.safe_load(SPECS_PATH.read_text(encoding="utf-8")) or {}


def compliance_of(proj: Project) -> dict:
    c = dict(COMPLIANCE_DEFAULTS)
    c.update(proj.spec.get("compliance", {}) or {})
    return c


def platforms_of(proj: Project) -> list[tuple[str, dict]]:
    """(platform_key, spec) のリスト。delivery.platforms → 別名解決。未指定なら形式から推定。"""
    specs = load_specs()
    wanted = (proj.spec.get("delivery", {}) or {}).get("platforms") or []
    keys: list[str] = []
    for w in wanted:
        k = MEDIA_ALIASES.get(str(w), MEDIA_ALIASES.get(str(w).lower(), str(w)))
        if k in specs and k not in keys:
            keys.append(k)
    if not keys:
        for f in proj.formats:
            k = FORMAT_DEFAULT_PLATFORM.get(f.get("id"))
            if k and k in specs and k not in keys:
                keys.append(k)
    return [(k, specs[k]) for k in keys]


def format_for(proj: Project, pspec: dict) -> dict | None:
    fid = pspec.get("format")
    for f in proj.formats:
        if f.get("id") == fid:
            return f
    return None


# variant を props（splash.variant）で受け取る汎用コンポジション（Root.tsx: SpotAd / SpotAd-V / SpotAd-SQ）
PROPS_DRIVEN = {"SpotAd"}


def composition_id(base: str, variant: str, fmt_id: str, render: dict | None = None) -> str:
    """Root.tsx の規約: {base}{-B|-C}{-V|-SQ}（SpotAd は variant サフィックス無し）。render.composition_pattern で上書き可。"""
    default = "{base}{format}" if base in PROPS_DRIVEN else "{base}{variant}{format}"
    pattern = (render or {}).get("composition_pattern") or default
    vs = "" if variant == "A" else f"-{variant}"
    return pattern.format(base=base, variant=vs, format=FORMAT_SUFFIX.get(fmt_id, ""))


def disclosure_text(comp: dict, specs: dict) -> str | None:
    if not comp.get("ai_disclosure", True):
        return None
    d = specs.get("disclosure", {}) or {}
    lang = comp.get("disclosure_lang", "ja")
    if lang == "both":
        return " / ".join(filter(None, [d.get("caption_ja"), d.get("caption_en")]))
    return d.get(f"caption_{lang}") or d.get("caption_ja") or "映像の一部はAIで生成しています"


def render_props(proj: Project, variant: dict, fmt: dict, pkey: str, pspec: dict, comp: dict) -> dict:
    """Remotion `--props` に渡す JSON。MiraiCM の `compliance` prop と同形。"""
    specs = load_specs()
    d = specs.get("disclosure", {}) or {}
    sz = pspec.get("safe_zone", {}) or {}
    text = disclosure_text(comp, specs)
    return {
        "variant": variant["id"], "splashVariant": variant["id"],
        "format": fmt["id"], "width": fmt["w"], "height": fmt["h"], "platform": pkey,
        "compliance": {
            "disclosure": ({"text": text, "seconds": float(d.get("duration_s", 2.0)),
                            "position": d.get("position", "bottom-right"),
                            "minHeightPct": float(d.get("min_height_pct", 3))} if text else None),
            "safeZone": {"topPct": float(sz.get("top_pct", 0)), "bottomPct": float(sz.get("bottom_pct", 0))},
            "captions": pspec.get("captions", "optional"),
        },
    }


# ---------------------------------------------------------------- content credentials
def _models_used(proj: Project) -> list[dict]:
    """generated/**/*.done から使用モデルを集計（C2PA の softwareAgent 相当）。"""
    seen: dict[str, dict] = {}
    if proj.generated.is_dir():
        for m in sorted(proj.generated.rglob("*.done")):
            try:
                rec = json.loads(m.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
            name = rec.get("model") or "unknown"
            s = seen.setdefault(name, {"model": name, "count": 0, "dry": bool(rec.get("dry"))})
            s["count"] += 1
    return list(seen.values())


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest(proj: Project, target: Path, pkey: str, props: dict, comp: dict) -> dict:
    """C2PA 互換のマニフェスト（c2patool が無い環境ではサイドカー JSON として書き出す）。"""
    brand = proj.spec.get("brand", {}) or {}
    meta = proj.spec.get("meta", {}) or {}
    models = _models_used(proj)
    actions = [{"action": "c2pa.created", "digitalSourceType":
                "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia",
                "softwareAgent": m["model"], "count": m["count"]} for m in models]
    actions.append({"action": "c2pa.edited", "softwareAgent": "Remotion (SPOT cm-pipeline build)",
                    "description": "composited real product UI, telop, narration, music"})
    return {
        "claim_generator": "SPOT cm-pipeline/1.0",
        "title": target.name,
        "format": "video/mp4",
        "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "assertions": [
            {"label": "c2pa.actions", "data": {"actions": actions}},
            {"label": "stds.schema-org.CreativeWork", "data": {
                "@context": "https://schema.org", "@type": "VideoObject",
                "name": f"{meta.get('client', '')} {meta.get('product', '')} {props.get('variant')}/{pkey}".strip(),
                "publisher": meta.get("client"), "inLanguage": comp.get("disclosure_lang", "ja")}},
            {"label": "spot.ai_disclosure", "data": {
                "enabled": bool(comp.get("ai_disclosure", True)),
                "caption": (props.get("compliance", {}).get("disclosure") or {}).get("text"),
                "guideline": (load_specs().get("disclosure", {}) or {}).get("guideline")}},
            {"label": "spot.brand_assets", "data": {
                "real_ui_only": bool(comp.get("real_ui_only", True)),
                "likeness_check": bool(comp.get("likeness_check", True)),
                "logo": brand.get("logo") or brand.get("app_icon"),
                "pronunciation": sorted((brand.get("pronunciation") or {}).keys())}},
            {"label": "spot.claims_evidence", "data": {"claims": comp.get("claims_evidence") or []}},
        ],
        "edit_history": ledger.read(proj)[-50:],
        "sha256": _sha256(target),
    }


def c2patool_manifest(man: dict) -> dict:
    """c2patool が受け付ける形（未知フィールド不可）に絞る。署名鍵は環境変数から。

    C2PA_SIGN_CERT / C2PA_PRIVATE_KEY: PEM のパス（未設定なら c2patool 内蔵のテスト証明書＝本番不可）。
    C2PA_ALG: es256 (既定) / es384 / ps256 等。C2PA_TA_URL: タイムスタンプ局。
    """
    import os
    m: dict = {
        "claim_generator_info": [{"name": "SPOT cm-pipeline", "version": "1.0"}],
        "title": man.get("title"),
        "assertions": man.get("assertions", []),
    }
    alg = os.environ.get("C2PA_ALG")
    cert, key = os.environ.get("C2PA_SIGN_CERT"), os.environ.get("C2PA_PRIVATE_KEY")
    if cert and key:
        m.update({"alg": alg or "es256", "sign_cert": cert, "private_key": key})
    if os.environ.get("C2PA_TA_URL"):
        m["ta_url"] = os.environ["C2PA_TA_URL"]
    return m


def attach_credentials(target: Path, man: dict, log) -> dict:
    """c2patool があれば埋め込み（署名）、無ければ <file>.c2pa.json サイドカーのみ。

    サイドカー（完全版: 編集履歴・SHA-256 含む）は常に書く。埋め込みは c2patool 形式の
    マニフェスト <file>.c2pa.manifest.json を別に作って渡す。
    """
    import os
    side = target.with_suffix(target.suffix + ".c2pa.json")
    side.write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
    tool = shutil.which("c2patool")
    if not tool:
        return {"mode": "sidecar", "sidecar": str(side), "note": "c2patool 未検出（brew install c2patool）"}
    if not target.is_file():
        return {"mode": "planned", "sidecar": str(side)}
    mpath = target.with_suffix(target.suffix + ".c2pa.manifest.json")
    mpath.write_text(json.dumps(c2patool_manifest(man), ensure_ascii=False, indent=2), encoding="utf-8")
    signed = target.with_name(target.stem + ".signed" + target.suffix)
    try:
        subprocess.run([tool, str(target), "-m", str(mpath), "-o", str(signed), "-f"],
                       check=True, capture_output=True)
        signed.replace(target)
        prod = bool(os.environ.get("C2PA_SIGN_CERT") and os.environ.get("C2PA_PRIVATE_KEY"))
        log(f"  C2PA  embedded → {target.name}" + ("" if prod else "  (test certificate — set C2PA_SIGN_CERT / C2PA_PRIVATE_KEY for production)"))
        return {"mode": "embedded", "signed_with": "production" if prod else "test-cert", "sidecar": str(side)}
    except subprocess.CalledProcessError as e:  # noqa: PERF203
        log(f"  WARN  c2patool 失敗（サイドカーのみ）: {e.stderr.decode()[:200]}")
        return {"mode": "sidecar", "sidecar": str(side), "error": e.stderr.decode()[:300]}


# ---------------------------------------------------------------- post-process
def _ffprobe_duration(path: Path) -> float | None:
    if not shutil.which("ffprobe") or not path.is_file():
        return None
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "csv=p=0", str(path)], check=True, capture_output=True, text=True).stdout
        return float(out.strip())
    except Exception:  # noqa: BLE001
        return None


def ffmpeg_cmd(src: Path, dst: Path, pspec: dict) -> list[str]:
    codec = pspec.get("codec", {}) or {}
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src)]
    if pspec.get("audio") == "none":
        cmd += ["-an"]
    else:
        lufs = pspec.get("loudness_lufs", -14)
        cmd += ["-af", f"loudnorm=I={lufs}:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
            "-r", str(codec.get("fps", 30)), "-movflags", "+faststart", str(dst)]
    return cmd


def postprocess(src: Path, dst: Path, pkey: str, pspec: dict, log, *, dry: bool) -> dict:
    """レンダ生成物 → 媒体仕様の納品ファイル。ラウドネス・無音化・尺チェック。"""
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = ffmpeg_cmd(src, dst, pspec)
    rep: dict = {"platform": pkey, "src": str(src), "dst": str(dst), "cmd": " ".join(cmd), "warnings": []}
    if dry:
        dst.with_suffix(".mp4.plan.txt").write_text(" ".join(cmd) + "\n", encoding="utf-8")
        return rep
    if not shutil.which("ffmpeg"):
        rep["warnings"].append("ffmpeg 未検出: レンダ生成物をそのままコピー")
        shutil.copy2(src, dst)
    else:
        subprocess.run(cmd, check=True)
    dur = _ffprobe_duration(dst)
    lim = (pspec.get("duration_s", {}) or {})
    mx = lim.get("max") or lim.get("loop")
    if dur is not None and mx and dur > float(mx) + 0.5:
        rep["warnings"].append(f"尺 {dur:.1f}s が {pkey} の上限 {mx}s を超過")
    if dur is not None:
        rep["duration_s"] = round(dur, 2)
    mb = (pspec.get("codec", {}) or {}).get("max_mb")
    if mb and dst.is_file() and dst.stat().st_size > mb * 1024 * 1024:
        rep["warnings"].append(f"ファイルサイズが {pkey} の上限 {mb}MB を超過")
    for w in rep["warnings"]:
        log(f"  WARN  {dst.name}: {w}")
    return rep


def write_report(proj: Project, items: list[dict], comp: dict) -> Path:
    p = proj.out / "delivery.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"project": proj.name, "compliance": comp,
                             "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                             "items": items}, ensure_ascii=False, indent=2), encoding="utf-8")
    return p
