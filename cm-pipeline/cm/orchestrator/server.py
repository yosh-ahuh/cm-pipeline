"""HTTP + SSE サーバ.

Web UI(komadori) が叩くバックエンドの最小形（Phase 2 の接続先）。
  POST /projects            {project, live?, workers?}  → DAGを起動（非同期）
  GET  /projects/<name>     現在のジョブ状態スナップショット
  GET  /projects/<name>/events   SSEで進捗を購読
  GET  /projects/<name>/cost     生成原価
  GET  /health
"""
from __future__ import annotations

import json
import queue
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .. import ledger, project as project_mod
from ..pipeline import Ctx
from . import db
from .engine import Engine
from .events import EventBus

# name -> {engine, bus, thread}
RUNS: dict[str, dict] = {}
_LOCK = threading.Lock()


def _start_run(project: str, *, live: bool, workers: int) -> dict:
    proj = project_mod.load(project)
    key = None
    if live:
        kp = project_mod.REPO.parent / ".fal_key"
        if not kp.is_file():
            raise FileNotFoundError(f"fal キーが見つかりません: {kp}")
        key = kp.read_text().strip()
    bus = EventBus()
    engine = Engine(proj, Ctx(dry_run=not live, key=key), workers=workers, bus=bus,
                    on_change=lambda snap: db.save(proj.name, snap))
    with _LOCK:
        RUNS[proj.name] = {"engine": engine, "bus": bus}
    t = threading.Thread(target=engine.run, name=f"run:{proj.name}", daemon=True)
    with _LOCK:
        RUNS[proj.name]["thread"] = t
    t.start()
    return engine.snapshot()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):  # 標準の逐一ログを抑制
        pass

    # ---- helpers ----
    def _json(self, code: int, obj) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _seg(self):
        return [s for s in urlparse(self.path).path.split("/") if s]

    # ---- routes ----
    def do_GET(self):
        seg = self._seg()
        if seg == ["health"]:
            return self._json(200, {"ok": True, "runs": list(RUNS)})
        if len(seg) >= 2 and seg[0] == "projects":
            name = seg[1]
            if len(seg) == 2:
                snap = _snapshot(name)
                return self._json(200 if snap else 404, snap or {"error": "unknown project"})
            if len(seg) == 3 and seg[2] == "cost":
                try:
                    proj = project_mod.load(name)
                except Exception as e:  # noqa: BLE001
                    return self._json(404, {"error": str(e)})
                return self._json(200, ledger.summary(ledger.read(proj)))
            if len(seg) == 3 and seg[2] == "events":
                return self._sse(name)
        return self._json(404, {"error": "not found"})

    def do_POST(self):
        seg = self._seg()
        if seg == ["projects"]:
            n = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(n) or b"{}")
            project = payload.get("project")
            if not project:
                return self._json(400, {"error": "project is required"})
            try:
                snap = _start_run(project, live=bool(payload.get("live")),
                                  workers=int(payload.get("workers", 3)))
            except Exception as e:  # noqa: BLE001
                return self._json(400, {"error": str(e)})
            return self._json(202, snap)
        return self._json(404, {"error": "not found"})

    def _sse(self, name: str):
        run = RUNS.get(name)
        if not run:
            return self._json(404, {"error": "no active run"})
        bus: EventBus = run["bus"]
        q, backlog = bus.subscribe()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        try:
            for ev in backlog:
                self.wfile.write(EventBus.sse(ev))
            self.wfile.flush()
            done = any(e.get("type") == "run.end" for e in backlog)
            while not done:
                try:
                    ev = q.get(timeout=15)
                    self.wfile.write(EventBus.sse(ev))
                    if ev.get("type") == "run.end":
                        done = True
                except queue.Empty:
                    self.wfile.write(b": keep-alive\n\n")  # ハートビート
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            bus.unsubscribe(q)


def _snapshot(name: str) -> dict | None:
    run = RUNS.get(name)
    if run:
        return run["engine"].snapshot()
    return db.load(name)


def serve(host: str = "127.0.0.1", port: int = 8787) -> None:
    srv = ThreadingHTTPServer((host, port), Handler)
    print(f"cm orchestrator listening on http://{host}:{port}", flush=True)
    print("  POST /projects {\"project\":\"mirai-koji\"}   GET /projects/<name>[/events|/cost]", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nbye", flush=True)
