"""モデルアダプタ層.

architecture.md「モデル抽象化層」の実装。fal.ai の各エンドポイントを
1関数=1アダプタで薄くラップし、配役表(model-casting.yaml)が「どの実装を使うか」を決める。
プロバイダ差し替えはアダプタ追加＋配役表1行で完結する（コード改変なし）。
"""

from .base import GenRequest, GenResult, DRY_PLACEHOLDER
from .registry import get_adapter, ADAPTERS

__all__ = ["GenRequest", "GenResult", "DRY_PLACEHOLDER", "get_adapter", "ADAPTERS"]
