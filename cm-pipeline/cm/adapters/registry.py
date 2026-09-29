"""モデル名 → アダプタ実装 の対応表.

配役表(model-casting.yaml)や cut の指定は「意味」を持つモデル名で書かれる。
ここがその名前を具体的な fal アダプタに解決する唯一の場所。
モデル追加は「アダプタを書いて1行足す」だけ（architecture.md #2）。
"""
from __future__ import annotations

from .. import prices
from .fal_video import KlingVideo, VeoVideo, Seedance25Video
from .fal_image import Imagen4, SeedreamEdit, SeedreamT2I
from .fal_consistency import NanoBananaEdit
from .fal_audio import MiniMaxTTS, Lyria2, MMAudioSFX, ElevenLabsSFX

# 「常に最新」方針（2026-09 更新）で各アダプタを最新版に更新：
#   Kling 2.5→v3 turbo pro / Seedream v4→v5 Pro / nano-banana→pro / MiniMax 02-hd→2.8-hd / Lyria2→Lyria3 Pro。
#   Seedance 2.5 を新たに選択肢として追加。旧モデル名は下のエイリアスで新実装に解決（既存 spec 互換）。
#   ⚠ 各エンドポイントは fal 公開一覧で実在確認済みだが、body/レスポンス形状は本番前に必ず --live でスモークテストすること
#     （tools/check_models.py で新版の有無を随時チェックできる）。
_still = SeedreamT2I()          # Seedream v5 Pro (t2i)
_kling = KlingVideo()           # Kling v3 turbo pro
_veo = VeoVideo()               # Veo 3.1（現行トップ・据置）
_seedance = Seedance25Video()   # Seedance 2.5
_nano = NanoBananaEdit()        # Nano Banana Pro
_minimax = MiniMaxTTS()         # MiniMax speech 2.8-hd
_lyria = Lyria2()               # Lyria 3 Pro
_mmaudio = MMAudioSFX()
_eleven = ElevenLabsSFX()

# 正規化済みモデル名 → アダプタ・インスタンス（ステートレス＝使い回し可）。旧名も新実装に解決。
ADAPTERS = {
    # --- 動画化 (image-to-video) ---
    "veo3.1": _veo,
    "kling-3-turbo-pro": _kling, "kling-2.5-turbo-pro": _kling,   # 旧名→新実装
    "seedance-2.5": _seedance,
    # --- スチル (text-to-image) ---
    "seedream-v5-pro": _still, "seedream-v4": _still, "imagen4": _still,   # imagen4 未提供 → Seedream に解決
    "seedream-v5-pro-edit": _still, "seedream-v4-edit": _still,            # 高解像 edit は当面 t2i にフォールバック
    # --- 人物一貫性 ---
    "nano-banana-pro": _nano, "nano-banana": _nano,
    # --- 音声 ---
    "minimax-speech-2.8-hd": _minimax, "minimax-speech-02-hd": _minimax,
    "lyria3-pro": _lyria, "lyria2": _lyria,
    "mmaudio-v2": _mmaudio,
    "elevenlabs-sfx-v2": _eleven,   # 当該アカウントで upstream 400（サウンドロゴは当面スキップ）
}
_UNUSED = (Imagen4, SeedreamEdit)


def get_adapter(model: str):
    key = prices.normalize(model)
    if key not in ADAPTERS:
        raise KeyError(f"未知のモデル '{model}'（正規化: '{key}'）。registry.ADAPTERS に追加が必要。")
    return ADAPTERS[key]
