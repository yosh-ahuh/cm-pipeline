"""動画化アダプタ (image-to-video)。Kling と Veo。

body 形状は ad-prototype/gen_clips.py / gen_veo_batch.py で実証済みのものを踏襲。
配役表 model-casting.yaml の animation ルール（暗部=Kling / 明部・動き=Veo）で選択される。
"""
from __future__ import annotations

from .base import Adapter, GenRequest, data_uri, mime_of

# gen_veo_batch.py の GUARD 相当（Veo の甘さ・カメラ目線・モーションブラー対策）。
VEO_GUARD = (
    " Crisp sharp motion without motion blur. His face stays exactly the same throughout, "
    "detailed skin texture with pores preserved. He NEVER looks toward the camera. "
    "Subtle realistic motion, documentary style, natural muted colors."
)
VEO_NEGATIVE = ("looking at camera, eye contact, facing the viewer, morphing face, changing face, "
                "distortion, motion blur, ghosting, trailing, soft focus, blurry, "
                "new objects appearing, duplicated objects, objects multiplying, page turning, pasting, writing, "
                "text changing, extra hands, extra fingers")
KLING_NEGATIVE = ("blur, distortion, low quality, extra fingers, morphing face, changing face, "
                  "changing clothes, oversaturated")


class KlingVideo(Adapter):
    # 常に最新方針（2026-09 更新）: Kling 2.5 turbo pro → v3 turbo pro（ネイティブ4K・動き/一貫性向上）。
    # body 形状は v2.5 と同一（prompt/image_url/duration/negative_prompt）。※本番投入前に必ず --live スモークテスト。
    endpoint = "fal-ai/kling-video/v3/turbo/pro/image-to-video"
    model = "kling-3-turbo-pro"
    ext = "mp4"
    kind = "video"

    def build_body(self, req: GenRequest) -> dict:
        return {
            "prompt": req.prompt,
            "image_url": data_uri(req.image_path, mime_of(req.image_path)),
            "duration": req.duration or "5",
            "negative_prompt": req.negative or KLING_NEGATIVE,
        }

    def extract_url(self, resp: dict) -> str:
        return resp["video"]["url"]


class Seedance25Video(Adapter):
    # ByteDance Seedance 2.5（image-to-video）。2026時点で最上位クラス（30秒/4K・優れたモーション/リップシンク）。
    # ※fal の bytedance/ ネームスペース（fal-ai/ 接頭辞なし）。本番投入前に --live スモークテスト。
    endpoint = "bytedance/seedance-2.5/image-to-video"
    model = "seedance-2.5"
    ext = "mp4"
    kind = "video"

    def build_body(self, req: GenRequest) -> dict:
        body = {
            "prompt": req.prompt,
            "image_url": data_uri(req.image_path, mime_of(req.image_path)),
            "resolution": req.resolution or "1080p",
        }
        if req.duration:
            body["duration"] = req.duration
        return body

    def extract_url(self, resp: dict) -> str:
        v = resp.get("video") or {}
        return v["url"] if isinstance(v, dict) else v


class VeoVideo(Adapter):
    endpoint = "fal-ai/veo3.1/image-to-video"
    model = "veo3.1"
    ext = "mp4"
    kind = "video"

    def build_body(self, req: GenRequest) -> dict:
        prompt = req.prompt
        if VEO_GUARD.strip() not in prompt:
            prompt = prompt + VEO_GUARD
        return {
            "prompt": prompt,
            "image_url": data_uri(req.image_path, mime_of(req.image_path)),
            "duration": req.duration or "6s",
            "resolution": req.resolution or "1080p",   # 必須。720pは甘くなる
            "generate_audio": False,
            "negative_prompt": req.negative or VEO_NEGATIVE,
        }

    def extract_url(self, resp: dict) -> str:
        return resp["video"]["url"]
