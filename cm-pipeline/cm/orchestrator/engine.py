"""ワーカープール実行エンジン.

DAG の依存が揃ったジョブから並列に実行する。各ジョブは CLI と同じ
`cm.pipeline` の per-cut / batch 関数を呼ぶ（ロジックの二重管理なし）。
生成は数分かかりうる → スレッドで並列化（fal は同期エンドポイント）。
"""
from __future__ import annotations

import threading
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from typing import Callable

from .. import ledger, pipeline
from ..pipeline import Ctx
from ..project import Project
from .events import EventBus
from .jobs import Job, build_dag, ready, terminal


class Engine:
    def __init__(self, proj: Project, ctx: Ctx, *, workers: int = 3,
                 bus: EventBus | None = None,
                 on_change: Callable[[dict], None] | None = None) -> None:
        self.proj = proj
        self.ctx = ctx
        self.workers = max(1, workers)
        self.bus = bus or EventBus()
        self.on_change = on_change
        self.jobs: dict[str, Job] = build_dag(proj)
        self._lock = threading.Lock()

    # ---- job → pipeline op ----
    def _cut(self, cid: str) -> dict:
        return next(c for c in self.proj.cuts if c.get("id") == cid)

    def _run_job(self, job: Job) -> tuple[str, float, dict]:
        p, ctx = self.proj, self.ctx
        if job.stage == "still":
            r = pipeline.still_one(p, ctx, self._cut(job.cut))
            return ("done" if r["status"] == "made" else "skipped"), r.get("usd", 0.0), r
        if job.stage == "review":
            r = pipeline.review_one(p, ctx, self._cut(job.cut))
            status = {"pass": "done", "ng": "failed", "wait": "failed"}[r["status"]]
            return status, 0.0, r
        if job.stage == "animate":
            r = pipeline.animate_one(p, ctx, self._cut(job.cut))
            status = {"made": "done", "skipped": "skipped", "blocked": "failed"}[r["status"]]
            return status, r.get("usd", 0.0), r
        if job.stage == "audio":
            return "done", 0.0, pipeline.audio(p, ctx)
        if job.stage == "build":
            return "done", 0.0, pipeline.build(p, ctx)
        raise ValueError(f"unknown stage {job.stage}")

    # ---- run loop ----
    def run(self) -> dict:
        self._emit("run.start", {"jobs": len(self.jobs)})
        with ThreadPoolExecutor(max_workers=self.workers) as ex:
            running: dict = {}
            while not terminal(self.jobs):
                with self._lock:
                    batch = ready(self.jobs)
                    for j in batch:
                        j.status = "running"
                for j in batch:
                    self._emit("job", j.as_dict())
                    running[ex.submit(self._run_job, j)] = j
                if not running:
                    break  # 進めるジョブが無い（全て blocked 等）
                done, _ = wait(running, return_when=FIRST_COMPLETED)
                for fut in done:
                    j = running.pop(fut)
                    try:
                        status, usd, detail = fut.result()
                    except Exception as e:  # noqa: BLE001
                        status, usd, detail = "failed", 0.0, {"error": repr(e)[:300]}
                    with self._lock:
                        j.status, j.usd, j.detail = status, usd, detail
                    self._emit("job", j.as_dict())
        summary = self.snapshot()
        self._emit("run.end", summary["totals"])
        return summary

    # ---- reporting ----
    def snapshot(self) -> dict:
        with self._lock:
            jobs = [j.as_dict() for j in self.jobs.values()]
        by_status: dict[str, int] = {}
        for j in jobs:
            by_status[j["status"]] = by_status.get(j["status"], 0) + 1
        cost = ledger.summary(ledger.read(self.proj))
        return {"project": self.proj.name, "jobs": jobs,
                "totals": {"by_status": by_status, "count": len(jobs),
                           "usd": cost["usd"], "jpy": cost["jpy"], "credits": cost["credits"]}}

    def _emit(self, kind: str, data: dict) -> None:
        self.bus.publish({"type": kind, "project": self.proj.name, **data})
        if self.on_change:
            self.on_change(self.snapshot())
