"""ステージ実装 — stills / review / animate / audio / build.

各ステージ = 独立に再開可能なジョブ（.done 冪等・コスト記録・検品ゲート）。
そのまま Phase 1b の Job Worker のロジックに昇格する（architecture.md）。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import ledger, prices, state
from .adapters import GenRequest, get_adapter
from .adapters.review_llm import VisionReview
from .compose import still_prompt
from .project import Project


@dataclass
class Ctx:
    dry_run: bool = True
    force: bool = False
    key: str | None = None
    def log(self, msg: str) -> None:
        print(msg, flush=True)


# ---------------------------------------------------------------- helpers
def _record(proj: Project, ctx: Ctx, stage: str, cut: str, res) -> None:
    ledger.record(proj, stage=stage, cut=cut, model=res.model, usd=res.usd,
                  dry=res.dry, ts=time.strftime("%Y-%m-%dT%H:%M:%S"))


def _skip(path: Path, ctx: Ctx) -> bool:
    return state.is_done(path) and not ctx.force


def _motion_prompt(cut: dict) -> str:
    m = cut.get("motion", {}) or {}
    subject = (cut.get("still", {}) or {}).get("subject", "")
    bits: list[str] = []
    if subject:
        bits.append(subject)
    bits.append("Subtle realistic motion, camera slowly pushes in")
    bits.append("hands stay still; no objects are picked up, moved, pasted, written or turned; nothing new appears; the scene composition stays the same")
    if m.get("gaze") == "downcast":
        bits.append("gaze stays downcast, never toward the camera")
    lw = m.get("living_world")
    if isinstance(lw, list) and lw:
        bits.append("living background: " + ", ".join(map(str, lw)))
    if m.get("exterior") == "static":
        bits.append("everything outside the windows is completely frozen and static")
    if m.get("light") == "even-no-flare":
        bits.append("even soft light, no flare or glow on the face or ears")
    return ". ".join(bits) + "."


# ---------------------------------------------------------------- per-cut ops
# 各 _one は 1カット分の仕事＝Orchestrator の1ジョブに対応する（CLIと共有）。
def still_one(proj: Project, ctx: Ctx, cut: dict) -> dict:
    cid = cut["id"]
    model = cut["still"]["model"]
    adapter = get_adapter(model)
    out = state.artifact(proj, f"{cid}.still", "png")
    if _skip(out, ctx):
        ctx.log(f"  SKIP  {cid} still ({model})")
        return {"status": "skipped", "cut": cid, "model": model, "usd": 0.0}
    pos, neg = still_prompt(proj, cut)
    # 参照は「人物一貫性」用のみ: 明示 consistency.ref、無ければ役者アンカー（最初の実写カットの still）。
    # ※ crop.portrait_native はクロップ用の別アセットで、一貫性 ref には使わない。
    ref = (cut.get("consistency", {}) or {}).get("ref")
    if not ref and prices.normalize(model) == "nano-banana":
        live = proj.live_cuts()
        anchor = live[0]["id"] if live else None
        if anchor and anchor != cid:
            ref = anchor
    ref_paths = []
    if ref:
        cand = state.artifact(proj, f"{ref}.still", "png")
        if cand.is_file():
            ref_paths = [str(cand)]
    # nano-banana は ref 必須。用意できなければ t2i にフォールバック（生成を止めない）。
    if prices.normalize(model) == "nano-banana" and not ref_paths:
        adapter = get_adapter("seedream-v4")
        ctx.log(f"  note  {cid}: ref 未用意のため一貫性editをt2iにフォールバック")
    req = GenRequest(prompt=pos, negative=neg, aspect_ratio="16:9", ref_paths=ref_paths)
    res = adapter.generate(req, str(out), key=ctx.key, dry_run=ctx.dry_run)
    state.mark_done(out, model=res.model, usd=res.usd, dry=res.dry, provider=res.provider)
    _record(proj, ctx, "stills", cid, res)
    ctx.log(f"  {'DRY ' if res.dry else 'GEN '} {cid} still ({model})  ${res.usd:.2f}")
    return {"status": "made", "cut": cid, "model": res.model, "usd": res.usd}


def review_one(proj: Project, ctx: Ctx, cut: dict, *, retake: bool = False) -> dict:
    vr = VisionReview()
    cid = cut["id"]
    still = state.artifact(proj, f"{cid}.still", "png")
    if not state.is_done(still):
        ctx.log(f"  WAIT  {cid}: still 未生成（先に cm stills）")
        return {"status": "wait", "cut": cid}
    verdicts = vr.check(str(still), proj.quality_checklist, key=ctx.key, dry_run=ctx.dry_run)
    ledger.record(proj, stage="review", cut=cid, model=vr.model,
                  usd=prices.usd_for(vr.model), dry=ctx.dry_run,
                  ts=time.strftime("%Y-%m-%dT%H:%M:%S"))
    report = state.artifact(proj, f"{cid}.review", "json")
    report.parent.mkdir(parents=True, exist_ok=True)
    ng = [v for v in verdicts if not v.ok]
    report.write_text(json.dumps(
        {"cut": cid, "pass": not ng, "verdicts": [v.__dict__ for v in verdicts]},
        ensure_ascii=False, indent=2), encoding="utf-8")
    if ng:
        ctx.log(f"  NG    {cid}: " + ", ".join(v.check for v in ng))
        if retake:
            state.marker(still).unlink(missing_ok=True)
        return {"status": "ng", "cut": cid, "ng": [v.check for v in ng], "retaken": retake}
    ctx.log(f"  PASS  {cid}  ({len(verdicts)}項目)")
    return {"status": "pass", "cut": cid}


def _safe_scale(requested: float, w: int, h: int) -> float:
    """Remotion の --scale は出力の幅・高さが偶数の整数でないと H.264 で失敗する（例: 0.6667 → 1280.064px）。
    要求倍率以下で最大の、w*s と h*s がともに偶数整数になる倍率を返す（候補は 1/16 刻み）。"""
    if requested >= 1.0:
        return 1.0
    best = 1.0
    for k in range(16, 0, -1):
        s = k / 16
        if s > requested + 1e-9:
            continue
        ww, hh = w * s, h * s
        if abs(ww - round(ww)) < 1e-9 and abs(hh - round(hh)) < 1e-9 and round(ww) % 2 == 0 and round(hh) % 2 == 0:
            return s
    return best


def _clip_duration(cut: dict, model: str) -> str | None:
    """カットの尺（dur フレーム）に合わせてクリップ長を選ぶ。Veo 3.1 は 4s/6s/8s、Kling は秒数（"5"/"10"）。"""
    dur = cut.get("dur")
    if not dur:
        return None
    secs = float(dur) / 30.0
    if "veo" in (model or ""):
        return "8s" if secs > 6.5 else "6s" if secs > 4.5 else "4s"
    if "kling" in (model or ""):
        return "10" if secs > 7 else "5"
    return None


def animate_one(proj: Project, ctx: Ctx, cut: dict) -> dict:
    cid = cut["id"]
    still = state.artifact(proj, f"{cid}.still", "png")
    if not state.is_done(still):
        ctx.log(f"  WAIT  {cid}: still 未生成"); return {"status": "blocked", "cut": cid, "why": "no-still"}
    if not _still_approved(proj, cid):
        ctx.log(f"  BLOCK {cid}: 検品NG（cm review --retake 後に再生成）")
        return {"status": "blocked", "cut": cid, "why": "review-ng"}
    model = cut["motion"]["model"]
    adapter = get_adapter(model)
    out = state.artifact(proj, cid, "mp4")
    if _skip(out, ctx):
        ctx.log(f"  SKIP  {cid} clip ({model})")
        return {"status": "skipped", "cut": cid, "model": model, "usd": 0.0}
    req = GenRequest(
        prompt=cut.get("motion", {}).get("prompt") or _motion_prompt(cut),
        image_path=str(still),
        resolution=cut.get("motion", {}).get("resolution"),
        duration=cut.get("motion", {}).get("duration") or _clip_duration(cut, model),
    )
    res = adapter.generate(req, str(out), key=ctx.key, dry_run=ctx.dry_run)
    state.mark_done(out, model=res.model, usd=res.usd, dry=res.dry, provider=res.provider)
    _record(proj, ctx, "animate", cid, res)
    ctx.log(f"  {'DRY ' if res.dry else 'GEN '} {cid} clip ({model})  ${res.usd:.2f}")
    return {"status": "made", "cut": cid, "model": res.model, "usd": res.usd}


def _clip_frames(clip: Path, out_dir: Path, cid: str) -> list[Path]:
    """クリップから冒頭・中間・末尾の 3 フレームを抜く（ffmpeg）。"""
    import shutil, subprocess
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        return []
    try:
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(clip)],
                                   capture_output=True, text=True, timeout=20).stdout.strip() or "0")
    except Exception:  # noqa: BLE001
        dur = 0.0
    if dur <= 0:
        return []
    times = [0.2, dur / 2, max(0.3, dur - 0.3)]
    frames = []
    for i, ts in enumerate(times, 1):
        f = out_dir / f"{cid}.clip.f{i}.jpg"
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ts:.2f}", "-i", str(clip), "-frames:v", "1", "-vf", "scale=1280:-2", str(f)],
                           capture_output=True, text=True, timeout=60)
        if r.returncode == 0 and f.is_file():
            frames.append(f)
    return frames


def review_clip_one(proj: Project, ctx: Ctx, cut: dict) -> dict:
    """動画クリップの検品。元スチルと 3 フレームを Claude に見せ、動画化で起きた破綻（物の増殖・手指・別人化・不自然な動作）を判定する。"""
    cid = cut["id"]
    clip = state.artifact(proj, cid, "mp4")
    still = state.artifact(proj, f"{cid}.still", "png")
    if not state.is_done(clip):
        ctx.log(f"  WAIT  {cid}: clip 未生成")
        return {"status": "wait", "cut": cid}
    frames = _clip_frames(clip, proj.generated, cid)
    if not frames:
        ctx.log(f"  SKIP  {cid}: clip 検品（フレーム抽出不可）")
        return {"status": "skipped", "cut": cid}
    vr = VisionReview()
    verdicts = vr.check_clip(str(still), [str(f) for f in frames], key=ctx.key, dry_run=ctx.dry_run)
    ledger.record(proj, stage="review_clip", cut=cid, model=vr.model, usd=prices.usd_for("vision-review-clip"),
                  dry=ctx.dry_run, ts=time.strftime("%Y-%m-%dT%H:%M:%S"))
    report = state.artifact(proj, f"{cid}.clipreview", "json")
    ng = [v for v in verdicts if not v.ok]
    report.write_text(json.dumps({"cut": cid, "pass": not ng, "verdicts": [v.__dict__ for v in verdicts]},
                                 ensure_ascii=False, indent=2), encoding="utf-8")
    if ng:
        ctx.log(f"  NG    {cid} clip: " + ", ".join(v.check.split(":")[0] + "（" + v.reason + "）" for v in ng))
        return {"status": "ng", "cut": cid, "ng": [v.check.split(":")[0] for v in ng], "reasons": [v.reason for v in ng]}
    ctx.log(f"  PASS  {cid} clip ({len(verdicts)}項目)")
    return {"status": "pass", "cut": cid}


def retake_clip(proj: Project, cid: str) -> None:
    """クリップを作り直すために done マーカーと旧ファイルを外す（animate_one が再生成する）。"""
    clip = state.artifact(proj, cid, "mp4")
    state.marker(clip).unlink(missing_ok=True)
    if clip.is_file():
        clip.rename(clip.with_name(f"{cid}.retake.mp4"))


def reject_clip(proj: Project, cid: str) -> None:
    """検品に落ちたクリップを外し、Remotion にスチル（ゆっくり寄る演出）で描かせる。壊れた動画を出すより安全。"""
    clip = state.artifact(proj, cid, "mp4")
    state.marker(clip).unlink(missing_ok=True)
    if clip.is_file():
        clip.rename(clip.with_name(f"{cid}.rejected.mp4"))


# ---------------------------------------------------------------- batch stages
def stills(proj: Project, ctx: Ctx) -> dict:
    made = skipped = 0
    for cut in proj.live_cuts():
        r = still_one(proj, ctx, cut)
        made += r["status"] == "made"; skipped += r["status"] == "skipped"
    return {"made": made, "skipped": skipped}


def _still_approved(proj: Project, cid: str) -> bool:
    report = state.artifact(proj, f"{cid}.review", "json")
    if not report.is_file():
        return True  # 検品未実施なら素通し（review はゲートだが必須ではない）
    return json.loads(report.read_text(encoding="utf-8")).get("pass", True)


def review(proj: Project, ctx: Ctx, *, retake: bool = False) -> dict:
    passed = failed = retaken = 0
    for cut in proj.live_cuts():
        r = review_one(proj, ctx, cut, retake=retake)
        passed += r["status"] == "pass"; failed += r["status"] == "ng"
        retaken += bool(r.get("retaken"))
    return {"passed": passed, "failed": failed, "retaken": retaken}


def animate(proj: Project, ctx: Ctx) -> dict:
    made = skipped = blocked = 0
    for cut in proj.live_cuts():
        r = animate_one(proj, ctx, cut)
        made += r["status"] == "made"; skipped += r["status"] == "skipped"
        blocked += r["status"] == "blocked"
    return {"made": made, "skipped": skipped, "blocked": blocked}


def audio(proj: Project, ctx: Ctx) -> dict:
    made = skipped = 0
    adir = proj.generated / "audio"
    voice = proj.spec.get("script", {}).get("voice", {}) or {}

    # ナレーション（1行1ファイル）
    for nid, text in proj.narration.items():
        adapter = get_adapter(voice.get("model", "minimax-speech-02-hd"))
        out = adir / f"{nid}.mp3"
        if _skip(out, ctx):
            skipped += 1; continue
        req = GenRequest(text=text, voice_id=voice.get("voice_id"), speed=voice.get("speed"),
                         extra={"emotion": voice.get("emotion")})   # 声・トーンは spec.script.voice で選択
        res = adapter.generate(req, str(out), key=ctx.key, dry_run=ctx.dry_run)
        state.mark_done(out, model=res.model, usd=res.usd, dry=res.dry, provider=res.provider)
        _record(proj, ctx, "audio", nid, res); made += 1
        ctx.log(f"  {'DRY ' if res.dry else 'GEN '} na {nid} ({res.model})  ${res.usd:.2f}")

    # BGM（トラック別）
    audio_spec = proj.spec.get("audio", {}) or {}
    for track in audio_spec.get("bgm", []) or []:
        adapter = get_adapter(track.get("model", "lyria2"))
        tid = track.get("id", "bgm")
        out = adir / f"bgm_{tid}.mp3"
        if _skip(out, ctx):
            skipped += 1; continue
        req = GenRequest(prompt=track.get("mood", "corporate"), seconds=track.get("seconds"))
        res = adapter.generate(req, str(out), key=ctx.key, dry_run=ctx.dry_run)
        state.mark_done(out, model=res.model, usd=res.usd, dry=res.dry, provider=res.provider)
        _record(proj, ctx, "audio", f"bgm_{tid}", res); made += 1
        ctx.log(f"  {'DRY ' if res.dry else 'GEN '} bgm {tid} ({res.model})  ${res.usd:.2f}")

    # サウンドロゴ（variant毎）
    sl = audio_spec.get("sound_logo")
    if sl:
        for v in proj.variants or [{"id": "A"}]:
            adapter = get_adapter(sl.get("model", "elevenlabs-sfx-v2"))
            out = adir / f"sound_logo_{v['id']}.mp3"
            if _skip(out, ctx):
                skipped += 1; continue
            req = GenRequest(text=v.get("splash", "brand sound logo"))
            try:   # ElevenLabs は当該アカウントで未提供のことがある → サウンドロゴは非致命でスキップ
                res = adapter.generate(req, str(out), key=ctx.key, dry_run=ctx.dry_run)
            except Exception as e:  # noqa: BLE001
                ctx.log(f"  skip  sound_logo {v['id']}: {repr(e)[:80]}"); skipped += 1; continue
            state.mark_done(out, model=res.model, usd=res.usd, dry=res.dry, provider=res.provider)
            _record(proj, ctx, "audio", f"sound_logo_{v['id']}", res); made += 1
            ctx.log(f"  {'DRY ' if res.dry else 'GEN '} sound_logo {v['id']} ({res.model})  ${res.usd:.2f}")

    return {"made": made, "skipped": skipped}


def build(proj: Project, ctx: Ctx) -> dict:
    """variant × 媒体 を Remotion でレンダし、媒体仕様（delivery）と法務（compliance）を適用して納品する。

    出力: out/<platform>/<name>_<variant>_<platform>.mp4（＋ .c2pa.json サイドカー）、out/delivery.json。
    - composition は Root.tsx の規約 {base}{-B|-C}{-V|-SQ} で形式ごとに切り替える（render.composition_pattern で上書き可）。
    - props に compliance（開示テロップ・セーフゾーン・字幕方針）を渡す。MiraiCM.tsx の `compliance` prop と同形。
    - レンダ後に ffmpeg でラウドネス正規化 / 無音化 / 尺・容量チェック、C2PA マニフェストを付与。
    DRY-RUN では各コマンドを *.plan.txt に書き、delivery.json に計画を残す（課金・レンダなし）。
    """
    from . import delivery, remotion_props

    render = proj.spec.get("render", {}) or {}
    base = render.get("composition", "SpotAd")   # 既定は project.yaml 駆動の汎用コンポジション
    entry = render.get("entry", "src/index.ts")
    prototype = Path(render.get("prototype") or (proj.root.parent.parent.parent / "ad-prototype"))
    comp = delivery.compliance_of(proj)
    plats = delivery.platforms_of(proj)
    raw_dir = proj.out / "_render"
    raw_dir.mkdir(parents=True, exist_ok=True)
    items: list[dict] = []
    planned = 0
    if not plats:
        ctx.log("  WARN  配信先を解決できません（delivery.platforms / output.formats を確認）")
    for pkey, pspec in plats:
        fmt = delivery.format_for(proj, pspec)
        if not fmt:
            ctx.log(f"  WARN  {pkey}: 必要な形式 '{pspec.get('format')}' が output.formats に無い → スキップ")
            continue
        for v in proj.variants or [{"id": "A"}]:
            comp_id = delivery.composition_id(base, v["id"], fmt["id"], render)
            raw = raw_dir / f"{proj.name}_{v['id']}_{pkey}.mp4"
            target = proj.out / pkey / f"{proj.name}_{v['id']}_{pkey}.mp4"
            props = delivery.render_props(proj, v, fmt, pkey, pspec, comp)
            if base in delivery.PROPS_DRIVEN:
                props = {**remotion_props.spot_props(proj, v, prototype), **props}
            cmd = ["npx", "remotion", "render", entry, comp_id, str(raw), f"--props={json.dumps(props, ensure_ascii=False)}"]
            # コンテナ（Railway 等）はメモリが小さく、既定の並列度だと Chrome が OOM で Killed になる。REMOTION_CONCURRENCY で制御（未設定＝1）
            conc = os.environ.get("REMOTION_CONCURRENCY", "1").strip()
            if conc:
                cmd.append(f"--concurrency={conc}")
            # REMOTION_SCALE（未設定＝1.0）: 描画解像度の倍率。0.6667 で 1920×1080 → 1280×720 相当になり Chrome のメモリが大きく下がる。
            scale = os.environ.get("REMOTION_SCALE", "").strip()
            if scale and scale not in ("1", "1.0"):
                s_eff = _safe_scale(float(scale), int(fmt["w"]), int(fmt["h"]))
                if s_eff != float(scale):
                    ctx.log(f"  NOTE  REMOTION_SCALE={scale} → {s_eff}（幅・高さが偶数の整数になる倍率に丸め。H.264 は奇数・小数ピクセル不可）")
                if s_eff < 1.0:
                    cmd.append(f"--scale={s_eff}")
            planned += 1
            if ctx.dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                raw.with_suffix(".mp4.plan.txt").write_text(" ".join(cmd) + f"\n(cwd: {prototype})\n", encoding="utf-8")
                ctx.log(f"  PLAN  {target.relative_to(proj.out)}  ←  {comp_id} {fmt['w']}x{fmt['h']} "
                        f"disclosure={'on' if props['compliance']['disclosure'] else 'off'} "
                        f"safe={props['compliance']['safeZone']}")
            else:
                if not (prototype / "package.json").is_file():
                    ctx.log(f"  WARN  ad-prototype 未検出: {prototype}（レンダ不可）"); continue
                if raw.is_file() and not ctx.force:
                    ctx.log(f"  SKIP  render {raw.name}（既存。--force で再レンダ）")
                else:
                    ctx.log(f"  RENDER {raw.name}  ←  {comp_id}")
                    subprocess.run(cmd, cwd=prototype, check=True)
            rep = delivery.postprocess(raw, target, pkey, pspec, ctx.log, dry=ctx.dry_run)
            rep.update({"variant": v["id"], "format": fmt["id"], "composition": comp_id, "props": props})
            if comp.get("content_credentials", True):
                man = delivery.manifest(proj, target, pkey, props, comp)
                rep["credentials"] = delivery.attach_credentials(target, man, ctx.log)
            items.append(rep)
    report = delivery.write_report(proj, items, comp)
    ctx.log(f"  REPORT {report.relative_to(proj.root)}  ({len(items)} files, "
            f"ai_disclosure={comp.get('ai_disclosure')}, c2pa={comp.get('content_credentials')})")
    return {"planned": planned, "files": len(items), "report": str(report)}
