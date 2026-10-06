#!/usr/bin/env python3
"""台本生成ステージ（P4）— projects.spec の cuts（役割だけ）に、ナレーション・文字・必要な素材・秒数を割り当てる。

- AI の台本: ブランドプロフィール（brands.profile）と選択（配信先・目的・相手・伝え方・トーン）から Claude が書く。
  Anthropic SDK と ANTHROPIC_API_KEY が無いときは、テンプレート台本（決定的）で代替する＝フローは常に通る。
- 持ち込み台本（spec.script.source == 'user'）: 文章は変えない。カット割り・秒数・文字・必要な素材だけ付ける。
- 読み方辞書（profile.voice.terms）: ナレーションの TTS 用テキスト（narration_tts）に読みを適用。表示文は変えない。
- 使わない表現（profile.voice.avoid）: AI 台本には禁止語として渡し、出力に残っていれば警告を detail に残す。

戻り値（patch）は projects.spec にマージする:
  cuts[i] += {narration, caption, subject?, secs, assets_required}
  script   += {source: 'ai'|'user'|'template', narration: [{id, text, tts}], pronunciation: [...], model, generated_at}

CLI: python3 script_gen.py --demo   # テンプレート台本をオフラインで表示（キー不要）
"""
from __future__ import annotations

import json
import os
import re
import sys
import time

DEFAULT_MODEL = os.environ.get("SPOT_SCRIPT_MODEL", "claude-opus-5-5")

# 役割ごとの見出し・尺の重み・映像の型（type は spec.cuts の値を優先）
ROLE = {
    "hook":     {"label": "オープニング",   "w": 1.0, "need": "none"},
    "problem":  {"label": "お悩みを見せる", "w": 1.3, "need": "none"},
    "demo":     {"label": "使い方（画面）", "w": 1.4, "need": "ui"},
    "howto":    {"label": "使い方",         "w": 1.4, "need": "ui"},
    "proof":    {"label": "実績・数字",     "w": 1.0, "need": "none"},
    "adoption": {"label": "導入シーン",     "w": 1.2, "need": "none"},
    "result":   {"label": "ビフォーアフター", "w": 1.0, "need": "none"},
    "scene":    {"label": "情景",           "w": 1.1, "need": "none"},
    "tension":  {"label": "葛藤",           "w": 1.2, "need": "none"},
    "turn":     {"label": "転機",           "w": 1.2, "need": "none"},
    "cta":      {"label": "締め・ご案内",   "w": 0.8, "need": "logo"},
}


def _sel(spec: dict) -> dict:
    return spec.get("selections") or {}


def total_seconds(spec: dict) -> int:
    out = spec.get("output") or {}
    if out.get("duration_frames"):
        return max(6, round(int(out["duration_frames"]) / 30))
    media = _sel(spec).get("media") or []
    if media and all(m in ("リール/ショート",) for m in media):
        return 15
    return 30


def plan_cuts(spec: dict) -> list[dict]:
    """cuts に秒数を配分（役割の重みで按分、合計 = total_seconds）。"""
    cuts = [c if isinstance(c, dict) else {"id": c, "type": "live-action"} for c in (spec.get("cuts") or [])]
    if not cuts:
        cuts = [{"id": "cut1", "role": "hook", "type": "live-action"}, {"id": "cut2", "role": "problem", "type": "live-action"},
                {"id": "cut3", "role": "demo", "type": "ui"}, {"id": "cut4", "role": "cta", "type": "cta"}]
    total = total_seconds(spec)
    ws = [ROLE.get(c.get("role") or "", {}).get("w", 1.0) for c in cuts]
    secs = [max(2, round(total * w / sum(ws))) for w in ws]
    secs[-1] += total - sum(secs)                      # 端数は最後のカットで調整
    out = []
    for c, s in zip(cuts, secs):
        d = dict(c)
        d["secs"] = max(2, s)
        d.setdefault("type", "live-action")
        out.append(d)
    return out


def assets_required(cut: dict) -> str:
    t = cut.get("type")
    if t == "ui":
        return "ui"       # アプリの画面写真（必須）
    if t == "cta":
        return "logo"     # ロゴ（ブランドから自動）
    return "none"


