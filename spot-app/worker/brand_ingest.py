#!/usr/bin/env python3
"""ブランド取り込み（P3）— brand_sources（URL / 自由記述 / ファイル）を読み、brands.profile を更新する。設計 = docs/brand-intake.md §4。

流れ（ブランド単位）:
  fetch     URL を取得（15 秒・2 MB・robots.txt 尊重）／ファイルを Storage からダウンロード
  extract   HTML: title / description / og / 見出し / 本文、ロゴ候補、色候補、画面候補。PDF: 本文（pypdf）。PPTX: スライド本文。画像: 画面候補
  summarize 抽出結果 → Claude（Anthropic SDK）でプロフィール（§3.1 のスキーマ）。キー無し／失敗時はヒューリスティック
  merge     既存 profile と合成。ユーザーが確認済み（confirmed_at）の項目は上書きしない。候補（色・ロゴ・画面）は補充

原文（HTML / PDF 全文）は保存しない。brand_sources.extracted には要約・構造化結果・画像 URL のみ。

環境変数: ANTHROPIC_API_KEY（任意）、SPOT_SCRIPT_MODEL（既定 claude-opus-5-5）
CLI: python3 brand_ingest.py --demo-url <url>   # 取得〜抽出〜ヒューリスティック要約をオフライン表示（Supabase 不要）
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import zipfile
from html.parser import HTMLParser
from pathlib import Path

DEFAULT_MODEL = os.environ.get("SPOT_SCRIPT_MODEL", "claude-opus-5-5")
UA = "SpotBrandBot/1.0 (+brand registration; reads public pages the brand owner submitted)"
MAX_BYTES = 2 * 1024 * 1024
TIMEOUT = 15

INDUSTRIES = ["SaaS・アプリ", "EC・D2C", "不動産", "採用", "飲食"]
TARGETS = ["実務担当者", "経営層", "一般消費者", "Z世代", "情報システム・IT担当", "マーケティング・営業担当", "人事・採用担当", "既存のお客さま"]
TONES = ["ドキュメンタリー", "明るいCM", "エモーショナル", "スタイリッシュ"]


class Fail(Exception):
    """ユーザー向けの平易な失敗理由。"""


# ------------------------------------------------------------------ fetch
def _get(url: str, limit: int = MAX_BYTES, timeout: int = TIMEOUT) -> tuple[bytes, str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/pdf,image/*,*/*;q=0.8", "Accept-Language": "ja,en;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            data = r.read(limit + 1)
            if len(data) > limit:
                raise Fail("ページが大きすぎて読み切れませんでした（2 MB まで）")
            return data, ctype, r.geturl()
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            raise Fail("このページは読み取りを拒否しています（ログインが必要か、外部からの取得を禁止しています）") from e
        if e.code == 404:
            raise Fail("ページが見つかりませんでした（URL をご確認ください）") from e
        raise Fail(f"ページを取得できませんでした（HTTP {e.code}）") from e
    except urllib.error.URLError as e:
        raise Fail("ページに接続できませんでした（URL をご確認ください）") from e
    except TimeoutError as e:  # noqa: F841
        raise Fail("ページの応答が遅く、読み取りを中断しました") from None


def robots_allowed(url: str) -> bool:
    """robots.txt を自前の UA で取得して判定（RobotFileParser.read は Python 既定 UA で取りに行き、
    bot 対策で 403 を返すサイトを「全面禁止」と誤判定する）。RFC 9309 に倣い 4xx＝robots 無し＝許可、取得不能も許可。"""
    try:
        p = urllib.parse.urlsplit(url)
        req = urllib.request.Request(f"{p.scheme}://{p.netloc}/robots.txt", headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=8) as r:
                body = r.read(64 * 1024).decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            return True   # 4xx＝robots 無し、5xx＝判定不能 → いずれも許可
        rp = urllib.robotparser.RobotFileParser()
        rp.parse(body.splitlines())
        return rp.can_fetch(UA, url)
    except Exception:  # noqa: BLE001  robots が無い／読めない → 許可扱い
        return True


def fetch_url(url: str) -> dict:
    if not re.match(r"^https?://", url or ""):
        raise Fail("https:// から始まる URL を入れてください")
    if not robots_allowed(url):
        raise Fail("このサイトは自動取得を禁止しています（robots.txt）。内容を「自由に書く」に貼り付けてください")
    data, ctype, final = _get(url)
    if "pdf" in ctype or final.lower().endswith(".pdf"):
        return {"kind": "pdf", "data": data, "url": final}
    if ctype.startswith("image/"):
        return {"kind": "image", "data": data, "url": final}
    text = data.decode("utf-8", errors="replace")
    if "text/html" not in ctype and "<html" not in text[:2000].lower():
        raise Fail("読み取れる Web ページではありませんでした（HTML / PDF / 画像のみ）")
    return {"kind": "html", "text": text, "url": final}


# ------------------------------------------------------------------ extract: HTML
class _HTML(HTMLParser):
    SKIP = {"script", "style", "noscript", "svg", "template", "iframe"}

    def __init__(self, base: str):
        super().__init__(convert_charrefs=True)
        self.base = base
        self.title = ""; self.meta = {}; self.heads = []; self.text = []; self.links = []; self.imgs = []; self.styles = []
        self._skip = 0; self._in_title = False; self._head = None; self._in_style = False; self._in_header = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in self.SKIP:
            self._skip += 1
            if tag == "style":
                self._in_style = True
            return
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            k = (a.get("property") or a.get("name") or "").lower(); v = a.get("content") or ""
            if k and v:
                self.meta[k] = v
        elif tag == "link":
            rel = (a.get("rel") or "").lower(); href = a.get("href")
            if href:
                self.links.append({"rel": rel, "href": urllib.parse.urljoin(self.base, href), "type": a.get("type") or ""})
        elif tag in ("h1", "h2", "h3"):
            self._head = tag
        elif tag == "header":
            self._in_header += 1
        elif tag == "img":
            src = a.get("src") or (a.get("srcset") or "").split(",")[0].split()[0] if (a.get("src") or a.get("srcset")) else None
            if src and not src.startswith("data:"):
                try:
                    w = int(re.sub(r"\D", "", a.get("width") or "0") or 0)
                except ValueError:
                    w = 0
                self.imgs.append({"src": urllib.parse.urljoin(self.base, src), "alt": a.get("alt") or "", "w": w,
                                  "cls": (a.get("class") or "").lower(), "header": self._in_header > 0})
        if a.get("style"):
            self.styles.append(a["style"])

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self._skip = max(0, self._skip - 1)
            if tag == "style":
                self._in_style = False
            return
        if tag == "title":
            self._in_title = False
        elif tag in ("h1", "h2", "h3"):
            self._head = None
        elif tag == "header":
            self._in_header = max(0, self._in_header - 1)

    def handle_data(self, data):
        if self._in_style:
            self.styles.append(data); return
        if self._skip:
            return
        t = re.sub(r"\s+", " ", data).strip()
        if not t:
            return
        if self._in_title:
            self.title += t
        elif self._head:
            self.heads.append(t)
        else:
            self.text.append(t)


HEX = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")


def _norm_hex(h: str) -> str:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return "#" + h.upper()


def _is_neutral(h: str) -> bool:
    r, g, b = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
    mx, mn = max(r, g, b), min(r, g, b)
    return (mx - mn) < 18 and (mx > 235 or mx < 30)   # ほぼ白／ほぼ黒


def color_candidates(css_texts: list[str], limit: int = 4) -> list[str]:
    cnt: dict[str, int] = {}
    for t in css_texts:
        for m in HEX.finditer(t):
            h = _norm_hex(m.group(0))
            if _is_neutral(h):
                continue
            cnt[h] = cnt.get(h, 0) + 1
    return [h for h, _ in sorted(cnt.items(), key=lambda kv: -kv[1])[:limit]]


def extract_html(text: str, url: str, fetch_css: bool = True) -> dict:
    p = _HTML(url); p.feed(text)
    css = list(p.styles)
    if fetch_css:
        for ln in [l for l in p.links if "stylesheet" in l["rel"]][:3]:
            try:
                d, _, _ = _get(ln["href"], limit=512 * 1024, timeout=10); css.append(d.decode("utf-8", errors="replace"))
            except Exception:  # noqa: BLE001
                pass
    logos = []
    og = p.meta.get("og:image")
    if og:
        logos.append({"url": urllib.parse.urljoin(url, og), "why": "og:image"})
    for ln in p.links:
        if "icon" in ln["rel"]:
            logos.append({"url": ln["href"], "why": "icon"})
    for im in p.imgs:
        if im["header"] or "logo" in im["cls"] or "logo" in im["alt"].lower() or "logo" in im["src"].lower():
            logos.append({"url": im["src"], "why": "header/logo"})
    seen = set(); logos = [l for l in logos if not (l["url"] in seen or seen.add(l["url"]))][:6]
    screens = [{"url": im["src"], "caption": (im["alt"] or "")[:40]} for im in p.imgs
               if (im["w"] >= 600 or re.search(r"(screen|shot|ui|app|dashboard|画面)", (im["src"] + im["alt"] + im["cls"]).lower())) and not im["header"]][:8]
    body = " ".join(p.text)
    return {
        "title": p.title[:120], "description": (p.meta.get("description") or p.meta.get("og:description") or "")[:300],
        "site_name": p.meta.get("og:site_name") or "", "headings": p.heads[:20], "body": body[:6000],
        "logos": logos, "colors": color_candidates(css), "screens": screens, "lang": "ja" if re.search(r"[ぁ-んァ-ン一-龥]", body[:2000]) else "en",
    }


# ------------------------------------------------------------------ extract: PDF / PPTX / text
def extract_pdf(data: bytes) -> dict:
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise Fail("PDF を読む部品（pypdf）が入っていません") from e
    try:
        r = PdfReader(io.BytesIO(data))
        pages = [(pg.extract_text() or "") for pg in r.pages[:30]]
    except Exception as e:  # noqa: BLE001
        raise Fail("PDF を読み取れませんでした（画像だけの PDF は文字を取り出せません）") from e
    body = re.sub(r"\s+", " ", " ".join(pages)).strip()
    if not body:
        raise Fail("PDF から文字を取り出せませんでした（画像だけの PDF かもしれません）")
    return {"title": "", "description": "", "headings": [], "body": body[:8000], "logos": [], "colors": [], "screens": [], "pages": len(r.pages)}


def extract_pptx(data: bytes) -> dict:
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as e:
        raise Fail("PPTX を開けませんでした") from e
    slides = sorted([n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)], key=lambda n: int(re.findall(r"\d+", n)[0]))
    texts = []
    for n in slides[:40]:
        xml = z.read(n).decode("utf-8", errors="replace")
        texts.append(" ".join(re.findall(r"<a:t>([^<]*)</a:t>", xml)))
    body = re.sub(r"\s+", " ", " ".join(texts)).strip()
    if not body:
        raise Fail("スライドから文字を取り出せませんでした")
    return {"title": texts[0][:80] if texts else "", "description": "", "headings": [t[:60] for t in texts[:10]], "body": body[:8000], "logos": [], "colors": [], "screens": [], "pages": len(slides)}


def extract_text(text: str) -> dict:
    body = re.sub(r"\s+", " ", text or "").strip()
    return {"title": "", "description": "", "headings": [], "body": body[:6000], "logos": [], "colors": [], "screens": []}


# ------------------------------------------------------------------ summarize
SCHEMA = {
    "type": "object",
    "properties": {
        "one_liner": {"type": "string"}, "audience": {"type": "string"},
        "values": {"type": "array", "items": {"type": "string"}},
        "register": {"type": "string", "enum": ["polite", "casual"]},
        "terms": {"type": "array", "items": {"type": "object", "properties": {"text": {"type": "string"}, "reading": {"type": "string"}}, "required": ["text", "reading"], "additionalProperties": False}},
        "avoid": {"type": "array", "items": {"type": "string"}},
        "industry": {"type": "string", "enum": INDUSTRIES}, "target": {"type": "string", "enum": TARGETS}, "tone": {"type": "string", "enum": TONES},
        "imagery": {"type": "string", "enum": ["photo", "illustration", "ui", "mixed"]},
        "confidence": {"type": "object", "properties": {k: {"type": "string", "enum": ["high", "low"]} for k in ["one_liner", "audience", "values", "register", "industry", "target", "tone"]},
                       "required": ["one_liner", "audience", "values", "register", "industry", "target", "tone"], "additionalProperties": False},
    },
    "required": ["one_liner", "audience", "values", "register", "terms", "avoid", "industry", "target", "tone", "imagery", "confidence"],
    "additionalProperties": False,
}
SYSTEM = (
    "あなたはブランドの資料を読んで、動画広告づくりに必要な『ブランドの理解』を日本語で簡潔にまとめる担当です。"
    "推測で埋めない。資料に根拠が無い項目は空文字や空配列にし、confidence を low にする。"
    "one_liner は 40 文字以内で『何をするサービスか』。audience は『誰向けか』を 30 文字以内。values は顧客にとっての価値を 3 つまで、各 12 文字以内。"
    "register は文章の敬体/常体から判定。terms は固有名詞の読み方（カタカナ）で、資料から確実に分かるものだけ。avoid は資料が避けている/避けるべき表現。"
    "industry / target / tone は与えられた選択肢から最も近いものを 1 つ。imagery は資料の見た目（写真中心/イラスト/画面中心/混在）。出力は JSON のみ。"
)


def llm_profile(brand_name: str, docs: list[dict], model: str = DEFAULT_MODEL) -> tuple[dict, dict]:
    import anthropic  # 遅延 import

    parts = [f"ブランド名: {brand_name}"]
    for i, d in enumerate(docs, 1):
        parts.append(f"--- 資料 {i}（{d.get('kind')}: {d.get('label', '')}）\nタイトル: {d.get('title', '')}\n説明: {d.get('description', '')}\n見出し: {' / '.join(d.get('headings') or [])}\n本文: {(d.get('body') or '')[:3500]}")
    prompt = "\n".join(parts) + "\n\n上の資料だけを根拠に、JSON で返してください。"
    client = anthropic.Anthropic()
    try:
        res = client.beta.messages.create(model=model, max_tokens=4096, betas=["server-side-fallback-2026-07-01"], fallbacks="default",
                                          system=SYSTEM, messages=[{"role": "user", "content": prompt}],
                                          output_config={"format": {"type": "json_schema", "schema": SCHEMA}})
    except TypeError:
        res = client.messages.create(model=model, max_tokens=4096, system=SYSTEM, messages=[{"role": "user", "content": prompt}],
                                     output_config={"format": {"type": "json_schema", "schema": SCHEMA}})
    if getattr(res, "stop_reason", None) == "refusal":
        raise RuntimeError("profile: model refused")
    data = json.loads(next(b.text for b in res.content if b.type == "text"))
    usage = getattr(res, "usage", None)
    return data, {"model": getattr(res, "model", model), "input_tokens": getattr(usage, "input_tokens", None), "output_tokens": getattr(usage, "output_tokens", None)}


def heuristic_profile(brand_name: str, docs: list[dict]) -> dict:
    """キー無し／失敗時: 資料の表層から最低限のプロフィール（すべて low）。"""
    first = docs[0] if docs else {}
    one = (first.get("description") or first.get("title") or "")[:40]
    body = " ".join((d.get("body") or "") for d in docs)
    polite = len(re.findall(r"(です|ます)[。！!]", body)) >= len(re.findall(r"(だ|である)[。！!]", body))
    heads = [h for d in docs for h in (d.get("headings") or [])]
    values = [h[:12] for h in heads if 3 <= len(h) <= 14][:3]
    return {"one_liner": one, "audience": "", "values": values, "register": "polite" if polite else "casual", "terms": [], "avoid": [],
            "industry": "", "target": "", "tone": "", "imagery": "ui" if any(d.get("screens") for d in docs) else "photo",
            "confidence": {k: "low" for k in ["one_liner", "audience", "values", "register", "industry", "target", "tone"]}}


# ------------------------------------------------------------------ merge
def merge_profile(existing: dict, got: dict, docs: list[dict], source_ids: list[str]) -> dict:
    """抽出結果を既存 profile に合成。confirmed_at 済みの項目（ユーザー確認済み）は上書きしない。"""
    pf = json.loads(json.dumps(existing or {}))
    pf.setdefault("version", 1)
    confirmed = bool(pf.get("confirmed_at"))
    sm = pf.setdefault("summary", {}); vi = pf.setdefault("visual", {}); vo = pf.setdefault("voice", {}); df = pf.setdefault("defaults", {}); cf = pf.setdefault("confidence", {})
    conf = got.get("confidence") or {}

    def put(d: dict, key: str, val, ckey: str):
        if val in (None, "", [], {}):
            return
        if confirmed and d.get(key) not in (None, "", []):
            return      # ユーザー確認済みの値を守る
        d[key] = val
        cf[ckey] = conf.get(ckey.split(".")[-1], "low")

    put(sm, "one_liner", got.get("one_liner"), "summary.one_liner")
    put(sm, "audience", got.get("audience"), "summary.audience")
    put(sm, "values", [v for v in (got.get("values") or []) if v][:3], "summary.values")
    put(vo, "register", got.get("register"), "voice.register")
    if got.get("terms"):
        cur = {t.get("text") for t in (vo.get("terms") or [])}
        vo["terms"] = (vo.get("terms") or []) + [t for t in got["terms"] if t.get("text") and t["text"] not in cur]
    if got.get("avoid"):
        vo["avoid"] = list(dict.fromkeys((vo.get("avoid") or []) + [a for a in got["avoid"] if a]))
    put(df, "industry", got.get("industry"), "defaults.industry")
    put(df, "target", got.get("target"), "defaults.target")
    put(df, "tone", got.get("tone"), "defaults.tone")
    if got.get("imagery") and not vi.get("imagery"):
        vi["imagery"] = got["imagery"]
    colors = [c for d in docs for c in (d.get("colors") or [])]
    if colors and not vi.get("colors"):
        vi["colors"] = list(dict.fromkeys(colors))[:4]; cf["visual.colors"] = "low"
    logos = [l for d in docs for l in (d.get("logos") or [])]
    if logos:
        vi["logo_candidates"] = list({l["url"]: l for l in logos}.values())[:6]
    screens = [s for d in docs for s in (d.get("screens") or [])]
    if screens:
        cur = {s.get("url") for s in (pf.get("screens") or [])}
        pf["screens"] = (pf.get("screens") or []) + [{"url": s["url"], "caption": s.get("caption") or "", "use": False} for s in screens if s["url"] not in cur][:12]
    pf["learned_from"] = list(dict.fromkeys((pf.get("learned_from") or []) + source_ids))
    pf["learned_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return pf


# ------------------------------------------------------------------ orchestration（Supabase）
def process_brand(sb, brand_id: str, live: bool, log=print) -> int:
    """1 ブランドの pending ソースを読み、profile を更新。処理件数を返す。sb は worker.Supa。"""
    rows = sb.select("brand_sources", brand_id=f"eq.{brand_id}", status="eq.pending")
    if not rows:
        return 0
    br = sb.select("brands", id=f"eq.{brand_id}", select="id,name,org_id,profile,assets")
    if not br:
        return 0
    brand = br[0]
    docs: list[dict] = []; done_ids: list[str] = []; n = 0
    for r in rows:
        n += 1
        sb.update("brand_sources", {"id": f"eq.{r['id']}"}, {"status": "running", "step": "fetch", "error": None})
        try:
            if r["kind"] == "url":
                got = fetch_url(r.get("url") or "")
                sb.update("brand_sources", {"id": f"eq.{r['id']}"}, {"step": "extract"})
                if got["kind"] == "html":
                    ex = extract_html(got["text"], got["url"]); label = got["url"]
                elif got["kind"] == "pdf":
                    ex = extract_pdf(got["data"]); label = got["url"]
                else:
                    ex = {"title": "", "description": "", "headings": [], "body": "", "logos": [], "colors": [], "screens": [{"url": got["url"], "caption": ""}]}; label = got["url"]
            elif r["kind"] == "text":
                ex = extract_text(r.get("text") or ""); label = "自由に書いた説明"
            elif r["kind"] == "file":
                path = r.get("storage_path") or ""
                dest = Path("/tmp/spot-brand") / brand_id / Path(path).name
                sb.download("assets", path, dest)
                sb.update("brand_sources", {"id": f"eq.{r['id']}"}, {"step": "extract"})
                data = dest.read_bytes(); low = (r.get("file_name") or path).lower(); label = r.get("file_name") or Path(path).name
                if low.endswith(".pdf"):
                    ex = extract_pdf(data)
                elif low.endswith(".pptx"):
                    ex = extract_pptx(data)
                elif re.search(r"\.(png|jpe?g|webp)$", low):
                    ex = {"title": "", "description": "", "headings": [], "body": "", "logos": [], "colors": [], "screens": [{"url": path, "caption": label}]}
                else:
                    raise Fail("対応していないファイル形式です（PDF / PPTX / PNG / JPG）")
                try:
                    dest.unlink()
                except OSError:
                    pass
            else:
                raise Fail("不明な取り込み元です")
            ex["kind"] = r["kind"]; ex["label"] = label
            docs.append(ex); done_ids.append(r["id"])
            keep = {k: v for k, v in ex.items() if k in ("title", "description", "headings", "logos", "colors", "screens", "pages", "lang")}
            keep["summary"] = (ex.get("body") or "")[:400]
            sb.update("brand_sources", {"id": f"eq.{r['id']}"}, {"step": "extracted", "extracted": keep})
            log(f"  src   {r['kind']:5} {label[:60]} ok")
        except Fail as e:
            sb.update("brand_sources", {"id": f"eq.{r['id']}"}, {"status": "failed", "step": None, "error": str(e)[:200]})
            log(f"  src   {r['kind']:5} {r.get('url') or r.get('file_name') or ''}: {e}")
        except Exception as e:  # noqa: BLE001
            sb.update("brand_sources", {"id": f"eq.{r['id']}"}, {"status": "failed", "step": None, "error": "読み取り中にエラーが起きました"})
            log(f"  src   {r['kind']:5} error: {e!r}")
    if not docs:
        return n
    # summarize（status は profile 更新まで running のまま＝アプリは全件 done/failed で確認画面へ進む）
    sb.update("brand_sources", {"id": f"in.({','.join(done_ids)})"}, {"step": "summarize"})
    got, meta = None, {}
    if live and os.environ.get("ANTHROPIC_API_KEY"):
        try:
            got, meta = llm_profile(brand.get("name") or "", docs)
        except Exception as e:  # noqa: BLE001
            log(f"  WARN  llm profile failed: {e!r}; heuristic fallback")
    if got is None:
        got = heuristic_profile(brand.get("name") or "", docs)
    pf = merge_profile(brand.get("profile") or {}, got, docs, done_ids)
    if meta.get("model"):
        pf["model"] = meta["model"]
    # ロゴ候補: brands.assets.logo が無ければ最初の候補を Storage に保存して visual.logo に
    try:
        if not (brand.get("assets") or {}).get("logo") and not (pf.get("visual") or {}).get("logo") and pf.get("visual", {}).get("logo_candidates"):
            cand = next((c for c in pf["visual"]["logo_candidates"] if c["why"] != "icon"), pf["visual"]["logo_candidates"][0])
            data, ctype, _ = _get(cand["url"], limit=5 * 1024 * 1024, timeout=10)
            ext = {"image/png": "png", "image/jpeg": "jpg", "image/svg+xml": "svg", "image/webp": "webp"}.get(ctype)
            if ext:
                tmp = Path("/tmp/spot-brand") / brand_id / f"logo.{ext}"; tmp.parent.mkdir(parents=True, exist_ok=True); tmp.write_bytes(data)
                path = f"{brand['org_id']}/brand/{brand_id}/logo.{ext}"
                sb.upload("assets", path, tmp); pf["visual"]["logo"] = path; pf["confidence"]["visual.logo"] = "low"
                log(f"  logo  saved {path}")
    except Exception as e:  # noqa: BLE001
        log(f"  WARN  logo candidate: {e!r}")
    sb.update("brands", {"id": f"eq.{brand_id}"}, {"profile": pf})
    sb.update("brand_sources", {"id": f"in.({','.join(done_ids)})"}, {"status": "done", "step": "done"})
    log(f"  brand {brand_id} profile updated ({'ai' if meta.get('model') else 'heuristic'}, {len(docs)} source(s))")
    return n


def tick_brands(sb, only_brand: str | None, live: bool, log=print) -> int:
    params = {"select": "brand_id", "status": "eq.pending"}
    if only_brand:
        params["brand_id"] = f"eq.{only_brand}"
    pending = sb.select("brand_sources", **params)
    total = 0
    for bid in sorted({p["brand_id"] for p in pending}):
        log(f"brand {bid} …")
        total += process_brand(sb, bid, live, log)
    return total


if __name__ == "__main__":
    if "--demo-url" in sys.argv:
        url = sys.argv[sys.argv.index("--demo-url") + 1]
        got = fetch_url(url)
        ex = extract_html(got["text"], got["url"]) if got["kind"] == "html" else extract_pdf(got["data"])
        print(json.dumps({k: v for k, v in ex.items() if k != "body"}, ensure_ascii=False, indent=2)); print("body:", ex["body"][:300])
        print("heuristic:", json.dumps(heuristic_profile("demo", [ex]), ensure_ascii=False))
    else:
        print(__doc__)
