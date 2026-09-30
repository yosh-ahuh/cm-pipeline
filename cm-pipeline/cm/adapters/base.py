"""アダプタ基底 — fal.run への薄いラッパと共通の生成テンプレート。

実際の fal 呼び出しは ad-prototype/ の gen_*.py で実証済みのパラメータをそのまま踏襲する
（Kling/Veo/mmaudio の body 形状はミライ工事案件で検証済み）。
"""
from __future__ import annotations

import base64
import json
import os
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from pathlib import Path

from .. import prices

FAL_BASE = "https://fal.run/"
DRY_PLACEHOLDER = b"CM-PIPELINE DRY-RUN PLACEHOLDER\n"


@dataclass
class GenRequest:
    """1回の生成呼び出しの入力。ステージ側が組み立て、アダプタが解釈する。"""
    prompt: str = ""
    image_path: str | None = None       # i2v / edit の入力画像
    ref_paths: list[str] = field(default_factory=list)  # 一貫性編集の参照群
    negative: str = ""
    duration: str | None = None
    resolution: str | None = None
    aspect_ratio: str | None = None
    voice_id: str | None = None
    speed: float | None = None
    text: str | None = None             # TTS
    seconds: float | None = None        # BGM 長さ
    extra: dict = field(default_factory=dict)


@dataclass
class GenResult:
    path: str
    usd: float
    model: str
    dry: bool = False
    provider: dict = field(default_factory=dict)


class Adapter:
    """生成テンプレート。サブクラスは endpoint/body/url 抽出/種別を定義するだけ。"""

    #: fal のパス（FAL_BASE からの相対）。例: "fal-ai/veo3.1/image-to-video"
    endpoint: str = ""
    #: prices.USD のキーになるモデル名。
    model: str = ""
    #: 出力ファイルの拡張子。
    ext: str = "bin"
    #: 種別（casting/state のルーティング用）。
    kind: str = ""

    def build_body(self, req: GenRequest) -> dict:
        raise NotImplementedError

    def extract_url(self, resp: dict) -> str:
        raise NotImplementedError

    # --- テンプレートメソッド：ドライラン／実呼び出しの分岐を一手に引き受ける ---
    def generate(self, req: GenRequest, out_path: str, *, key: str | None,
                 dry_run: bool, timeout: int = 560) -> GenResult:
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        usd = prices.usd_for(self.model)

        if dry_run or not key:
            body = self.build_body(req)
            out.write_bytes(DRY_PLACEHOLDER + json.dumps(
                {"endpoint": self.endpoint, "model": self.model,
                 "body_preview": _preview(body)}, ensure_ascii=False, indent=2
            ).encode())
            return GenResult(str(out), usd, self.model, dry=True,
                             provider={"endpoint": self.endpoint})

        body = self.build_body(req)
        resp = fal_post(self.endpoint, body, key, timeout=timeout)
        url = self.extract_url(resp)
        _download(url, out)
        return GenResult(str(out), usd, self.model, dry=False,
                         provider={"endpoint": self.endpoint, "url": url})


# ---------------------------------------------------------------- http helpers
def fal_post(endpoint: str, body: dict, key: str, *, timeout: int = 560) -> dict:
    """fal.run へ同期POST（エンドポイントが完了までブロック）。gen_*.py と同一方式。"""
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        FAL_BASE + endpoint.lstrip("/"),
        data=data,
        headers={"Authorization": f"Key {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:400]
        low = detail.lower()
        # 残高不足/クォータ超過は「全生成が止まる」重大事象。ログで即検知できるよう目立つ印を付ける
        # （worker がこの印を出力→運用側は "FAL_BALANCE_OR_QUOTA" を監視してアラート/自動チャージにつなぐ）。
        if e.code in (402, 429) or any(k in low for k in ("insufficient", "balance", "quota", "exhausted", "payment required", "out of credits")):
            raise RuntimeError(f"FAL_BALANCE_OR_QUOTA fal {endpoint} HTTP {e.code}: {detail}") from e
        raise RuntimeError(f"fal {endpoint} HTTP {e.code}: {detail}") from e


def data_uri(path: str, mime: str) -> str:
    b = base64.b64encode(Path(path).read_bytes()).decode()
    return f"data:{mime};base64,{b}"


def mime_of(path) -> str:
    """画像 MIME を **内容（マジックバイト）** から判定する。
    Seedream は jpg を返すが pipeline はファイル名を .png 固定にするため、拡張子では誤判定する。"""
    try:
        b = Path(path).read_bytes()[:12]
    except Exception:
        return "image/png"
    if b[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        return "image/webp"
    return "image/png"


def _download(url: str, out: Path) -> None:
    urllib.request.urlretrieve(url, out)


def _preview(body: dict) -> dict:
    """data URI 等の巨大値を伏せた body のプレビュー（ドライラン出力用）。"""
    clean = {}
    for k, v in body.items():
        if isinstance(v, str) and v.startswith("data:"):
            clean[k] = f"<data-uri {len(v)}B>"
        elif isinstance(v, str) and len(v) > 220:
            clean[k] = v[:200] + "…"
        else:
            clean[k] = v
    return clean
