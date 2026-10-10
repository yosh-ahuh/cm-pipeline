#!/usr/bin/env python3
"""SPOT 生成ワーカー（Supabase jobs 駆動）.

`jobs` テーブルを見て、依存が揃った pending ジョブを実行し status/usd を更新、
credit_ledger を積む。service_role キーで PostgREST を叩く（RLS を貫通）。

Web の DEV ランナー（index.html の __devRunJobs）と同じループのサーバ版。
既定は DRY-RUN（課金なし・原価は概算計上）。--live では projects.spec を cm-pipeline の
project.yaml に写像し（projects/_supabase/<project_id>/）、still/review/animate/audio/build の
各ステージを実行、生成物を Storage(assets) にアップロードして generations / renders に記録する。
build は spec.compliance / spec.delivery を読み、開示テロップ・C2PA・媒体仕様を適用する。

環境変数:
  SUPABASE_URL                 例: https://xxxx.supabase.co
  SUPABASE_SERVICE_ROLE_KEY    service_role キー（サーバ専用・絶対に公開しない）
  FAL_KEY                      （--live）fal.ai キー。未設定なら ../../.fal_key を読む
  ANTHROPIC_API_KEY            （--live・任意）台本ステージ（script）で Claude に台本を書かせる。未設定ならテンプレート台本
  SPOT_SCRIPT_MODEL            （任意）台本生成／ブランド要約モデル。既定 claude-opus-5-5
  ※ ブランド取り込み（brand_sources.status=pending）も同じループで処理する（--brand <uuid> で対象を絞れる）
  CM_PIPELINE_DIR              （任意）cm-pipeline のパス。既定は ../../cm-pipeline
  RESEND_API_KEY               （任意）制作完了メールを送る Resend の API キー。未設定ならメールは送らない
  RESEND_FROM                  （任意）差出人。既定 "Spot <no-reply@creativepunx.com>"
  APP_URL                      （任意）メール内のリンク先（例 https://app.spot.creativepunx.com/ ＝仮ドメイン）。既定は SUPABASE_URL

使い方:
  export SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=...
  python3 worker.py            # 全プロジェクトの pending を処理して終了
  python3 worker.py --watch    # 5秒間隔でポーリング常駐
  python3 worker.py --project <uuid>
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import script_gen  # noqa: E402  台本ステージ（P4）
import brand_ingest  # noqa: E402  ブランド取り込み（P3）
SPOT_ROOT = HERE.parent.parent                                   # SPOT/
CM_DIR = Path(os.environ.get("CM_PIPELINE_DIR") or SPOT_ROOT / "cm-pipeline")

# cm-pipeline の概算原価と揃える（実生成時は実測に置換）。
JOB_USD = {"script": 0.02, "still": 0.05, "review": 0.01, "animate": 3.50, "audio": 0.28, "build": 0.0}
CREDIT_USD = 0.30
SUCCESS = {"done", "skipped"}


def env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        sys.exit(f"環境変数 {name} が未設定です（README 参照）。")
    return v


_ALERTED: set[str] = set()   # 同一プロセス内での重複通知防止


def alert_ops(subject: str, text: str, dedup_key: str = "") -> None:
    """運用アラート。Resend が設定されていればメール送信、無ければログ出力のみ（無害）。
    env: RESEND_API_KEY / SPOT_ALERT_EMAIL(宛先) / SPOT_ALERT_FROM(検証済み差出人)。"""
    if dedup_key:
        if dedup_key in _ALERTED:
            return
        _ALERTED.add(dedup_key)
    print(f"  ALERT  {subject} — {text[:200]}", flush=True)
    key = os.environ.get("RESEND_API_KEY")
    to = os.environ.get("SPOT_ALERT_EMAIL")
    frm = os.environ.get("SPOT_ALERT_FROM")
    if not (key and to and frm):
        return   # 通知先未設定なら print のみ
    try:
        data = json.dumps({"from": frm, "to": [to], "subject": subject, "text": text}).encode()
        req = urllib.request.Request(
            "https://api.resend.com/emails", data=data, method="POST",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                     "User-Agent": "SpotWorker/1.0 (+ops alert)"})
        urllib.request.urlopen(req, timeout=15).read()
    except Exception as e:  # noqa: BLE001
        print(f"  ALERT send failed: {e}", flush=True)


class Supa:
    """PostgREST への薄いクライアント（service_role）。"""
    def __init__(self, url: str, key: str):
        self.base = url.rstrip("/") + "/rest/v1"
        self.h = {"apikey": key, "Authorization": f"Bearer {key}",
                  "Content-Type": "application/json"}

    def _req(self, method: str, path: str, params=None, body=None, prefer=None):
        q = ("?" + urllib.parse.urlencode(params)) if params else ""
        headers = dict(self.h)
        if prefer:
            headers["Prefer"] = prefer
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path + q, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                txt = r.read().decode()
                return json.loads(txt) if txt else None
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"{method} {path} HTTP {e.code}: {e.read().decode()[:300]}") from e

    def select(self, table, **params):
        params.setdefault("select", "*")
        return self._req("GET", f"/{table}", params) or []

    def update(self, table, match: dict, body: dict):
        return self._req("PATCH", f"/{table}", match, body, prefer="return=representation")

    def insert(self, table, body: dict):
        return self._req("POST", f"/{table}", None, body, prefer="return=representation")

    def admin_user(self, user_id: str) -> dict | None:
        """auth.admin: ユーザーのメール・メタデータ（service_role）。"""
        url = self.base.replace("/rest/v1", "/auth/v1") + f"/admin/users/{user_id}"
        req = urllib.request.Request(url, headers={k: v for k, v in self.h.items() if k != "Content-Type"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode() or "null")
        except urllib.error.HTTPError:
            return None

    def download(self, bucket: str, path: str, dest: Path) -> Path:
        """Storage からダウンロード（service_role）。"""
        url = self.base.replace("/rest/v1", "/storage/v1") + f"/object/{bucket}/{path}"
        req = urllib.request.Request(url, headers={k: v for k, v in self.h.items() if k != "Content-Type"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(r.read())
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"download {path} HTTP {e.code}: {e.read().decode()[:300]}") from e
        return dest

    def upload(self, bucket: str, path: str, file: Path) -> str:
        """Storage へアップロード（upsert）。戻り値は bucket 内パス。"""
        url = self.base.replace("/rest/v1", "/storage/v1") + f"/object/{bucket}/{path}"
        ctype = mimetypes.guess_type(str(file))[0] or "application/octet-stream"
        headers = {k: v for k, v in self.h.items() if k != "Content-Type"}
        headers.update({"Content-Type": ctype, "x-upsert": "true"})
        req = urllib.request.Request(url, data=file.read_bytes(), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                r.read()
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"upload {path} HTTP {e.code}: {e.read().decode()[:300]}") from e
        return path


def job_key(j: dict) -> str:
    return f"{j['stage']}:{j['cut']}" if j.get("cut") else j["stage"]


ALLOWED_STAGES: set[str] | None = None   # --stages / WORKER_STAGES で限定（None＝全部）


def ready(j: dict, all_jobs: list[dict]) -> bool:
    if j["status"] != "pending":
        return False
    if ALLOWED_STAGES is not None and j.get("stage") not in ALLOWED_STAGES:
        return False   # このワーカーの担当外（別のワーカーが拾う）
    deps = j.get("deps") or []
    done = {job_key(x) for x in all_jobs if x["status"] in SUCCESS}
    return all(d in done for d in deps)


# ---------------------------------------------------------------- live: cm-pipeline 接続
_CM_LOADED = False


def _load_cm():
    """cm-pipeline を import 可能にする（venv の site-packages も追加）。"""
    global _CM_LOADED
    if _CM_LOADED:
        return
    if not (CM_DIR / "cm").is_dir():
        raise RuntimeError(f"cm-pipeline が見つかりません: {CM_DIR}（CM_PIPELINE_DIR で指定）")
    sys.path.insert(0, str(CM_DIR))
    try:
        import yaml  # noqa: F401
    except ModuleNotFoundError:
        # cm-pipeline/.venv の site-packages を借りる（pyyaml）
        for sp in sorted((CM_DIR / ".venv" / "lib").glob("python*/site-packages")):
            sys.path.append(str(sp))
    _CM_LOADED = True


def _fal_key() -> str | None:
    k = os.environ.get("FAL_KEY")
    if k:
        return k.strip()
    f = SPOT_ROOT / ".fal_key"
    return f.read_text(encoding="utf-8").strip() if f.is_file() else None


# spot-app の spec（ウィザード生成）→ cm-pipeline project.yaml。
# cuts は {id, role, type} なので role を被写体に、業種/トーンを語彙に落とす。
#
# spec はクライアントが自由に書ける（projects の RLS）＝信頼できない入力。
# cm-pipeline は spec の値をファイル名・ローカルパス・レンダ設定としてそのまま使うため、
# ここで「許可したキー・型・形式だけ」を組み立て直す（Allow List）。特に:
#   ・render（prototype/entry/composition）は spec から一切受け取らない（任意コード実行の防止）
#   ・ファイル名になる id は SAFE_ID のみ（パストラバーサル防止）
#   ・素材パスは自組織プレフィックス配下の Storage パスのみ（ローカル読み出し・他テナント参照の防止）
_TONE = {"ドキュメンタリー": "documentary", "documentary": "documentary"}
SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
CUT_TYPES = {"live-action", "ui", "graphic", "cta"}
RENDER = {"composition": "SpotAd", "prototype": str(SPOT_ROOT / "ad-prototype")}
MAX_CUTS, MAX_FORMATS, MAX_VARIANTS, MAX_NARRATION, MAX_BGM, MAX_UI_ASSETS = 24, 3, 3, 24, 2, 8
# 生成モデルは既定（検証済み）のみ。spec 経由の任意モデル指定で原価が跳ねないように。
VOICE_MODELS = {"minimax-speech-02-hd"}
BGM_MODELS = {"lyria2"}
SFX_MODELS = {"elevenlabs-sfx-v2"}


def _id(v) -> str:
    if not isinstance(v, str) or not SAFE_ID.match(v):
        raise ValueError(f"不正な id: {v!r}")
    return v


def _txt(v, n: int = 200) -> str | None:
    return v[:n] if isinstance(v, str) else None


def _num(v, lo: float, hi: float) -> float | None:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return min(max(float(v), lo), hi)


def _txts(v, n: int = 200, k: int = 8) -> list[str]:
    return [x[:n] for x in (v or [])[:k] if isinstance(x, str)] if isinstance(v, list) else []


def _clean(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}


def spec_to_project(project_id: str, spec: dict, product: str | None) -> dict:
    spec = spec if isinstance(spec, dict) else {}
    sel = spec.get("selections") if isinstance(spec.get("selections"), dict) else {}
    meta = spec.get("meta") if isinstance(spec.get("meta"), dict) else {}
    out = spec.get("output") if isinstance(spec.get("output"), dict) else {}

    formats = []
    for f in (out.get("formats") or [])[:MAX_FORMATS]:
        if isinstance(f, dict) and _num(f.get("w"), 16, 3840) and _num(f.get("h"), 16, 3840):
            formats.append({"id": _id(f.get("id")), "w": int(f["w"]), "h": int(f["h"])})
    formats = formats or [{"id": "wide", "w": 1920, "h": 1080}]
    variants = []
    for v in (out.get("variants") or [])[:MAX_VARIANTS]:
        if isinstance(v, dict):
            variants.append(_clean({"id": _id(v.get("id")), "splash": _txt(v.get("splash"), 60)}))
    variants = variants or [{"id": "A"}, {"id": "B"}, {"id": "C"}]

    cuts = []
    narration = []   # P4: 台本ステージが付けたナレーション → script.narration（TTS は読み方適用済みの tts を優先）
    raw_cuts = spec.get("cuts") or []
    if not isinstance(raw_cuts, list) or len(raw_cuts) > MAX_CUTS:
        raise ValueError("cuts が不正です")
    for i, c in enumerate(raw_cuts, 1):
        if isinstance(c, str):
            c = {"id": c, "type": "live-action"}
        if not isinstance(c, dict):
            raise ValueError(f"不正な cut: {c!r}")
        cut = {"id": _id(c.get("id")), "type": c.get("type") or "live-action"}
        if cut["type"] not in CUT_TYPES:
            raise ValueError(f"不正な cut type: {cut['type']!r}")
        role = _txt(c.get("role"), 60) or cut["id"]
        label = script_gen.ROLE.get(role, {}).get("label", role)
        telop = _txts(c.get("telop"), 80) or ([_txt(c.get("caption"), 80)] if _txt(c.get("caption"), 80) else [label])
        nar = _txt(c.get("narration"), 400)
        if nar:
            nid = _id(c.get("narration_id")) if c.get("narration_id") else f"na{i}"
            narration.append({"id": nid, "text": _txt(c.get("narration_tts"), 400) or nar, "display": nar})
            cut["narration"] = nid
        if cut["type"] == "live-action":
            subj = _txt(c.get("subject"), 400) or f"{_txt(sel.get('industry'), 60) or product or 'プロダクト'}の{_txt(sel.get('target'), 60) or '利用者'}。{label}"
            cut["still"] = {"subject": subj}
            cut["motion"] = {"resolution": "1080p"}
            motion_en = _txt(c.get("motion_en"), 300)
            if motion_en:   # 台本ステージが書いた最小限の動き（英語）。手作業・ページめくり等は台本側で禁止済み
                cut["motion"]["prompt"] = f"{subj}. {motion_en}. Camera slowly pushes in. Hands stay still; no objects are picked up, moved, pasted, written or turned; nothing new appears."
            cut["telop"] = telop
        elif cut["type"] == "cta":
            # ボタン文言は台本の字幕（例「お問い合わせはこちら」）を優先。検索語は CM 名ではなくブランド名
            brand_name = _txt((spec.get("brand") or {}).get("name") if isinstance(spec.get("brand"), dict) else None, 60)
            cut.update({"button": _txt(c.get("button"), 60) or _txt(c.get("caption"), 60) or "今すぐ 無料ではじめる",
                        "badges": _txts(c.get("badges"), 40),
                        "search": _txt(c.get("search"), 60) or brand_name or product, "note": _txt(c.get("note"), 120), "telop": telop})
        elif cut["type"] == "graphic":
            v = c.get("value") if isinstance(c.get("value"), dict) else {}
            num = v.get("number")
            cut["value"] = _clean({"label": _txt(v.get("label"), 60) or _txt(c.get("caption"), 60) or label,
                                   "unit": _txt(v.get("unit"), 20), "note": _txt(v.get("note"), 120),
                                   "number": num if isinstance(num, (int, float, str)) and not isinstance(num, bool) else None})
        else:  # ui
            # assets: アプリが Storage に上げたスクショのパス配列（localize_assets が検証して assets/ にダウンロード）
            # UI カットは caption を画面下に描くので、同文の telop は重ねない（明示 telop がある場合のみ）
            cut.update({"assets": _txts(c.get("assets"), 512, MAX_UI_ASSETS),
                        "caption": _txt(c.get("caption"), 120) or label, "telop": _txts(c.get("telop"), 80)})
        secs = _num(c.get("secs"), 0.5, 60)
        if secs:
            cut["dur"] = int(round(secs * 30))
        cuts.append(cut)
    # 尺を媒体上限（既定30s）に収める。台本は cuts.secs を上限ちょうどに作りがちで、そこへ
    # cover(1F)+splash(60F) が上乗せされると超過する（例: 30s + 2s = 961F = 32.1s）。
    # cover+splash+Σ(cut.dur) が上限を超えたら、各カット尺を比例縮小して収める。
    # ナレーションは各カット尺より十分短いため、数%の縮小で音声が切れることはない。
    _FPS = 30
    _COVER_SPLASH = 1 + int(_num(out.get("splash_frames"), 0, 300) or 60)   # remotion_props: COVER_FRAMES=1, SPLASH_FRAMES=60
    _cap_f = int(round((_num(out.get("max_seconds"), 5, 600) or 30) * _FPS))
    _timed = [c for c in cuts if c.get("dur")]
    _content = sum(c["dur"] for c in _timed)
    _budget = _cap_f - _COVER_SPLASH
    if _content > _budget > 0 and _timed:
        _scale = _budget / _content
        for c in _timed:
            c["dur"] = max(1, int(c["dur"] * _scale))
        _content = sum(c["dur"] for c in _timed)
    _duration_frames = int(_num(out.get("duration_frames"), 150, 1800) or (_COVER_SPLASH + _content))

    b = spec.get("brand") if isinstance(spec.get("brand"), dict) else {}
    colors = b.get("colors") if isinstance(b.get("colors"), dict) else {}
    wm = b.get("watermark")
    brand = _clean({
        "name": _txt(b.get("name"), 60), "tagline": _txt(b.get("tagline"), 120),
        "colors": _clean({k: _txt(colors.get(k), 32) for k in ("primary", "accent", "dark")}) or None,
        "watermark": wm if isinstance(wm, bool) else (_clean({"text": _txt(wm.get("text"), 60), "enabled": wm.get("enabled") if isinstance(wm.get("enabled"), bool) else None}) if isinstance(wm, dict) else None),
        "app_icon": _txt(b.get("app_icon"), 512), "logo": _txt(b.get("logo"), 512),   # localize_assets で検証
        "references": _txts(b.get("references"), 512, 3) or None,                      # reference_stills が入れるお手本スチル
        "imagery": _txt(b.get("imagery"), 400), "register": _txt(b.get("register"), 400),   # ブランドの画作り・言葉遣いヒント
        "pronunciation": {k[:40]: v[:80] for k, v in list(b["pronunciation"].items())[:20]
                          if isinstance(k, str) and isinstance(v, str)} if isinstance(b.get("pronunciation"), dict) else None,
    })

    sc = spec.get("script") if isinstance(spec.get("script"), dict) else {}
    voice = sc.get("voice") if isinstance(sc.get("voice"), dict) else {}
    script = _clean({
        "source": _txt(sc.get("source"), 20),
        "voice": _clean({"model": voice.get("model") if voice.get("model") in VOICE_MODELS else None,
                         "voice_id": _txt(voice.get("voice_id"), 64), "speed": _num(voice.get("speed"), 0.5, 2.0),
                         "emotion": _txt(voice.get("emotion"), 32)}) or None,
        "narration": narration or None,
    })

    au = spec.get("audio") if isinstance(spec.get("audio"), dict) else {}
    bgm = [_clean({"id": _id(t.get("id") or "bgm"), "model": t.get("model") if t.get("model") in BGM_MODELS else None,
                   "mood": _txt(t.get("mood"), 100), "seconds": _num(t.get("seconds"), 5, 60),
                   "from": _num(t.get("from"), 0, 1800), "volume": _num(t.get("volume"), 0, 1)})
           for t in (au.get("bgm") or [])[:MAX_BGM] if isinstance(t, dict)]
    audio = {"bgm": bgm or [{"id": "main", "model": "lyria2", "mood": "uplifting-corporate"}]}
    sl = au.get("sound_logo")
    if isinstance(sl, dict):
        audio["sound_logo"] = _clean({"model": sl.get("model") if sl.get("model") in SFX_MODELS else None})

    comp = spec.get("compliance") if isinstance(spec.get("compliance"), dict) else {}
    compliance = {k: comp[k] for k in ("ai_disclosure", "content_credentials", "likeness_check", "real_ui_only")
                  if isinstance(comp.get(k), bool)}
    if comp.get("disclosure_lang") in ("ja", "en", "both"):
        compliance["disclosure_lang"] = comp["disclosure_lang"]
    if isinstance(comp.get("claims_evidence"), list):
        compliance["claims_evidence"] = _txts(comp["claims_evidence"], 300, 20)
    dl = spec.get("delivery") if isinstance(spec.get("delivery"), dict) else {}

    return {
        "meta": {"name": project_id, "client": _txt(meta.get("client"), 80), "product": product or _txt(meta.get("name"), 80),
                 "goal": _txt(meta.get("goal"), 200) or _txt(sel.get("angle"), 60), "source": "spot-app"},
        "output": {"fps": 30, "duration_frames": _duration_frames, "formats": formats, "variants": variants},
        "brand": brand,
        "style": {"tone": _TONE.get(sel.get("tone"), "documentary"), "grade": "broadcast-cool"},
        "script": script,
        "cuts": cuts,
        "audio": audio,
        "compliance": compliance,
        "delivery": {"platforms": _txts(dl.get("platforms"), 32)},   # 既知の媒体キー以外は cm 側で無視される
        # レンダ設定は固定（spec からは受け取らない）。project.yaml 駆動の汎用コンポジション SpotAd。
        "render": dict(RENDER),
    }


def storage_path_ok(p, prefixes: list[str]) -> bool:
    """自組織（または旧 owner）プレフィックス配下の正規化済み Storage パスか。
    絶対パス・..・バックスラッシュ・NUL・他テナント参照を弾く（ローカル読み出し/越境防止）。"""
    if not isinstance(p, str) or len(p) > 512 or "\\" in p or "\x00" in p:
        return False
    segs = p.split("/")
    if len(segs) < 2 or segs[0] not in [x for x in prefixes if x]:
        return False
    return all(s and s not in (".", "..") for s in segs)


def localize_assets(sb: Supa, root: Path, d: dict, prefixes: list[str]) -> int:
    """project.yaml 内の Storage パス（<org_id>/... または旧 <owner>/...）を root/assets/ にダウンロードして相対パスに置換。
    許可外のパス（絶対パス・..・他組織・ローカル参照）は捨てる。"""
    n = 0

    def fetch(p):
        nonlocal n
        if not storage_path_ok(p, prefixes):
            if p:
                print(f"  assets: rejected path {str(p)[:120]!r}", flush=True)
            return None
        dest = root / "assets" / Path(p).name
        if not dest.is_file():
            sb.download("assets", p, dest)
            n += 1
        return f"assets/{dest.name}"

    brand = d.get("brand") or {}
    for k in ("app_icon", "logo"):
        if brand.get(k):
            v = fetch(brand[k])
            if v:
                brand[k] = v
            else:
                del brand[k]
    if isinstance(brand.get("references"), list):
        brand["references"] = [v for v in (fetch(x) for x in brand["references"]) if v]
    for cut in d.get("cuts") or []:
        a = cut.get("assets")
        if isinstance(a, list):
            cut["assets"] = [v for v in (fetch(x) for x in a) if v]
        elif isinstance(a, dict):
            cut["assets"] = {k: v for k, v in ((k, fetch(x)) for k, x in a.items()) if v}
    return n


# ---------------------------------------------------------------- P5: ブランドの見た目・言葉を生成へ（ブランドメモリ Phase 2）
def merge_brand(sb: Supa, spec: dict, brand_id: str | None) -> dict:
    """spec.brand（アプリのスナップショット）を、最新の brands.assets / profile で補完する。既にある値は保たれる。"""
    b = dict(spec.get("brand") or {})
    if not brand_id:
        return b
    rows = sb.select("brands", id=f"eq.{brand_id}", select="name,assets,profile")
    if not rows:
        return b
    a = rows[0].get("assets") or {}; pf = rows[0].get("profile") or {}
    vi, vo, sm = pf.get("visual") or {}, pf.get("voice") or {}, pf.get("summary") or {}
    b.setdefault("name", rows[0].get("name") or "")
    if not b.get("logo") and (a.get("logo") or vi.get("logo")):
        b["logo"] = a.get("logo") or vi.get("logo")
    if not b.get("app_icon") and a.get("app_icon"):
        b["app_icon"] = a["app_icon"]
    palette = ((a.get("colors") or {}).get("palette")) or vi.get("colors") or []
    colors = dict(b.get("colors") or {})
    if not colors.get("primary") and (((a.get("colors") or {}).get("primary")) or palette):
        colors["primary"] = (a.get("colors") or {}).get("primary") or palette[0]
    if not colors.get("accent") and len(palette) > 1:
        colors["accent"] = palette[1]
    if not colors.get("dark") and len(palette) > 2:
        colors["dark"] = palette[2]
    if colors:
        b["colors"] = colors
    if not b.get("tagline") and sm.get("one_liner"):
        b["tagline"] = sm["one_liner"]
    pron = dict(b.get("pronunciation") or {})
    for t in vo.get("terms") or []:
        if t.get("text") and t.get("reading"):
            pron.setdefault(t["text"], t["reading"])
    if pron:
        b["pronunciation"] = pron
    for k, v in (("imagery", vi.get("imagery")), ("register", vo.get("register"))):
        if v and not b.get(k):
            b[k] = v
    return b


def reference_stills(sb: Supa, brand_id: str | None, exclude_project: str, limit: int = 3) -> list[str]:
    """同じブランドで「お手本」（projects.approved）にした案件の生成スチルを参照画像として集める（Storage パス）。"""
    if not brand_id:
        return []
    try:
        projs = sb.select("projects", brand_id=f"eq.{brand_id}", approved="eq.true", select="id", order="updated_at.desc", limit="5")
        ids = [p["id"] for p in projs if p["id"] != exclude_project]
        if not ids:
            return []
        gens = sb.select("generations", project_id=f"in.({','.join(ids)})", kind="eq.still", status="eq.done",
                         select="storage_path,created_at", order="created_at.desc", limit=str(limit))
        return [g["storage_path"] for g in gens if g.get("storage_path")]
    except Exception as e:  # noqa: BLE001
        print(f"  WARN  reference stills: {e}", flush=True)
        return []


def restore_generations(sb: Supa, proj, project_id: str) -> int:
    """generations（kind=still/clip/audio, status=done）を Storage から generated/ に戻し、done マーカーを付ける。
    ローカルに無いものだけ取得。失敗しても生成は続く（その場合は再生成される）。"""
    try:
        from cm import state
        rows = sb.select("generations", project_id=f"eq.{project_id}", status="eq.done",
                         select="kind,cut,model,usd,storage_path,created_at", order="created_at.asc")
    except Exception as e:  # noqa: BLE001
        print(f"  WARN  restore: generations を読めません: {e}", flush=True)
        return 0
    seen: dict[str, dict] = {}
    for r in rows or []:
        if r.get("kind") in ("still", "clip", "audio") and r.get("storage_path"):
            seen[r["storage_path"]] = r          # 同じパスは最新行で上書き（作り直しスチル等）
    n = 0
    for path, r in seen.items():
        name = Path(path).name
        dest = proj.generated / ("audio" if r["kind"] == "audio" else "") / name if r["kind"] == "audio" else proj.generated / name
        if dest.is_file() and state.is_done(dest):
            continue
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            sb.download("assets", path, dest)
            state.mark_done(dest, model=r.get("model") or "restored", usd=float(r.get("usd") or 0.0), dry=False,
                            provider={"restored_from": path})
            n += 1
        except Exception as e:  # noqa: BLE001
            print(f"  WARN  restore {name}: {e}", flush=True)
    return n


class LiveRunner:
    """1プロジェクト分の cm-pipeline 実行コンテキスト（spec → project.yaml → ステージ）。"""

    def __init__(self, sb: Supa, project_id: str, owner: str, spec: dict, product: str | None, org: str | None = None,
                 brand_id: str | None = None):
        _load_cm()
        import yaml
        from cm import ledger, pipeline, project as project_mod
        self.sb, self.project_id, self.owner, self.org = sb, project_id, owner, org
        self.pipeline, self.ledger = pipeline, ledger
        root = CM_DIR / "projects" / "_supabase" / project_id
        root.mkdir(parents=True, exist_ok=True)
        spec = dict(spec)
        spec["brand"] = merge_brand(sb, spec, brand_id)                  # P5: 最新のブランドで色・ロゴ・読み方を補完
        refs = reference_stills(sb, brand_id, project_id)
        if refs:
            spec["brand"]["references"] = refs                           # お手本案件のスチル（人物一貫性・スタイル参照用）
        d = spec_to_project(project_id, spec, product)
        got = localize_assets(sb, root, d, [org, owner])   # 新 <org_id>/… と旧 <owner>/… の両対応
        if got:
            print(f"  assets: {got} file(s) downloaded", flush=True)
        (root / "project.yaml").write_text(
            yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
        self.proj = project_mod.load(str(root / "project.yaml"))
        issues = project_mod.validate(self.proj)
        if issues:
            raise RuntimeError("spec → project.yaml の検証NG: " + "; ".join(issues))
        self.ctx = pipeline.Ctx(dry_run=False, force=False, key=_fal_key())
        self.cuts = {c["id"]: c for c in self.proj.cuts}
        # コンテナ再起動・再デプロイでローカルの生成物が消えても、Storage に上げた still / clip / audio を戻して続きから進める
        got = restore_generations(sb, self.proj, project_id)
        if got:
            print(f"  restore: {got} generated file(s) from Storage", flush=True)

    def _usd_delta(self, before: float) -> float:
        return round(sum(r["usd"] for r in self.ledger.read(self.proj)) - before, 4)

    def _ledger_total(self) -> float:
        return sum(r["usd"] for r in self.ledger.read(self.proj))

    def _put(self, file: Path, kind: str, cut: str | None, model: str | None, usd: float, table: str = "generations",
             extra: dict | None = None) -> None:
        scope = self.org or self.owner   # 新パス規約 <org_id>/<project>/...（org未解決なら owner）
        path = f"{scope}/{self.project_id}/{file.name}"
        self.sb.upload("assets", path, file)
        row = {"project_id": self.project_id, "owner": self.owner, "storage_path": path}
        if self.org:
            row["org_id"] = self.org
        if table == "generations":
            row.update({"cut": cut, "kind": kind, "model": model, "usd": usd, "status": "done"})
        else:
            row.update(extra or {})
        self.sb.insert(table, row)

    def _make_poster(self, mp4: "Path | None") -> None:
        """本編mp4の先頭付近から1フレームを切り出し、カバー（poster）として保存する。
        assets/<scope>/<project_id>/poster.jpg にアップロードし projects.poster_path を更新。
        ffmpeg が無い/失敗しても本処理は落とさない（カバーが無いだけ）。"""
        if not mp4 or not mp4.is_file():
            return
        ff = shutil.which("ffmpeg")
        if not ff:
            print("  poster: ffmpeg not found; skip", flush=True)
            return
        out = self.proj.generated / "poster.jpg"
        try:
            # -ss 0.5: 先頭の黒みを避けて“再生前の画面”らしい1枚に。長辺640へ縮小。
            subprocess.run(
                [ff, "-y", "-ss", "0.5", "-i", str(mp4), "-frames:v", "1",
                 "-vf", "scale='min(640,iw)':-2", "-q:v", "3", str(out)],
                check=True, capture_output=True,
            )
        except Exception as e:  # noqa: BLE001
            print(f"  poster: ffmpeg failed: {e}", flush=True)
            return
        if not out.is_file():
            return
        scope = self.org or self.owner
        path = f"{scope}/{self.project_id}/poster.jpg"
        try:
            self.sb.upload("assets", path, out)
            self.sb.update("projects", {"id": f"eq.{self.project_id}"}, {"poster_path": path})
            print(f"  poster: {path}", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"  poster: upload/update failed: {e}", flush=True)

    def run(self, job: dict) -> float:
        stage, cut_id = job["stage"], job.get("cut")
        before = self._ledger_total()
        self.notes = {}   # 検品の要確認・フォールバック等を jobs.detail に残す
        p, ctx = self.pipeline, self.ctx
        if stage in ("still", "review", "animate"):
            cut = self.cuts.get(cut_id)
            if not cut:
                raise RuntimeError(f"cut '{cut_id}' が spec に無い")
        if stage == "still":
            r = p.still_one(self.proj, ctx, cut)
            f = self.proj.generated / f"{cut_id}.still.png"
            if f.is_file():
                self._put(f, "still", cut_id, r.get("model"), r.get("usd", 0.0))
        elif stage == "review":
            f = self.proj.generated / f"{cut_id}.still.png"
            mtime0 = f.stat().st_mtime if f.is_file() else 0.0
            r = p.review_one(self.proj, ctx, cut, retake=True)
            if r.get("status") == "ng":
                # NG → スチルを再生成して再検品（1回）。2 回目も NG なら止めずに「要確認」を付けて進める（生成全体を失敗させない）
                r2 = p.still_one(self.proj, ctx, cut)
                r = p.review_one(self.proj, ctx, cut, retake=False)
                if r.get("status") == "ng":
                    rep_path = self.proj.generated / f"{cut_id}.review.json"
                    try:
                        rep = json.loads(rep_path.read_text(encoding="utf-8")); rep["pass"] = True; rep["needs_check"] = True
                        rep_path.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
                    except Exception:  # noqa: BLE001
                        pass
                    self.notes["needs_check"] = {"stage": "still", "ng": r.get("ng") or []}
                    print(f"  WARN  {cut_id}: 検品 2 回目も NG → 要確認として進める: " + ", ".join(r.get("ng") or []), flush=True)
                if f.is_file() and f.stat().st_mtime > mtime0:   # 作り直したスチルを Storage にも反映（古い方を上書き）
                    self._put(f, "still", cut_id, r2.get("model"), r2.get("usd", 0.0))
        elif stage == "animate":
            r = p.animate_one(self.proj, ctx, cut)
            if r.get("status") == "blocked":
                raise RuntimeError(f"animate blocked: {r.get('why')}")
            # クリップ検品（元スチル＋3 フレーム）。NG → 1 回作り直し → それでも NG ならクリップを捨ててスチル演出に切替
            rc = p.review_clip_one(self.proj, ctx, cut)
            if rc.get("status") == "ng":
                p.retake_clip(self.proj, cut_id)
                r = p.animate_one(self.proj, ctx, cut)
                rc = p.review_clip_one(self.proj, ctx, cut)
                if rc.get("status") == "ng":
                    p.reject_clip(self.proj, cut_id)
                    self.notes["clip_fallback"] = {"cut": cut_id, "ng": rc.get("ng") or [], "reasons": rc.get("reasons") or []}
                    print(f"  FALLBACK {cut_id}: クリップ検品 2 回 NG → スチル演出に切替（" + ", ".join(rc.get("ng") or []) + "）", flush=True)
            f = self.proj.generated / f"{cut_id}.mp4"
            if f.is_file():
                self._put(f, "clip", cut_id, r.get("model"), r.get("usd", 0.0))
        elif stage == "audio":
            p.audio(self.proj, ctx)
            adir = self.proj.generated / "audio"
            # 台帳（ledger）から音声ファイルごとのモデル・原価を引く（cut 列 = na1 / bgm_main 等 = ファイル名の stem）
            led = {}
            for rec in self.ledger.read(self.proj):
                if rec.get("stage") == "audio" and rec.get("cut"):
                    led[rec["cut"]] = rec
            for f in sorted(adir.glob("*.mp3")) if adir.is_dir() else []:
                rec = led.get(f.stem) or {}
                self._put(f, "audio", f.stem, rec.get("model"), float(rec.get("usd") or 0.0))
        elif stage == "build":
            res = p.build(self.proj, ctx)
            report = Path(res.get("report", ""))
            if report.is_file():
                self._put(report, "render", None, None, 0.0)
            primary = None       # ポスター元（最初の1本）
            primary_wide = None  # 横長を優先
            for item in (json.loads(report.read_text(encoding="utf-8")).get("items", []) if report.is_file() else []):
                dst = Path(item["dst"])
                if dst.is_file():
                    self._put(dst, "render", None, None, 0.0, table="renders",
                              extra={"variant": item.get("variant"), "format": item.get("platform")})
                    if primary is None:
                        primary = dst
                    plat = str(item.get("platform") or "").lower()
                    if primary_wide is None and any(k in plat for k in ("wide", "landscape", "16", "youtube", "yt")):
                        primary_wide = dst
                side = Path((item.get("credentials") or {}).get("sidecar", ""))
                if side.is_file():
                    self._put(side, "render", None, None, 0.0)
            self._make_poster(primary_wide or primary)   # カバー（再生前の1枚）を本編mp4から生成
        else:
            raise RuntimeError(f"未知のステージ: {stage}")
        return self._usd_delta(before)


def run_script_stage(sb: Supa, project_id: str, live: bool) -> float:
    """台本ステージ: projects.spec に narration / caption / 必要な素材 / 秒数を書き込む（brands.profile を参照）。"""
    proj = sb.select("projects", id=f"eq.{project_id}", select="spec,product,name,brand_id")
    if not proj:
        raise RuntimeError("project not found")
    spec = proj[0].get("spec") or {}
    spec.setdefault("meta", {})
    spec["meta"].setdefault("product", proj[0].get("product") or proj[0].get("name"))
    profile = {}
    if proj[0].get("brand_id"):
        br = sb.select("brands", id=f"eq.{proj[0]['brand_id']}", select="name,profile")
        if br:
            profile = dict(br[0].get("profile") or {})
            profile.setdefault("name", br[0].get("name"))
    patch, detail = script_gen.run(spec, profile, live)
    spec["cuts"] = patch["cuts"]
    spec["script"] = patch["script"]
    sb.update("projects", {"id": f"eq.{project_id}"}, {"spec": spec})
    src = patch["script"].get("source")
    print(f"  script: {src} ({len(patch['cuts'])} cuts)" + (f" model={detail.get('model')}" if detail.get("model") else "")
          + (f" warn={detail.get('warnings')}" if detail.get("warnings") else "") + (f" note={detail.get('note')}" if detail.get("note") else ""), flush=True)
    return JOB_USD["script"] if src == "ai" else 0.0


def execute(job: dict, live: bool, runner: "LiveRunner | None" = None) -> float:
    """ジョブを実行して実コスト(USD)を返す。

    DRY-RUN: 概算原価を返すだけ（生成物なし）。
    LIVE: LiveRunner が cm-pipeline のステージを実行し、生成物を Storage(assets) へ
      アップロードして generations / renders 行を作る。
    """
    if live:
        if runner is None:
            raise RuntimeError("live 実行には LiveRunner が必要です")
        return runner.run(job)
    return JOB_USD.get(job["stage"], 0.05)


def process_project(sb: Supa, project_id: str, owner: str, live: bool) -> int:
    """1プロジェクトの ready ジョブを可能な限り進める。処理件数を返す。"""
    processed = 0
    runner = None

    def ensure_runner():
        """LiveRunner は台本ステージの後に（最初の生成ジョブで）作る＝ナレーション入りの project.yaml を使う。"""
        nonlocal runner
        if not live or runner is not None:
            return runner
        proj = sb.select("projects", id=f"eq.{project_id}", select="spec,product,name,org_id,brand_id")
        if not proj:
            raise RuntimeError("project not found")
        runner = LiveRunner(sb, project_id, owner, proj[0].get("spec") or {},
                            proj[0].get("product") or proj[0].get("name"), proj[0].get("org_id"), proj[0].get("brand_id"))
        return runner

    header_shown = False

    def header():
        nonlocal header_shown
        if not header_shown:
            print(f"project {project_id} …", flush=True)
            header_shown = True

    for _ in range(500):
        jobs = sb.select("jobs", project_id=f"eq.{project_id}")
        # 依存先が failed のまま残る pending は永久に ready にならない → blocked として failed に倒す（UI に理由を出す）
        changed = True
        while changed:   # 連鎖（review 失敗 → animate → build）を同じ tick で伝播させる
            changed = False
            failed_keys = {job_key(x): (x.get("detail") or {}).get("error", "") for x in jobs if x["status"] == "failed"}
            for j in jobs:
                if j["status"] != "pending":
                    continue
                bad = [d for d in (j.get("deps") or []) if d in failed_keys]
                if bad:
                    header()
                    detail = {"error": f"blocked: {bad[0]} failed ({failed_keys[bad[0]][:120]})"[:300], "blocked_by": bad}
                    sb.update("jobs", {"id": f"eq.{j['id']}"}, {"status": "failed", "detail": detail})
                    print(f"  BLOCK {job_key(j):16} ← {bad[0]} failed", flush=True)
                    j["status"] = "failed"; j["detail"] = detail; changed = True
        pend = [j for j in jobs if ready(j, jobs)]
        if not pend:
            break
        header()
        for j in pend:
            sb.update("jobs", {"id": f"eq.{j['id']}"}, {"status": "running"})
            try:
                if j["stage"] == "script":
                    usd = run_script_stage(sb, project_id, live)
                else:
                    try:
                        ensure_runner()
                    except Exception as e:  # noqa: BLE001
                        print(f"  FAIL  project setup: {e}", flush=True)
                        sb.update("jobs", {"project_id": f"eq.{project_id}", "status": "eq.pending"},
                                  {"status": "failed", "detail": {"error": f"setup: {e!r}"[:300]}})
                        sb.update("jobs", {"id": f"eq.{j['id']}"}, {"status": "failed", "detail": {"error": f"setup: {e!r}"[:300]}})
                        return processed
                    usd = execute(j, live, runner)
                done_patch = {"status": "done", "usd": usd}
                notes = getattr(runner, "notes", None) if runner is not None else None
                if notes:
                    done_patch["detail"] = notes
                sb.update("jobs", {"id": f"eq.{j['id']}"}, done_patch)
                if usd > 0:
                    # コストのみ記録（credits=0）。残高消費は生成時に spend_credits(RPC) で実施済み。
                    sb.insert("credit_ledger", {
                        "owner": owner, "project_id": project_id, "stage": j["stage"],
                        "model": j["stage"], "usd": usd, "credits": 0,
                    })
                print(f"  done  {job_key(j):16} ${usd:.2f}", flush=True)
            except Exception as e:  # noqa: BLE001
                err = repr(e)
                sb.update("jobs", {"id": f"eq.{j['id']}"},
                          {"status": "failed", "detail": {"error": err[:300]}})
                print(f"  FAIL  {job_key(j):16} {e}", flush=True)
                if "FAL_BALANCE_OR_QUOTA" in err:   # 全生成が止まる重大事象 → 運用アラート
                    alert_ops("[Spot] fal 残高/クォータ枯渇の可能性",
                              "fal API がクレジット/クォータ不足で失敗しました。全生成が停止する恐れがあります。至急ご確認ください（残高の補充）。\n"
                              f"project={project_id}\njob={job_key(j)}\nerror={err[:500]}",
                              dedup_key="fal_balance")
            processed += 1
    # 全 build まで終わっていれば done に。恒久失敗があれば failed に落とし、前払いクレジットを自動返却。
    jobs = sb.select("jobs", project_id=f"eq.{project_id}")
    if jobs and any(j["stage"] != "script" for j in jobs) and all(j["status"] in SUCCESS for j in jobs):
        sb.update("projects", {"id": f"eq.{project_id}"}, {"status": "done"})
        if live:
            notify_done(sb, project_id, owner)   # 完了メール（RESEND_API_KEY があるときだけ送る）
    elif any(j["status"] == "failed" for j in jobs) and not any(j["status"] in ("pending", "running") for j in jobs):
        # これ以上進めない（pending/running なし）＝終局失敗 → failed 遷移＋返金（詰まり/二重課金の防止）。
        sb.update("projects", {"id": f"eq.{project_id}"}, {"status": "failed"})
        if live:
            try:
                refunded = sb._req("POST", "/rpc/refund_project_credits",
                                   body={"p_project": project_id, "p_reason": "generation_failed"})
                print(f"  refund  project {project_id}: {refunded}", flush=True)
            except Exception as e:  # noqa: BLE001
                print(f"  refund FAILED for {project_id}: {e}", flush=True)
    return processed


# ---------------------------------------------------------------- 完了メール（Resend）
def send_email(to: str, subject: str, html: str, text: str) -> bool:
    key = os.environ.get("RESEND_API_KEY")
    if not key or not to:
        return False
    body = {"from": os.environ.get("RESEND_FROM", "Spot <no-reply@creativepunx.com>"),
            "to": [to], "subject": subject, "html": html, "text": text}
    req = urllib.request.Request("https://api.resend.com/emails", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                                          "User-Agent": "SpotWorker/1.0 (+completion email)"},   # Python 既定 UA は Cloudflare に 403 (1010) で弾かれる
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            r.read()
        return True
    except urllib.error.HTTPError as e:
        print(f"  WARN  resend HTTP {e.code}: {e.read().decode()[:200]}", flush=True)
        return False


def notify_done(sb: Supa, project_id: str, owner: str) -> None:
    """制作完了をオーナーにメール（profiles.notify_done が ON のときだけ・1 回だけ）。"""
    try:
        proj = sb.select("projects", id=f"eq.{project_id}", select="name,notified_at")
        if not proj or proj[0].get("notified_at"):
            return
        prof = sb.select("profiles", id=f"eq.{owner}", select="notify_done")
        if prof and prof[0].get("notify_done") is False:
            return
        user = sb.admin_user(owner) or {}
        to = user.get("email")
        if not to:
            return
        lang = ((user.get("user_metadata") or {}).get("lang")) or "ja"
        name = proj[0].get("name") or ("your ad" if lang == "en" else "CM")
        link = os.environ.get("APP_URL") or os.environ.get("SUPABASE_URL", "")
        if lang == "en":
            subject = f"Your ad is ready — {name}"
            text = f"{name} has finished generating. Open Spot to review and export your files: {link}"
            html = f"<p><b>{name}</b> has finished generating.</p><p><a href=\"{link}\">Open Spot</a> to review the 3 patterns and export your files.</p><p style=\"color:#888\">You can turn these emails off in Spot → Sign-in &amp; security.</p>"
        else:
            subject = f"CMができあがりました — {name}"
            text = f"「{name}」の生成が終わりました。Spot を開いて確認・書き出しできます: {link}"
            html = f"<p>「<b>{name}</b>」の生成が終わりました。</p><p><a href=\"{link}\">Spot を開く</a>と、3パターンを確認して書き出せます。</p><p style=\"color:#888\">このメールは Spot → ログインとセキュリティ で停止できます。</p>"
        if send_email(to, subject, html, text):
            sb.update("projects", {"id": f"eq.{project_id}"}, {"notified_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
            print("  mail  completion email sent", flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"  WARN  notify_done failed: {e}", flush=True)


def tick(sb: Supa, only_project: str | None, live: bool, only_brand: str | None = None) -> int:
    """処理すべきプロジェクトを見つけて進める。処理件数を返す。ブランド取り込み（P3）も先に進める。"""
    total = 0
    if not only_project:
        try:
            total += brand_ingest.tick_brands(sb, only_brand, live)
        except Exception as e:  # noqa: BLE001
            print("brand ingest error:", e, flush=True)
    if only_brand:
        return total
    params = {"select": "project_id", "status": "eq.pending"}
    if only_project:
        params["project_id"] = f"eq.{only_project}"
    pending = sb.select("jobs", **params)
    project_ids = sorted({p["project_id"] for p in pending})
    for pid in project_ids:
        proj = sb.select("projects", id=f"eq.{pid}", select="owner,status")
        if not proj:
            continue
        owner = proj[0]["owner"]
        total += process_project(sb, pid, owner, live)   # 見出しは実際にジョブが動くときだけ出す
    return total


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="SPOT 生成ワーカー（Supabase jobs 駆動）")
    ap.add_argument("--project", help="対象プロジェクトID（省略時は全て）")
    ap.add_argument("--brand", help="ブランド取り込みだけを、このブランドIDについて実行")
    ap.add_argument("--watch", action="store_true", help="ポーリング常駐")
    ap.add_argument("--interval", type=float, default=5.0, help="--watch のポーリング間隔秒")
    ap.add_argument("--live", action="store_true", help="実生成（既定は DRY-RUN）")
    ap.add_argument("--stages", help="このワーカーが担当するステージをカンマ区切りで限定（例: script,still,review,animate,audio ／ build）。環境変数 WORKER_STAGES でも可")
    args = ap.parse_args(argv)
    global ALLOWED_STAGES
    st = (args.stages or os.environ.get("WORKER_STAGES") or "").strip()
    if st:
        ALLOWED_STAGES = {s.strip() for s in st.split(",") if s.strip()}
        print(f"stages: {sorted(ALLOWED_STAGES)}", flush=True)

    sb = Supa(env("SUPABASE_URL"), env("SUPABASE_SERVICE_ROLE_KEY"))
    mode = "LIVE" if args.live else "DRY-RUN"
    print(f"SPOT worker start (mode={mode}, project={args.project or 'ALL'})", flush=True)

    if not args.watch:
        n = tick(sb, args.project, args.live, args.brand)
        print(f"done. processed {n} job(s).", flush=True)
        return 0
    while True:
        try:
            tick(sb, args.project, args.live, args.brand)
        except Exception as e:  # noqa: BLE001
            print("tick error:", e, flush=True)
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
