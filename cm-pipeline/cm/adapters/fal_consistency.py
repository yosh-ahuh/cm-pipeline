"""人物一貫性アダプタ (nano-banana edit)。実キーで疎通確認済み（2026-09-11）。

顔・髪型・服装を完全一致で固定。ref 画像（前カットのstill）を渡すと同一人物を保つ。
endpoint: fal-ai/nano-banana/edit、body: {prompt, image_urls:[data-uri]}。
"""
from __future__ import annotations

from .base import Adapter, GenRequest, data_uri, mime_of

GUARD = " 顔・髪型・服装を完全一致で保持。ロゴなし。ONE single photograph, not a collage."


class NanoBananaEdit(Adapter):
    # 常に最新方針（2026-09 更新）: nano-banana → **nano-banana-pro**（Google最新・人物一貫性/文字精度向上）。
    endpoint = "fal-ai/nano-banana-pro/edit"
    model = "nano-banana-pro"
    ext = "png"
    kind = "image"

    def build_body(self, req: GenRequest) -> dict:
        refs = req.ref_paths or ([req.image_path] if req.image_path else [])
        return {
            "prompt": (req.prompt + GUARD) if GUARD.strip() not in req.prompt else req.prompt,
            "image_urls": [data_uri(p, mime_of(p)) for p in refs],
        }

    def extract_url(self, resp: dict) -> str:
        imgs = resp.get("images")
        if isinstance(imgs, list) and imgs:
            return imgs[0]["url"] if isinstance(imgs[0], dict) else imgs[0]
        raise KeyError(f"no image url in response keys={list(resp)}")
