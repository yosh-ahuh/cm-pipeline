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
_TONE = {"ドキュメンタリー": "documentary", "documentary": "documentary"}


def spec_to_project(project_id: str, spec: dict, product: str | None) -> dict:
    sel = spec.get("selections", {}) or {}
    meta = spec.get("meta", {}) or {}
    out = spec.get("output", {}) or {}
    formats = out.get("formats") or [{"id": "wide", "w": 1920, "h": 1080}]
    cuts = []
    narration = []   # P4: 台本ステージが付けたナレーション → script.narration（TTS は読み方適用済みの tts を優先）
    for i, c in enumerate(spec.get("cuts") or [], 1):
        if isinstance(c, str):
            c = {"id": c, "type": "live-action"}
        cut = {"id": c["id"], "type": c.get("type", "live-action")}
        role = c.get("role") or c["id"]
        label = script_gen.ROLE.get(role, {}).get("label", role)
        telop = c.get("telop") or ([c["caption"]] if c.get("caption") else [label])
        if c.get("narration"):
            nid = c.get("narration_id") or f"na{i}"
            narration.append({"id": nid, "text": c.get("narration_tts") or c["narration"], "display": c["narration"]})
            cut["narration"] = nid
        if cut["type"] == "live-action":
            subj = c.get("subject") or f"{sel.get('industry') or product or 'プロダクト'}の{sel.get('target') or '利用者'}。{label}"
            cut["still"] = {"subject": subj}
            cut["motion"] = {"resolution": "1080p"}
            if c.get("motion_en"):   # 台本ステージが書いた最小限の動き（英語）。手作業・ページめくり等は台本側で禁止済み
                cut["motion"]["prompt"] = f"{subj}. {c['motion_en']}. Camera slowly pushes in. Hands stay still; no objects are picked up, moved, pasted, written or turned; nothing new appears."
            cut["telop"] = telop
        elif cut["type"] == "cta":
            # ボタン文言は台本の字幕（例「お問い合わせはこちら」）を優先。検索語は CM 名ではなくブランド名
            brand_name = ((spec.get("brand") or {}).get("name") or "").strip()
            cut.update({"button": c.get("button") or c.get("caption") or "今すぐ 無料ではじめる", "badges": c.get("badges") or [],
                        "search": c.get("search") or brand_name or product, "note": c.get("note"), "telop": telop})
        elif cut["type"] == "graphic":
            cut["value"] = c.get("value") or {"label": c.get("caption") or label}
        elif cut["type"] == "ui":
            # assets: アプリが Storage に上げたスクショのパス配列（LiveRunner が assets/ にダウンロードして差し替え）
            # UI カットは caption を画面下に描くので、同文の telop は重ねない（明示 telop がある場合のみ）
            cut.update({"assets": list(c.get("assets") or []), "caption": c.get("caption") or label, "telop": c.get("telop") or []})
        else:
            cut["role"] = role
        if c.get("secs"):
            cut["dur"] = int(round(float(c["secs"]) * 30))
        cuts.append(cut)
    script = dict(spec.get("script") or {})
    if narration:
        script["narration"] = narration
    script.pop("userScript", None)
    return {
        "meta": {"name": project_id, "client": meta.get("client"), "product": product or meta.get("name"),
                 "goal": meta.get("goal") or sel.get("angle"), "source": "spot-app"},
        "output": {"fps": 30, "duration_frames": out.get("duration_frames", 961), "formats": formats,
                   "variants": out.get("variants") or [{"id": "A"}, {"id": "B"}, {"id": "C"}]},
        "brand": spec.get("brand") or {},
        "style": {"tone": _TONE.get(sel.get("tone"), "documentary"), "grade": "broadcast-cool"},
        "script": script,
        "cuts": cuts,
        "audio": spec.get("audio") or {"bgm": [{"id": "main", "model": "lyria2", "mood": "uplifting-corporate"}]},
        "compliance": spec.get("compliance") or {},
        "delivery": spec.get("delivery") or {},
        # 既定は project.yaml 駆動の汎用コンポジション SpotAd（cm-pipeline/cm/remotion_props.py が props を組む）
        "render": spec.get("render") or {"composition": "SpotAd", "prototype": str(SPOT_ROOT / "ad-prototype")},
    }


def localize_assets(sb: Supa, root: Path, d: dict, prefixes: list[str]) -> int:
    """project.yaml 内の Storage パス（<org_id>/... または旧 <owner>/...）を root/assets/ にダウンロードして相対パスに置換。"""
    n = 0
    pres = [p for p in prefixes if p]

    def fetch(p):
        nonlocal n
        if not isinstance(p, str) or not any(p.startswith(f"{pre}/") for pre in pres):
            return p
        dest = root / "assets" / Path(p).name
        if not dest.is_file():
            sb.download("assets", p, dest)
            n += 1
        return f"assets/{dest.name}"

    brand = d.get("brand") or {}
    for k in ("app_icon", "logo"):
        if brand.get(k):
            brand[k] = fetch(brand[k])
    if isinstance(brand.get("references"), list):
        brand["references"] = [fetch(x) for x in brand["references"]]
    for cut in d.get("cuts") or []:
        a = cut.get("assets")
        if isinstance(a, list):
            cut["assets"] = [fetch(x) for x in a]
        elif isinstance(a, dict):
            cut["assets"] = {k: fetch(v) for k, v in a.items()}
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
            for item in (json.loads(report.read_text(encoding="utf-8")).get("items", []) if report.is_file() else []):
                dst = Path(item["dst"])
                if dst.is_file():
                    self._put(dst, "render", None, None, 0.0, table="renders",
                              extra={"variant": item.get("variant"), "format": item.get("platform")})
                side = Path((item.get("credentials") or {}).get("sidecar", ""))
                if side.is_file():
                    self._put(side, "render", None, None, 0.0)
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
                sb.update("jobs", {"id": f"eq.{j['id']}"},
                          {"status": "failed", "detail": {"error": repr(e)[:300]}})
                print(f"  FAIL  {job_key(j):16} {e}", flush=True)
            processed += 1
    # 全 build まで終わっていれば done に
    jobs = sb.select("jobs", project_id=f"eq.{project_id}")
    if jobs and any(j["stage"] != "script" for j in jobs) and all(j["status"] in SUCCESS for j in jobs):
        sb.update("projects", {"id": f"eq.{project_id}"}, {"status": "done"})
        if live:
            notify_done(sb, project_id, owner)   # 完了メール（RESEND_API_KEY があるときだけ送る）
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
