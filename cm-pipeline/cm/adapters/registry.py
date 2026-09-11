"""モデル名 → アダプタ実装 の対応表.

配役表(model-casting.yaml)や cut の指定は「意味」を持つモデル名で書かれる。
ここがその名前を具体的な fal アダプタに解決する唯一の場所。
モデル追加は「アダプタを書いて1行足す」だけ（architecture.md #2）。
"""
from __future__ import annotations

from .. import prices
from .fal_video import KlingVideo, VeoVideo
from .fal_image import Imagen4, SeedreamEdit, SeedreamT2I
from .fal_consistency import NanoBananaEdit
from .fal_audio import MiniMaxTTS, Lyria2, MMAudioSFX, ElevenLabsSFX

# 疎通確認（2026-09-11 実キー）: imagen4 は未提供 / Seedream v4 t2i は動作・肌◎ /
# nano-banana edit は動作（ref付きで人物一貫性）。
#   ・新規スチル: SeedreamT2I（text-to-image）
#   ・人物一貫性: NanoBananaEdit（前カットの still を ref に）。pipeline が ref を渡せない時は t2i にフォールバック。
_still = SeedreamT2I()

# 正規化済みモデル名 → アダプタ・インスタンス（ステートレスなので使い回し可）。
ADAPTERS = {
    "veo3.1": VeoVideo(),
    "kling-2.5-turbo-pro": KlingVideo(),
    "seedream-v4": _still,
    "imagen4": _still,            # 未提供 → Seedream t2i に解決
    "seedream-v4-edit": _still,   # 高解像 edit は後日。当面 t2i
    "nano-banana": NanoBananaEdit(),   # 人物一貫性（要 ref。無ければ pipeline が t2i にフォールバック）
    "minimax-speech-02-hd": MiniMaxTTS(),
    "lyria2": Lyria2(),
    "mmaudio-v2": MMAudioSFX(),
    "elevenlabs-sfx-v2": ElevenLabsSFX(),   # 当該アカウントで upstream 400（サウンドロゴは当面スキップ）
}
_UNUSED = (Imagen4, SeedreamEdit)


def get_adapter(model: str):
    key = prices.normalize(model)
    if key not in ADAPTERS:
        raise KeyError(f"未知のモデル '{model}'（正規化: '{key}'）。registry.ADAPTERS に追加が必要。")
    return ADAPTERS[key]