def caption_from(narration: str, limit: int = 18) -> str:
    """ナレーションから文字（字幕）を作る：最初の文・句読点で切って ≤ limit 文字。"""
    s = re.split(r"[。！!？?\n]", narration.strip())[0].strip() if narration else ""
    s = re.split(r"[、,]", s)[0].strip() if len(s) > limit else s
    return s[:limit]


def apply_readings(text: str, terms: list[dict]) -> str:
    """読み方辞書（表記→読み）を TTS 用テキストに適用。表示文は変えない。長い表記から順に置換。"""
    for t in sorted(terms or [], key=lambda x: -len(x.get("text") or "")):
        a, b = (t.get("text") or "").strip(), (t.get("reading") or "").strip()
        if a and b:
            text = text.replace(a, b)
    return text


# ------------------------------------------------------------------ テンプレート（AI 不在時のフォールバック）
def template_script(spec: dict, profile: dict, cuts: list[dict]) -> list[dict]:
    sm = profile.get("summary") or {}
    name = (spec.get("meta") or {}).get("product") or profile.get("name") or "このサービス"
    one = sm.get("one_liner") or f"{_sel(spec).get('industry') or 'あなたの仕事'}をラクにするサービス"
    who = sm.get("audience") or (_sel(spec).get("targets") or [_sel(spec).get("target") or "担当者"])[0]
    vals = sm.get("values") or ["手間が減る", "すぐ使える", "その場で完了"]
    polite = (profile.get("voice") or {}).get("register") != "casual"
    goal = (_sel(spec).get("goals") or [None])[0] or "問い合わせ"
    end = "。" if polite else "！"
    lines = {
        "hook":     (f"{who}の毎日、まだ手作業{'ですか？' if polite else '？'}", "まだ手作業？"),
        "problem":  (f"時間も手間もかかる作業が、積み重なって{'いきます' if polite else 'いく'}{end}", "積み重なる手間"),
        "demo":     (f"{name}なら、{one}{end}", f"{vals[0]}"),
        "howto":    (f"使い方はかんたん{end}{vals[0]}{end}", f"{vals[0]}"),
        "proof":    (f"多くの{who}に選ばれて{'います' if polite else 'る'}{end}", "選ばれています"),
        "adoption": (f"導入したその日から、{vals[0]}{end}", f"{vals[0]}"),
        "result":   (f"{vals[1] if len(vals) > 1 else vals[0]}{end}", f"{vals[1] if len(vals) > 1 else vals[0]}"),
        "scene":    (f"いつもの現場、いつもの一日{end}", "いつもの一日"),
        "tension":  (f"でも、ひとつだけ面倒なことが{'あります' if polite else 'ある'}{end}", "面倒なこと"),
        "turn":     (f"{name}で、それが変わ{'ります' if polite else 'る'}{end}", "それが変わる"),
        "cta":      (f"{name}。まずは{'お気軽にお問い合わせください' if '問い合わせ' in goal else '無料で試してみてください' if polite else '試してみて'}{end}", f"{name}"),
    }
    out = []
    for c in cuts:
        na, cap = lines.get(c.get("role") or "", (f"{name}{end}", f"{name}"))
        d = dict(c)
        d["narration"] = na
        d["caption"] = cap
        if d.get("type") == "live-action":
            d["subject"] = f"{who}。{ROLE.get(c.get('role') or '', {}).get('label', '')}の場面"
        out.append(d)
    return out


