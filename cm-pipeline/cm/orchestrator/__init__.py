"""Orchestrator (Phase 1b).

Phase 1a の CLI ステージ・ロジックを、非同期ジョブDAG＋ワーカープールで回す層。
カット表を still→review→animate のジョブDAGに展開し、依存が揃ったものから並列実行。
進捗は EventBus で配信（SSE）、状態は JSON で永続化（architecture.md「Orchestrator」）。

CLI と同じ `cm.pipeline` の *_one 関数を再利用するため、ロジックの二重管理は無い。
"""

from .jobs import Job, build_dag, SUCCESS
from .events import EventBus
from .engine import Engine

__all__ = ["Job", "build_dag", "SUCCESS", "EventBus", "Engine"]
