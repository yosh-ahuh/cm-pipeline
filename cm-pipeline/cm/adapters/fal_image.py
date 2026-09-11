"""スチル生成アダプタ。

疎通確認（2026-09-11・実キー）:
  ・imagen4 は **このアカウントで未提供**（fal.run 404 "Application imagen4 not found"）。
  ・**Seedream v4 text-to-image は動作**し、肌質感も良好（model-casting の "Seedream 肌◎" と一致）。
  → 新規スチルの既定を Seedream v4 t2i に変更（registry で imagen4 もこれに解決）。
実証済み: Kling / Veo / mmaudio / Seedream v4 (t2i)。
"""
from __future__ import annotations

from .base import Adapter, GenRequest, data_uri

# aspect_ratio → Seedream の image_size
_SEEDREAM_SIZE = {"16:9": "landscape_16_9", "9:16": "portrait_16_9", "1:1": "square_hd"}


class SeedreamT2I(Adapter):
    """Seedream v4 text-to-image（新規スチル生成）。実キーで疎通確認済み。"""
    endpoint = "fal-ai/bytedance/seedream/v4/text-to-image"
    model = "seedream-v4"
    ext = "jpg"
    kind = "image"

    def build_body(self, req: GenRequest) -> dict:
        body = {"prompt": req.prompt, "image_size": _SEEDREAM_SIZE.get(req.aspect_ratio, "landscape_16_9")}
        if req.negative:
            body["negative_prompt"] = req.negative
        return body

    def extract_url(self, resp: dict) -> str:
        return _first_image(resp)


class Imagen4(Adapter):
    # 未提供（404）のため残置のみ。registry は imagen4 → SeedreamT2I に解決する。
    endpoint = "fal-ai/imagen4/preview"
    model = "imagen4"
    ext = "png"
    kind = "image"

    def build_body(self, req: GenRequest) -> dict:
        body = {"prompt": req.prompt, "num_images": 1}
        if req.aspect_ratio:
            body["aspect_ratio"] = req.aspect_ratio
        if req.negative:
            body["negative_prompt"] = req.negative
        return body

    def extract_url(self, resp: dict) -> str:
        return _first_image(resp)


class SeedreamEdit(Adapter):
    endpoint = "fal-ai/bytedance/seedream/v4/edit"
    model = "seedream-v4-edit"
    ext = "png"
    kind = "image"

    def build_body(self, req: GenRequest) -> dict:
        refs = [data_uri(p, "image/png") for p in (req.ref_paths or ([req.image_path] if req.image_path else []))]
        return {
            "prompt": req.prompt,
            "image_urls": refs,
            "image_size": req.extra.get("image_size", "2048x2048"),
        }

    def extract_url(self, resp: dict) -> str:
        return _first_image(resp)


def _first_image(resp: dict) -> str:
    imgs = resp.get("images") or resp.get("image")
    if isinstance(imgs, list) and imgs:
        return imgs[0]["url"] if isinstance(imgs[0], dict) else imgs[0]
    if isinstance(imgs, dict):
        return imgs["url"]
    raise KeyError(f"no image url in response keys={list(resp)}")