# ------------------------------------------------------------------ Claude（Anthropic SDK）
SCHEMA = {
    "type": "object",
    "properties": {
        "cuts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "narration": {"type": "string"},
                    "caption": {"type": "string"},
                    "subject": {"type": "string"},
                },
                "required": ["id", "narration", "caption", "subject"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["cuts"],
    "additionalProperties": False,
}

SYSTEM = (
    "あなたは B2B 向け動画広告（15〜30 秒）の放送作家です。日本語で、指定されたカット構成に沿ってナレーションと画面の文字を書きます。"
    "ルール: ナレーションは 1 カットあたり秒数×5 文字以内（例: 6 秒なら 30 文字以内）。最初のカットは 2 秒で『見る人の困りごと』に触れる。"
    "文字（caption）は 18 文字以内の体言止めかひとこと。専門用語・誇張・比較広告・断定的な効果保証（No.1、最安、必ず）は使わない。"
    "『使わない表現』は絶対に使わない。ブランドの言葉づかい（ていねい／くだけた）に合わせる。"
    "subject は実写カットの映像の説明（誰が・どこで・何をしている）を 40 文字以内の日本語で。アプリ画面カットは『提供されたアプリ画面』、CTA は『ロゴと問い合わせ先』と書く。"
    "出力は JSON のみ。"
)


def brief(spec: dict, profile: dict, cuts: list[dict]) -> str:
    sel = _sel(spec)
    sm, vo = profile.get("summary") or {}, profile.get("voice") or {}
    lines = [
        f"サービス名: {(spec.get('meta') or {}).get('product') or profile.get('name') or '（不明）'}",
        f"ひとこと説明: {sm.get('one_liner') or '（不明）'}",
        f"誰向けか: {sm.get('audience') or '（不明）'}",
        f"伝えたいこと: {'、'.join(sm.get('values') or []) or '（指定なし）'}",
        f"言葉づかい: {'くだけた' if vo.get('register') == 'casual' else 'ていねい'}",
        f"使わない表現: {'、'.join(vo.get('avoid') or []) or '（なし）'}",
    ]
    for c in profile.get("custom") or []:
        if c.get("label") or c.get("value"):
            lines.append(f"{c.get('label') or '補足'}: {c.get('value') or ''}")
    lines += [
        f"配信先: {'、'.join(sel.get('media') or [])}",
        f"目的: {'、'.join(sel.get('goals') or [])}",
        f"届ける相手: {'、'.join(sel.get('targets') or ([sel.get('target')] if sel.get('target') else []))}（筆頭の相手に冒頭を合わせる）",
        f"業種: {sel.get('industry') or ''} / 伝え方: {sel.get('angle') or ''} / トーン: {sel.get('tone') or ''}",
        f"合計: {total_seconds(spec)} 秒",
        "カット構成（この順番・id を変えない）:",
    ]
    for i, c in enumerate(cuts, 1):
        r = ROLE.get(c.get("role") or "", {})
        lines.append(f"  {i}. id={c['id']} 役割={r.get('label', c.get('role'))} 種類={c.get('type')} 秒数={c['secs']}")
    return "\n".join(lines)


def llm_script(spec: dict, profile: dict, cuts: list[dict], model: str = DEFAULT_MODEL) -> tuple[list[dict], dict]:
    """Claude に台本を書かせる。失敗は例外（呼び出し側でテンプレートへフォールバック）。"""
    import anthropic  # 遅延 import（未インストール環境でもテンプレート経路は動く）

    client = anthropic.Anthropic()
    prompt = brief(spec, profile, cuts) + "\n\n各カットの narration / caption / subject を JSON で返してください。"
    try:
        res = client.beta.messages.create(
            model=model, max_tokens=4096,
            betas=["server-side-fallback-2026-07-01"], fallbacks="default",   # 安全側の拒否時はサーバ側でフォールバック
            system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
        )
    except TypeError:   # 古い SDK（fallbacks 未対応）
        res = client.messages.create(
            model=model, max_tokens=4096, system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
        )
    if getattr(res, "stop_reason", None) == "refusal":
        raise RuntimeError("script: model refused")
    text = next(b.text for b in res.content if b.type == "text")
    data = json.loads(text)
    by_id = {c.get("id"): c for c in data.get("cuts") or []}
    out = []
    for c in cuts:
        g = by_id.get(c["id"]) or {}
        d = dict(c)
        d["narration"] = (g.get("narration") or "").strip()
        d["caption"] = (g.get("caption") or "").strip()[:18] or caption_from(d["narration"])
        if d.get("type") == "live-action" and g.get("subject"):
            d["subject"] = g["subject"].strip()[:60]
        out.append(d)
    usage = getattr(res, "usage", None)
    meta = {"model": getattr(res, "model", model),
            "input_tokens": getattr(usage, "input_tokens", None), "output_tokens": getattr(usage, "output_tokens", None)}
    return out, meta


# ------------------------------------------------------------------ 仕上げ・入口
def finalize(cuts: list[dict], profile: dict) -> tuple[list[dict], list[dict], list[str]]:
    terms = (profile.get("voice") or {}).get("terms") or []
    avoid = [a for a in ((profile.get("voice") or {}).get("avoid") or []) if a]
    narration, warnings = [], []
    for i, c in enumerate(cuts, 1):
        c["assets_required"] = assets_required(c)
        if c.get("narration"):
            if not c.get("caption"):
                c["caption"] = caption_from(c["narration"])
            nid = f"na{i}"
            c["narration_id"] = nid
            c["narration_tts"] = apply_readings(c["narration"], terms)
            narration.append({"id": nid, "text": c["narration"], "tts": c["narration_tts"]})
            for a in avoid:
                if a in c["narration"] or a in (c.get("caption") or ""):
                    warnings.append(f"カット{i}: 使わない表現「{a}」が含まれています")
    return cuts, narration, warnings


def run(spec: dict, profile: dict | None, live: bool) -> tuple[dict, dict]:
    """台本ステージ本体。(spec に対するパッチ, detail) を返す。"""
    profile = profile or {}
    script = dict(spec.get("script") or {})
    cuts = plan_cuts(spec)
    detail: dict = {}
    source = "user" if script.get("source") == "user" else None
    if source == "user":
        # 持ち込み: 文章は変えない。narration が空のカットだけテンプレートで埋める
        filled = template_script(spec, profile, cuts)
        for c, f in zip(cuts, filled):
            if not c.get("narration"):
                c["narration"] = f["narration"]
            if c.get("type") == "live-action" and not c.get("subject"):
                c["subject"] = f.get("subject")
        detail["note"] = "持ち込み台本をそのまま使用"
    else:
        used_llm = False
        if live and os.environ.get("ANTHROPIC_API_KEY"):
            try:
                cuts, meta = llm_script(spec, profile, cuts)
                detail.update(meta); used_llm = True; source = "ai"
            except Exception as e:  # noqa: BLE001
                detail["llm_error"] = repr(e)[:200]
        if not used_llm:
            cuts = template_script(spec, profile, cuts)
            source = "template"
            if live and not os.environ.get("ANTHROPIC_API_KEY"):
                detail["note"] = "ANTHROPIC_API_KEY 未設定のためテンプレート台本"
    cuts, narration, warnings = finalize(cuts, profile)
    if warnings:
        detail["warnings"] = warnings
    script.update({"source": source, "narration": narration,
                   "pronunciation": [t for t in ((profile.get("voice") or {}).get("terms") or []) if t.get("text")],
                   "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    if detail.get("model"):
        script["model"] = detail["model"]
    return {"cuts": cuts, "script": script}, detail


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo_spec = {"meta": {"product": "ミライ工事写真"}, "selections": {"media": ["YouTube", "リール/ショート"], "goals": ["問い合わせを増やしたい"],
                     "targets": ["実務担当者"], "industry": "SaaS・アプリ", "angle": "課題解決", "tone": "ドキュメンタリー"},
                     "cuts": [{"id": "cut1", "role": "hook", "type": "live-action"}, {"id": "cut2", "role": "problem", "type": "live-action"},
                              {"id": "cut3", "role": "demo", "type": "ui"}, {"id": "cut4", "role": "cta", "type": "cta"}]}
        demo_profile = {"summary": {"one_liner": "現場で写真を撮るだけで、工事台帳が自動でできるアプリ", "audience": "建設会社の現場監督", "values": ["持ち帰りゼロ", "台帳が自動", "その場でPDF"]},
                        "voice": {"register": "polite", "terms": [{"text": "ミライ工事", "reading": "ミライこうじ"}], "avoid": ["業界最安"]}}
        patch, detail = run(demo_spec, demo_profile, live="--live" in sys.argv)
        print(json.dumps(patch, ensure_ascii=False, indent=2)); print("detail:", json.dumps(detail, ensure_ascii=False))
    else:
        print(__doc__)
