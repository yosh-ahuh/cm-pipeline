"""音声アダプタ。ナレーション(MiniMax) / BGM(Lyria2) / 効果音(mmaudio・ElevenLabs)。

疎通確認済み（2026-09-11）: MiniMax speech-02-hd / Lyria2 / mmaudio-v2。
MiniMax は日本語ボイス多数＋emotion(happy/sad/angry/neutral/fearful/surprised) で声・トーンを可変。
ElevenLabs は当該アカウント未提供（upstream 400）。
"""
from __future__ import annotations

from .base import Adapter, GenRequest, data_uri

# MiniMax が受け付ける emotion（calm は不可）。
_MINIMAX_EMOTIONS = {"happy", "sad", "angry", "neutral", "fearful", "surprised", "disgusted"}


class MiniMaxTTS(Adapter):
    # 常に最新方針（2026-09 更新）: speech-02-hd → **speech-2.8-hd**。
    # ※voice_id は版で対応リストが変わり得る。--live スモークで日本語ボイスの実在を確認すること。
    endpoint = "fal-ai/minimax/speech-2.8-hd"
    model = "minimax-speech-2.8-hd"
    ext = "mp3"
    kind = "audio"

    def build_body(self, req: GenRequest) -> dict:
        vs = {
            "voice_id": req.voice_id or "Japanese_LoyalKnight",
            "speed": req.speed or 1.0,
        }
        emo = (req.extra or {}).get("emotion")
        if emo in _MINIMAX_EMOTIONS:
            vs["emotion"] = emo
        return {"text": req.text or req.prompt, "voice_setting": vs}

    def extract_url(self, resp: dict) -> str:
        a = resp.get("audio")
        return a["url"] if isinstance(a, dict) else a


class Lyria2(Adapter):
    # 常に最新方針（2026-09 更新）: Lyria2 → **Lyria 3 Pro**（BGM品質向上）。クラス名は互換のため据置。
    endpoint = "fal-ai/lyria3/pro"
    model = "lyria3-pro"
    ext = "mp3"
    kind = "audio"

    def build_body(self, req: GenRequest) -> dict:
        body = {"prompt": req.prompt}
        if req.seconds:
            body["duration_seconds"] = req.seconds
        return body

    def extract_url(self, resp: dict) -> str:
        a = resp.get("audio")
        return a["url"] if isinstance(a, dict) else a


class MMAudioSFX(Adapter):
    """映像に環境音・効果音を付与（gen_sfx.py と同一方式）。"""
    endpoint = "fal-ai/mmaudio-v2"
    model = "mmaudio-v2"
    ext = "mp4"
    kind = "audio"

    def build_body(self, req: GenRequest) -> dict:
        return {
            "video_url": data_uri(req.image_path, "video/mp4"),  # 入力は動画
            "prompt": req.prompt,
            "negative_prompt": req.negative or "music, melody, speech, voice, talking",
        }

    def extract_url(self, resp: dict) -> str:
        v = resp.get("video") or resp.get("audio") or {}
        return v["url"] if isinstance(v, dict) else v


class ElevenLabsSFX(Adapter):
    """効果音・サウンドロゴ（テキスト記述 → 音）。"""
    endpoint = "fal-ai/elevenlabs/sound-effects"
    model = "elevenlabs-sfx-v2"
    ext = "mp3"
    kind = "audio"

    def build_body(self, req: GenRequest) -> dict:
        body = {"text": req.text or req.prompt}
        if req.seconds:
            body["duration_seconds"] = req.seconds
        return body

    def extract_url(self, resp: dict) -> str:
        a = resp.get("audio")
        return a["url"] if isinstance(a, dict) else a
