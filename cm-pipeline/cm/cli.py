"""cm — コマンドラインエントリ.

    cm validate <project>
    cm stills   <project>          # カット表 → スチル生成
    cm review   <project> [--retake]
    cm animate  <project>          # 承認スチル → 動画化（配役表で Kling/Veo 振り分け）
    cm audio    <project>          # NA / BGM / サウンドロゴ
    cm build    <project>          # Remotion 合成 → 形式別レンダ
    cm run      <project>          # stills→review→animate→audio→build
    cm cost     <project>          # 生成原価の集計
    cm clean    <project>          # .done マーカーを削除して再生成可能に

既定は DRY-RUN（課金なし・原価は概算計上）。実生成は --live。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, ledger, prices, project as project_mod, state
from . import pipeline
from .pipeline import Ctx


def _resolve_key(args) -> str | None:
    if args.dry_run:
        return None
    path = Path(args.key) if args.key else (project_mod.REPO.parent / ".fal_key")
    if not path.is_file():
        sys.exit(f"--live 指定だが fal キーが見つかりません: {path}")
    return path.read_text().strip()


def _ctx(args) -> Ctx:
    return Ctx(dry_run=args.dry_run, force=args.force, key=_resolve_key(args))


def _load(args) -> project_mod.Project:
    try:
        return project_mod.load(args.project)
    except (FileNotFoundError, Exception) as e:  # noqa: BLE001
        sys.exit(f"プロジェクト読み込み失敗: {e}")


def _banner(proj, args) -> None:
    mode = "DRY-RUN" if args.dry_run else "LIVE"
    print(f"[{proj.name}]  mode={mode}  cuts={len(proj.cuts)}  formats={len(proj.formats)}"
          f"  variants={len(proj.variants)}", flush=True)


# ---------------------------------------------------------------- commands
def cmd_validate(args):
    proj = _load(args)
    issues = project_mod.validate(proj)
    if not issues:
        print(f"✓ {proj.name}: project.yaml は schema 準拠です（cuts={len(proj.cuts)}）")
        return 0
    print(f"✗ {proj.name}: {len(issues)} 件の問題")
    for i in issues:
        print("  -", i)
    return 1


def _run_stage(args, fn, **kw):
    proj = _load(args)
    _banner(proj, args)
    res = fn(proj, _ctx(args), **kw)
    print("→", res)
    return 0


def cmd_stills(args):  return _run_stage(args, pipeline.stills)
def cmd_animate(args): return _run_stage(args, pipeline.animate)
def cmd_audio(args):   return _run_stage(args, pipeline.audio)
def cmd_build(args):   return _run_stage(args, pipeline.build)
def cmd_review(args):  return _run_stage(args, pipeline.review, retake=args.retake)


def cmd_run(args):
    proj = _load(args)
    _banner(proj, args)
    ctx = _ctx(args)
    for name, fn in [("stills", pipeline.stills), ("review", pipeline.review),
                     ("animate", pipeline.animate), ("audio", pipeline.audio),
                     ("build", pipeline.build)]:
        print(f"── {name} ──")
        print("→", fn(proj, ctx))
    print("── cost ──")
    _print_cost(proj)
    return 0


def cmd_cost(args):
    proj = _load(args)
    _print_cost(proj)
    return 0


def _print_cost(proj):
    s = ledger.summary(ledger.read(proj))
    if not s["count"]:
        print("台帳が空です（まだ生成していません）。")
        return
    print(f"生成回数: {s['count']}   概算原価: ${s['usd']}  ≒ ¥{s['jpy']:,}  ≒ {s['credits']} クレジット")
    if s["dry_usd"]:
        print(f"  （うち DRY-RUN 概算: ${s['dry_usd']}）")
    print("  ステージ別:")
    for k, v in s["by_stage"].items():
        print(f"    {k:<10} ${v}")
    print("  モデル別:")
    for k, v in s["by_model"].items():
        print(f"    {k:<24} ${v}")


def cmd_clean(args):
    proj = _load(args)
    n = state.clear(proj)
    print(f"✓ {n} 個の .done マーカーを削除しました（生成物は保持）。")
    return 0


# ---------------------------------------------------------------- orchestrator
def cmd_orchestrate(args):
    """DAG をワーカープールで実行（Phase 1b をインプロセスで）。"""
    from .orchestrator.engine import Engine
    from .orchestrator import db
    proj = _load(args)
    _banner(proj, args)
    engine = Engine(proj, _ctx(args), workers=args.workers,
                    on_change=lambda snap: db.save(proj.name, snap))
    snap = engine.run()
    t = snap["totals"]
    print(f"→ jobs={t['count']}  {t['by_status']}")
    print(f"  原価: ${t['usd']}  ≒ ¥{t['jpy']:,}  ≒ {t['credits']} クレジット")
    return 0 if not t["by_status"].get("failed") and not t["by_status"].get("blocked") else 1


def cmd_serve(args):
    from .orchestrator.server import serve
    serve(host=args.host, port=args.port)
    return 0


def cmd_submit(args):
    import json as _json
    import urllib.request
    base = f"http://{args.host}:{args.port}"
    body = _json.dumps({"project": args.project, "live": not args.dry_run,
                        "workers": args.workers}).encode()
    req = urllib.request.Request(base + "/projects", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            snap = _json.load(r)
    except Exception as e:  # noqa: BLE001
        sys.exit(f"送信失敗（cm serve は起動中?）: {e}")
    print(f"✓ 投入: {snap['project']}  jobs={snap['totals']['count']}")
    print(f"  進捗: curl -N {base}/projects/{snap['project']}/events")
    print(f"  状態: curl {base}/projects/{snap['project']}")
    return 0


# ---------------------------------------------------------------- parser
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cm", description="AIコマーシャル制作パイプライン (Phase 1a)")
    p.add_argument("--version", action="version", version=f"cm-pipeline {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("project", help="プロジェクト名 or project.yaml へのパス")
        sp.add_argument("--live", dest="dry_run", action="store_false", default=True,
                        help="実際に fal 生成する（課金あり）。既定は DRY-RUN")
        sp.add_argument("--force", action="store_true", help=".done を無視して再生成")
        sp.add_argument("--key", help="fal キーのパス（既定: ../.fal_key）")

    specs = [
        ("validate", cmd_validate, False),
        ("stills", cmd_stills, True),
        ("review", cmd_review, True),
        ("animate", cmd_animate, True),
        ("audio", cmd_audio, True),
        ("build", cmd_build, True),
        ("run", cmd_run, True),
        ("cost", cmd_cost, False),
        ("clean", cmd_clean, False),
    ]
    for name, fn, needs_run_flags in specs:
        sp = sub.add_parser(name, help=fn.__doc__)
        if needs_run_flags:
            common(sp)
        else:
            sp.add_argument("project", help="プロジェクト名 or project.yaml へのパス")
        if name == "review":
            sp.add_argument("--retake", action="store_true",
                            help="NG のスチルを再生成対象に戻す")
        sp.set_defaults(func=fn)

    # orchestrate: DAG をワーカープールで実行（インプロセス）
    sp = sub.add_parser("orchestrate", help=cmd_orchestrate.__doc__)
    common(sp)
    sp.add_argument("--workers", type=int, default=3, help="並列ワーカー数（既定3）")
    sp.set_defaults(func=cmd_orchestrate)

    # serve: HTTP/SSE サーバ
    sp = sub.add_parser("serve", help="Orchestrator を HTTP/SSE で起動")
    sp.add_argument("--host", default="127.0.0.1")
    sp.add_argument("--port", type=int, default=8787)
    sp.set_defaults(func=cmd_serve)

    # submit: 起動中サーバへ投入
    sp = sub.add_parser("submit", help="起動中の cm serve へプロジェクトを投入")
    sp.add_argument("project")
    sp.add_argument("--host", default="127.0.0.1")
    sp.add_argument("--port", type=int, default=8787)
    sp.add_argument("--workers", type=int, default=3)
    sp.add_argument("--live", dest="dry_run", action="store_false", default=True,
                    help="実生成（既定は DRY-RUN）")
    sp.set_defaults(func=cmd_submit)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
