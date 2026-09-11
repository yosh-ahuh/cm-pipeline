"""モデル別の実測原価（USD）とクレジット換算。

architecture.md #4「コスト計上→クレジット換算」の実体。
値は fal.ai の実測に基づく概算。ここを直すだけで全ステージの原価集計に反映される。
"""

# 1呼び出しあたりの USD 概算。キーは model-casting の model 名（正規化後）。
USD: dict[str, float] = {
    # --- 動画化 (image-to-video) ---
    "veo3.1": 3.50,               # 1080p 6s。実測 $3-4/本
    "kling-2.5-turbo-pro": 0.35,  # 5s。実測 $0.35/本
    # --- スチル ---
    "imagen4": 0.04,
    "seedream-v4": 0.03,          # text-to-image（新規スチル。実測 ≈$0.03）
    "seedream-v4-edit": 0.06,     # 2048px 焼き直し
    "nano-banana": 0.04,          # 一貫性編集（顔・服固定）
    # --- 音声 ---
    "minimax-speech-02-hd": 0.02, # 1行あたり
    "lyria2": 0.05,               # 1トラックあたり
    "elevenlabs-sfx-v2": 0.02,    # 効果音・サウンドロゴ
    "mmaudio-v2": 0.02,           # 実写カットの環境音・SE
    # --- 検品 ---
    "vision-review": 0.01,        # 1カット1チェック
}

# 未知モデルのフォールバック原価。
DEFAULT_USD = 0.05

# 換算レート。UI「クレジット残」「¥」表示と整合させるための係数。
JPY_PER_USD = 150.0     # 為替の目安（請求時に実レートで上書き）
USD_PER_CREDIT = 0.30   # 1クレジットの原価目安。UI: CM1本 ≒ 1クレジット ≒ ¥1,200前後


def usd_for(model: str) -> float:
    """モデル名から1呼び出しの USD 概算を返す。"""
    return USD.get(normalize(model), DEFAULT_USD)


def to_jpy(usd: float) -> float:
    return usd * JPY_PER_USD


def to_credits(usd: float) -> float:
    return usd / USD_PER_CREDIT


def normalize(model: str | None) -> str:
    """`veo`, `veo3`, `kling` 等の表記ゆれを price/adapters のキーに正規化。"""
    if not model:
        return ""
    m = model.strip().lower()
    aliases = {
        "veo": "veo3.1", "veo3": "veo3.1", "veo3.1": "veo3.1", "veo-3.1": "veo3.1",
        "kling": "kling-2.5-turbo-pro", "kling2.5": "kling-2.5-turbo-pro",
        "kling-2.5-turbo-pro": "kling-2.5-turbo-pro",
        "imagen4": "imagen4", "imagen-4": "imagen4",
        "seedream-v4": "seedream-v4",
        "seedream": "seedream-v4-edit", "seedream-v4-edit": "seedream-v4-edit",
        "nano-banana": "nano-banana", "nano-banana-edit": "nano-banana",
        "minimax": "minimax-speech-02-hd", "minimax-speech-02-hd": "minimax-speech-02-hd",
        "lyria": "lyria2", "lyria2": "lyria2",
        "elevenlabs-sfx-v2": "elevenlabs-sfx-v2", "elevenlabs": "elevenlabs-sfx-v2",
        "mmaudio": "mmaudio-v2", "mmaudio-v2": "mmaudio-v2",
        "vision-review": "vision-review",
    }
    return aliases.get(m, m)
