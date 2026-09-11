"""スレッドセーフな進捗イベントバス（SSE配信の土台）.

各ジョブの状態遷移を購読者（SSEストリーム）へ push する。購読者ごとに Queue を持ち、
接続時にスナップショットを、以降は増分イベントを流す。
"""
from __future__ import annotations

import json
import queue
import threading
import time


class EventBus:
    def __init__(self) -> None:
        self._subs: list[queue.Queue] = []
        self._log: list[dict] = []      # 再送用の全履歴（接続時スナップショット）
        self._lock = threading.Lock()

    def publish(self, event: dict) -> None:
        event = {"ts": time.strftime("%H:%M:%S"), **event}
        with self._lock:
            self._log.append(event)
            subs = list(self._subs)
        for q in subs:
            q.put(event)

    def subscribe(self) -> tuple[queue.Queue, list[dict]]:
        q: queue.Queue = queue.Queue()
        with self._lock:
            self._subs.append(q)
            backlog = list(self._log)
        return q, backlog

    def unsubscribe(self, q: queue.Queue) -> None:
        with self._lock:
            if q in self._subs:
                self._subs.remove(q)

    def history(self) -> list[dict]:
        with self._lock:
            return list(self._log)

    @staticmethod
    def sse(event: dict) -> bytes:
        return f"data: {json.dumps(event, ensure_ascii=False)}\n\n".encode()
