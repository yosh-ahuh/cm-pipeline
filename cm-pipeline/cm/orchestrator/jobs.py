"""ジョブモデルと DAG 構築.

1本のCM = 20〜40個の非同期AIジョブの連鎖（architecture.md）。ここではカット表を
still→review→animate のチェーンに展開し、audio と build を加えて DAG を作る。
"""
from __future__ import annotations

from dataclasses import dataclass, field

# 依存が満たされたとみなす（下流を進められる）状態。
SUCCESS = {"done", "skipped"}
# これ以上進めない終端の失敗状態（下流は blocked になる）。
FAILED = {"failed", "blocked"}


@dataclass
class Job:
    id: str                       # 例: "still:cut01" / "audio" / "build"
    stage: str                    # still / review / animate / audio / build
    cut: str | None               # 対象カットID（audio/build は None）
    deps: list[str] = field(default_factory=list)
    status: str = "pending"       # pending/running/done/skipped/failed/blocked
    usd: float = 0.0
    retries: int = 0
    detail: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"id": self.id, "stage": self.stage, "cut": self.cut, "deps": self.deps,
                "status": self.status, "usd": round(self.usd, 4),
                "retries": self.retries, "detail": self.detail}


def build_dag(proj) -> dict[str, Job]:
    """Project から DAG を生成。live-action は still→review→animate の直列。

    build は全 animate と audio の完了に依存する（成果物が揃ってから合成）。
    """
    jobs: dict[str, Job] = {}
    animate_ids: list[str] = []
    for cut in proj.live_cuts():
        cid = cut["id"]
        s, r, a = f"still:{cid}", f"review:{cid}", f"animate:{cid}"
        jobs[s] = Job(s, "still", cid, [])
        jobs[r] = Job(r, "review", cid, [s])
        jobs[a] = Job(a, "animate", cid, [r])
        animate_ids.append(a)
    jobs["audio"] = Job("audio", "audio", None, [])
    jobs["build"] = Job("build", "build", None, animate_ids + ["audio"])
    return jobs


def ready(jobs: dict[str, Job]) -> list[Job]:
    """今すぐ実行可能な pending ジョブ（全依存が SUCCESS）を返す。

    依存に失敗が含まれる pending は blocked に落とす（副作用）。
    """
    out: list[Job] = []
    for j in jobs.values():
        if j.status != "pending":
            continue
        dep_status = [jobs[d].status for d in j.deps]
        if any(s in FAILED for s in dep_status):
            j.status = "blocked"
            j.detail = {"why": "upstream-failed"}
        elif all(s in SUCCESS for s in dep_status):
            out.append(j)
    return out


def terminal(jobs: dict[str, Job]) -> bool:
    return all(j.status not in ("pending", "running") for j in jobs.values())
