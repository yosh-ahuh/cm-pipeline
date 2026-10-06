"""モデル別の実測原価（USD）とクレジット換算。

architecture.md #4「コスト計上→クレジット換算」の実体。
値は fal.ai の実測に基づく概算。ここを直すだけで全ステージの原価集計に反映される。
"""

# 1呼び出しあたりの USD 概算。キーは model-casting の model 名（正規化後）。
USD: dict[str, float] = {
    # --- 動画化 (image-to-video) ---  ※2026-09「常に最新」更新。新版の値は概算（--live 実測で置換すること）。
    "veo3.1": 3.50,               # 1080p 6s。実測 $3-4/本
    "kling-3-turbo-pro": 0.70,    # v3 turbo pro（概算。v2.5=$0.35 の約2倍想定・要実測）
    "kling-2.5-turbo-pro": 0.35,  # 旧・実測 $0.35/本
    "seedance-2.5": 0.60,         # Seedance 2.5（概算・要実測）
    # --- スチル ---
    "imagen4": 0.04,
    "seedream-v5-pro": 0.05,      # v5 Pro t2i（概算・要実測。v4=$0.03）
    "seedream-v5-pro-edit": 0.08, # v5 Pro edit（概算）
    "seedream-v4": 0.03,          # 旧
    "seedream-v4-edit": 0.06,     # 旧
    "nano-banana-pro": 0.06,      # Nano Banana Pro（概算。旧=$0.04）
    "nano-banana": 0.04,          # 旧
    # --- 音声 ---
    "minimax-speech-2.8-hd": 0.02, # 1行あたり（概算）
    "minimax-speech-02-hd": 0.02,  # 旧
    "lyria3-pro": 0.06,           # Lyria 3 Pro（概算。旧 lyria2=$0.05）
    "lyria2": 0.05,               # 旧
    "elevenlabs-sfx-v2": 0.02,    # 効果音・サウンドロゴ
    "mmaudio-v2": 0.02,           # 実写カットの環境音・SE
    # --- 検品 ---
    "vision-review": 0.01,        # 1カット1チェック
    "vision-review-clip": 0.02,   # クリップ検品（元スチル＋3フレーム）
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
    # 「常に最新」方針：旧名も最新の正規名へ解決する（既存 spec / casting 互換）。
    aliases = {
        "veo": "veo3.1", "veo3": "veo3.1", "veo3.1": "veo3.1", "veo-3.1": "veo3.1",
        # Kling: 旧 2.5 も最新 v3 turbo pro に解決
        "kling": "kling-3-turbo-pro", "kling3": "kling-3-turbo-pro", "kling-3-turbo-pro": "kling-3-turbo-pro",
        "kling2.5": "kling-3-turbo-pro", "kling-2.5-turbo-pro": "kling-3-turbo-pro",
        # Seedance（新規採用）
        "seedance": "seedance-2.5", "seedance-2.5": "seedance-2.5", "seedance2.5": "seedance-2.5",
        "imagen4": "imagen4", "imagen-4": "imagen4",
        # Seedream: 旧 v4 も最新 v5 Pro に解決
        "seedream-v4": "seedream-v5-pro", "seedream-v5-pro": "seedream-v5-pro",
        "seedream": "seedream-v5-pro-edit", "seedream-v4-edit": "seedream-v5-pro-edit",
        "seedream-v5-pro-edit": "seedream-v5-pro-edit",
        # Nano Banana: 旧も pro に解決
        "nano-banana": "nano-banana-pro", "nano-banana-edit": "nano-banana-pro", "nano-banana-pro": "nano-banana-pro",
        # 音声: 旧も最新に解決
        "minimax": "minimax-speech-2.8-hd", "minimax-speech-02-hd": "minimax-speech-2.8-hd",
        "minimax-speech-2.8-hd": "minimax-speech-2.8-hd",
        "lyria": "lyria3-pro", "lyria2": "lyria3-pro", "lyria3": "lyria3-pro", "lyria3-pro": "lyria3-pro",
        "elevenlabs-sfx-v2": "elevenlabs-sfx-v2", "elevenlabs": "elevenlabs-sfx-v2",
        "mmaudio": "mmaudio-v2", "mmaudio-v2": "mmaudio-v2",
        "vision-review": "vision-review", "vision-review-clip": "vision-review-clip",
    }
    return aliases.get(m, m)
