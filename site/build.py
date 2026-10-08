#!/usr/bin/env python3
"""Spot marketing site — static generator.

    python3 site/build.py            # → site/dist/
    python3 site/build.py --serve    # build, then serve dist/ on :5510

Everything the crawler needs is written into real HTML at build time:
one file per page per language, canonical + hreflang in the <head>,
JSON-LD per page type, per-language sitemaps, robots.txt, llms.txt,
and the social card at /og/spot-cover.png.

Content lives in site/content/*.py as plain dicts (en + ja). No deps.
"""
from __future__ import annotations

import html
import json
import os
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
sys.path.insert(0, str(ROOT))

from content import common, core, usecases, compare, guides  # noqa: E402

SITE = common.SITE
TODAY = date.today().isoformat()


# --------------------------------------------------------------------------- helpers
def esc(s: str) -> str:
    return html.escape(s, quote=True)


def url(lang: str, path: str) -> str:
    """Absolute URL for a page path ('' = home) in a language."""
    path = path.strip("/")
    if lang == "ja":
        return f"{SITE}/ja/{path}/" if path else f"{SITE}/ja/"
    return f"{SITE}/{path}/" if path else f"{SITE}/"


def out_path(lang: str, path: str) -> Path:
    path = path.strip("/")
    base = DIST / "ja" if lang == "ja" else DIST
    return (base / path / "index.html") if path else (base / "index.html")


def jsonld(obj) -> str:
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + "</script>"


def md_inline(s: str) -> str:
    """Tiny inline markup: **bold**, [text](url). Everything else escaped."""
    import re
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[(.+?)\]\((https?://[^\s)]+|/[^\s)]*)\)", r'<a href="\2">\1</a>', s)
    return s


# --------------------------------------------------------------------------- CSS
CSS = """
:root{color-scheme:dark;--ground:#131318;--surface:#1E1E26;--surface-2:#25252F;--ink:#F1EDE4;--muted:#A8A49A;--faint:#8A867C;--line:#2C2C37;--line-strong:#3E3E4B;--blue:#4A67E3;--blue-ink:#AEBCFA;--blue-soft:#1B2350;--good:#6DB98C;--warn:#E4B14C;
--shadow:0 1px 2px rgba(0,0,0,.3),0 12px 32px rgba(0,0,0,.5);--shadow-lift:0 4px 14px rgba(0,0,0,.45),0 30px 60px rgba(0,0,0,.65);
--fd:"Bricolage Grotesque","Hanken Grotesk",system-ui,sans-serif;--fb:"Hanken Grotesk",system-ui,-apple-system,"Zen Kaku Gothic New",sans-serif;--fm:"DM Mono",ui-monospace,monospace;--r:14px}
html[lang=ja]{--fb:"Zen Kaku Gothic New","Hiragino Kaku Gothic ProN",system-ui,sans-serif}
*{box-sizing:border-box}body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--fb);font-size:16px;line-height:1.7;-webkit-font-smoothing:antialiased}
h1,h2,h3{margin:0;font-weight:700;letter-spacing:-.02em;text-wrap:balance}html[lang=ja] h1,html[lang=ja] h2,html[lang=ja] h3{letter-spacing:0}
a{color:inherit;text-decoration:none}p{margin:0}::selection{background:var(--blue-soft)}
a:focus-visible,button:focus-visible{outline:2px solid var(--blue);outline-offset:2px}
.wrap{max-width:1120px;margin:0 auto;padding:0 28px}.narrow{max-width:760px}
.btn{border:none;border-radius:11px;padding:13px 22px;font-family:var(--fb);font-size:15px;font-weight:700;cursor:pointer;transition:.15s;display:inline-flex;align-items:center;gap:8px}
.btn-primary{background:var(--blue);color:#fff}.btn-primary:hover{transform:translateY(-2px);box-shadow:0 12px 28px color-mix(in srgb,var(--blue) 42%,transparent)}
.btn-ghost{background:transparent;border:1px solid var(--line-strong);color:var(--ink)}.btn-ghost:hover{border-color:var(--blue);color:var(--blue-ink)}
.eyebrow{font-family:var(--fm);font-size:12.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--blue-ink)}
nav.top{position:sticky;top:0;z-index:30;background:color-mix(in srgb,var(--ground) 82%,transparent);backdrop-filter:saturate(1.4) blur(10px);border-bottom:1px solid var(--line)}
.nav-in{display:flex;align-items:center;gap:26px;height:66px}.brand{display:flex;align-items:center;gap:11px}.brand .word{font-family:var(--fd);font-weight:800;font-size:22px}.brand .word .o{color:var(--blue)}
.nav-links{display:flex;gap:22px;margin-left:14px}.nav-links a{font-size:14.5px;color:var(--muted);font-weight:500}.nav-links a:hover,.nav-links a[aria-current]{color:var(--ink)}
.nav-right{margin-left:auto;display:flex;align-items:center;gap:12px}
.lang{display:inline-flex;border:1px solid var(--line-strong);border-radius:9px;overflow:hidden;font-family:var(--fm);font-size:12px}.lang a{padding:7px 11px;color:var(--muted)}.lang a[aria-current]{background:var(--ink);color:var(--ground)}
.crumbs{font-family:var(--fm);font-size:12px;color:var(--faint);padding:22px 0 0}.crumbs a{color:var(--muted)}.crumbs span{margin:0 8px}
.hero{padding:76px 0 26px}.hero .eyebrow{display:block;margin-bottom:20px}.hero h1{font-family:var(--fd);font-weight:800;font-size:clamp(44px,7vw,84px);line-height:1.02}html[lang=ja] .hero h1{font-size:clamp(36px,6vw,68px);line-height:1.15}
.hero .sub{font-size:19px;color:var(--muted);max-width:46ch;margin:24px 0 0;line-height:1.6}.hero .cta{display:flex;gap:13px;margin-top:32px;flex-wrap:wrap;align-items:center}.hero .cta .micro{font-size:13px;color:var(--faint);font-family:var(--fm)}
.stage{margin-top:56px;display:flex;gap:20px;align-items:flex-end;justify-content:center;padding:36px 24px;background:var(--surface);border:1px solid var(--line);border-radius:22px;box-shadow:var(--shadow-lift);overflow:hidden;position:relative}
.stage::before{content:"";position:absolute;left:50%;top:-80px;transform:translateX(-50%);width:420px;height:420px;border-radius:50%;background:radial-gradient(circle,var(--blue-soft),transparent 68%);opacity:.9}
.fr{position:relative;background:linear-gradient(160deg,#2f3947,#161b22);border-radius:12px;box-shadow:var(--shadow-lift);color:#fff;overflow:hidden;flex:none}.fr.wide{width:340px;height:191px}.fr.square{width:200px;height:200px}.fr.vert{width:120px;height:213px}
.fr .lbl{position:absolute;top:9px;left:10px;font-family:var(--fm);font-size:9.5px;background:rgba(0,0,0,.35);padding:2px 7px;border-radius:5px;z-index:2}.fr .cap{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;text-align:center;font-weight:800;font-size:15px;padding:0 14px;text-shadow:0 2px 8px rgba(0,0,0,.4)}.fr.square .cap{font-size:13px}.fr.vert .cap{font-size:11px}
.page-head{padding:56px 0 8px}.page-head h1{font-family:var(--fd);font-weight:800;font-size:clamp(34px,5vw,56px);line-height:1.06;margin-top:14px}html[lang=ja] .page-head h1{font-size:clamp(30px,4.4vw,48px);line-height:1.2}
.page-head .lede{font-size:18px;color:var(--muted);max-width:52ch;margin-top:18px;line-height:1.6}.page-head .upd{font-family:var(--fm);font-size:12px;color:var(--faint);margin-top:18px}
section.blk{padding:56px 0 8px}.sec-head h2{font-family:var(--fd);font-size:clamp(26px,3.6vw,38px);font-weight:800;margin-top:12px;line-height:1.12}html[lang=ja] .sec-head h2{font-size:clamp(24px,3vw,32px);line-height:1.25}
.sec-head p{color:var(--muted);font-size:17px;margin-top:14px;line-height:1.6;max-width:60ch}
.qa{margin-top:28px;display:grid;gap:18px}.qa .q{padding:22px 24px;background:var(--surface);border:1px solid var(--line);border-radius:var(--r)}.qa h2,.qa h3{font-size:19px;line-height:1.35}.qa p{color:var(--muted);margin-top:10px;font-size:15.5px;line-height:1.7}.qa p strong{color:var(--ink)}
.answer{margin-top:26px;padding:24px 26px;background:var(--blue-soft);border-left:3px solid var(--blue);border-radius:0 var(--r) var(--r) 0}.answer h2{font-size:20px;line-height:1.35}.answer p{margin-top:10px;font-size:16.5px;line-height:1.7}
.tw{overflow-x:auto;margin-top:22px;border:1px solid var(--line);border-radius:var(--r);background:var(--surface)}table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.5;font-variant-numeric:tabular-nums}
th,td{text-align:left;padding:11px 14px;border-bottom:1px solid var(--line);vertical-align:top}th{font-family:var(--fm);font-weight:500;font-size:11.5px;letter-spacing:.06em;color:var(--muted);background:var(--surface-2);white-space:nowrap}tr:last-child td{border-bottom:none}
td.hl{background:var(--blue-soft);font-weight:700}.cap{font-size:12.5px;color:var(--faint);margin-top:10px;font-family:var(--fm)}
.facts{margin-top:22px;display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}.fact{padding:18px 20px;background:var(--surface);border:1px solid var(--line);border-radius:var(--r)}.fact .n{font-family:var(--fd);font-weight:800;font-size:30px;letter-spacing:-.02em;line-height:1;color:var(--blue-ink)}.fact .k{font-size:13.5px;color:var(--muted);margin-top:8px;line-height:1.5}.fact .s{font-family:var(--fm);font-size:11px;color:var(--faint);margin-top:8px}.fact .s a{color:var(--muted);border-bottom:1px solid var(--line-strong)}
blockquote.pull{margin:28px 0 0;padding:22px 26px;border-left:3px solid var(--blue);background:var(--surface);border-radius:0 var(--r) var(--r) 0;font-size:17px;line-height:1.65}blockquote.pull cite{display:block;margin-top:10px;font-style:normal;font-family:var(--fm);font-size:12px;color:var(--muted)}
.prose{margin-top:22px;font-size:16px;line-height:1.8;max-width:68ch}.prose p+p{margin-top:14px}.prose ul{margin:12px 0 0;padding-left:1.3em}.prose li{margin:6px 0}.prose a{color:var(--blue-ink);border-bottom:1px solid color-mix(in srgb,var(--blue) 40%,transparent)}
.steps,.pillars,.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:38px}.grid2{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-top:28px}
.step,.pillar,.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:26px;box-shadow:var(--shadow)}.step .no{font-family:var(--fm);font-size:12px;color:var(--blue)}.step h3,.pillar h3,.card h3{font-size:19px;margin:14px 0 8px}.step p,.pillar p,.card p{color:var(--muted);font-size:14.5px;line-height:1.6}
.card a.more{display:inline-block;margin-top:12px;color:var(--blue-ink);font-size:14px}.card h3{margin-top:0}
.band{background:var(--ink);color:var(--ground);border-radius:22px;padding:48px;margin:8px 0;display:grid;grid-template-columns:repeat(3,1fr);gap:30px;box-shadow:var(--shadow-lift)}.metric .n{font-family:var(--fd);font-weight:800;font-size:clamp(36px,5vw,54px);letter-spacing:-.03em;line-height:1}.metric .n em{color:#7E97FF;font-style:normal}.metric .k{color:color-mix(in srgb,var(--ground) 62%,transparent);font-size:14px;margin-top:10px}
.plans{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin-top:34px}.plan{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:24px 22px;display:flex;flex-direction:column;gap:8px}.plan.hl{border-color:var(--blue);box-shadow:0 0 0 1px var(--blue) inset}
.plan .nm{font-family:var(--fd);font-weight:800;font-size:20px}.plan .pr{font-family:var(--fd);font-weight:800;font-size:34px;letter-spacing:-.02em;line-height:1;margin-top:4px}.plan .pr small{font-size:14px;color:var(--muted);font-weight:500;letter-spacing:0}.plan .jp{font-family:var(--fm);font-size:12px;color:var(--muted)}
.plan .sp{font-size:15px;margin-top:8px}.plan ul{margin:8px 0 0;padding:0;list-style:none;font-size:13.5px;color:var(--muted);display:grid;gap:5px}.plan ul li::before{content:"— ";color:var(--faint)}.plan .btn{margin-top:auto;justify-content:center;padding:11px 16px;font-size:14px}
.plain{margin-top:18px;padding:18px 22px;background:var(--surface-2);border-radius:var(--r);font-size:15px;line-height:1.75;font-family:var(--fm);color:var(--muted)}.plain b{color:var(--ink);font-weight:500}
.final{text-align:center;padding:84px 0}.final h2{font-family:var(--fd);font-size:clamp(32px,5vw,56px);font-weight:800}html[lang=ja] .final h2{font-size:clamp(28px,4vw,44px)}.final p{color:var(--muted);font-size:18px;margin:16px auto 30px;max-width:44ch}
.related{margin-top:48px;padding-top:28px;border-top:1px solid var(--line)}.related h2{font-size:14px;font-family:var(--fm);font-weight:500;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}.related ul{margin:14px 0 0;padding:0;list-style:none;display:flex;flex-wrap:wrap;gap:10px}.related li a{display:inline-block;padding:8px 14px;border:1px solid var(--line-strong);border-radius:9px;font-size:14px;color:var(--ink)}.related li a:hover{border-color:var(--blue);color:var(--blue-ink)}
footer{border-top:1px solid var(--line);padding:40px 0;color:var(--muted);font-size:13.5px;margin-top:40px}.foot-in{display:grid;grid-template-columns:1.2fr 1fr 1fr 1fr;gap:28px}.foot-in h4{margin:0 0 10px;font-family:var(--fm);font-weight:500;font-size:11.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--faint)}.foot-in ul{list-style:none;margin:0;padding:0;display:grid;gap:7px}.foot-in a:hover{color:var(--ink)}.foot-bottom{margin-top:28px;font-size:12.5px;color:var(--faint);display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px}
.logos{padding:40px 0 10px}.logos .cap{text-align:center;font-family:var(--fm);font-size:12px;color:var(--faint);letter-spacing:.06em;text-transform:uppercase}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
@media (max-width:820px){.steps,.pillars,.band,.grid3,.grid2{grid-template-columns:1fr}.nav-links{display:none}.fr.vert{display:none}.foot-in{grid-template-columns:1fr 1fr}}
/* ---- brush-up: depth, interactivity, hero life, trust ---- */
body{position:relative}
body::before{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;background:radial-gradient(880px 480px at 82% -10%,color-mix(in srgb,var(--blue) 13%,transparent),transparent 62%),radial-gradient(680px 520px at -6% 6%,color-mix(in srgb,var(--blue) 6%,transparent),transparent 55%)}
.step,.pillar,.card,.fact,.plan{transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease}
.step:hover,.pillar:hover,.card:hover,.fact:hover,.plan:hover{transform:translateY(-3px);border-color:var(--line-strong);box-shadow:var(--shadow-lift)}
.fr{background-size:cover;background-position:center}
.fr.vert{background-image:url(/hero/vert.jpg),linear-gradient(155deg,#3a4a5e,#141a24)}.fr.wide{background-image:url(/hero/wide.jpg),linear-gradient(150deg,#27324d,#0f1420)}.fr.square{background-image:url(/hero/square.jpg),linear-gradient(160deg,#4a3f5e,#181423)}
.fr::before{content:"";position:absolute;inset:0;pointer-events:none;background:linear-gradient(180deg,rgba(0,0,0,.12),rgba(0,0,0,.52))}
.fr::after{content:"";position:absolute;inset:0;pointer-events:none;background:linear-gradient(125deg,rgba(255,255,255,.10),transparent 42%)}
.fr .cap{z-index:1}
.fr .play{position:absolute;left:50%;bottom:9px;transform:translateX(-50%);width:30px;height:30px;border-radius:50%;background:rgba(255,255,255,.94);color:var(--blue);display:grid;place-items:center;box-shadow:0 4px 12px rgba(0,0,0,.4);z-index:3}.fr .play svg{width:11px;height:11px;margin-left:1px}
@media (prefers-reduced-motion:no-preference){.fr{animation:spotfloat 6s ease-in-out infinite}.fr.wide{animation-delay:-2s}.fr.square{animation-delay:-4s}@keyframes spotfloat{0%,100%{transform:translateY(0)}50%{transform:translateY(-9px)}}}
.band{position:relative;overflow:hidden}.band::before{content:"";position:absolute;top:0;left:44px;width:120px;height:3px;border-radius:0 0 3px 3px;background:linear-gradient(90deg,var(--blue),transparent)}
.metric+.metric{border-left:1px solid color-mix(in srgb,var(--ground) 24%,transparent);padding-left:30px}
.plan{position:relative}.plan.hl{box-shadow:0 0 0 1px var(--blue) inset,var(--shadow-lift)}.plan .pop{position:absolute;top:-11px;right:16px;background:var(--blue);color:#fff;font-family:var(--fm);font-size:10.5px;letter-spacing:.03em;padding:3px 10px;border-radius:999px;box-shadow:0 4px 10px color-mix(in srgb,var(--blue) 45%,transparent)}
.trust{margin-top:34px;display:flex;align-items:center;gap:22px;flex-wrap:wrap}.trust .cap{font-family:var(--fm);font-size:11.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--faint)}.trust .row{display:flex;gap:26px;flex-wrap:wrap}.trust .row b{font-family:var(--fd);font-weight:700;font-size:16px;color:var(--muted)}
@media (max-width:820px){.metric+.metric{border-left:none;padding-left:0}.band::before{left:28px}}
.theme-btn{border:1px solid var(--line-strong);background:transparent;color:var(--muted);width:34px;height:34px;border-radius:9px;cursor:pointer;font-size:15px;line-height:1;flex:none}.theme-btn:hover{color:var(--ink);border-color:var(--blue)}
html.js .reveal{opacity:.55;transform:translateY(16px)}html.js .reveal.in{opacity:1;transform:none;transition:opacity .5s ease,transform .5s ease}
@media (prefers-reduced-motion:reduce){html.js .reveal{opacity:1!important;transform:none!important}}
"""

FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,700;12..96,800&family=Hanken+Grotesk:wght@400;500;700&family=DM+Mono:wght@400;500&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap">'

LOGO_SVG = '<img src="/spot-mark.png" width="28" height="28" alt="" aria-hidden="true" style="display:block">'


# --------------------------------------------------------------------------- page shell
def head(lang: str, page: dict) -> str:
    t = common.T[lang]
    path = page["path"]
    here = url(lang, path)
    other = url("ja" if lang == "en" else "en", path)
    title = page["title"]
    desc = page["desc"]
    og_title = page.get("og_title", title)
    ld = [common.org_jsonld(lang), common.website_jsonld(lang)]
    ld += page.get("jsonld", [])
    if page.get("crumbs"):
        ld.append({
            "@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": n, "item": url(lang, p)}
                for i, (n, p) in enumerate([(t["home"], "")] + page["crumbs"] + [(page["h1_plain"], path)])
            ],
        })
    if page.get("faq"):
        ld.append({
            "@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in page["faq"]],
        })
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta name="theme-color" content="#0E0F14">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16.png">
<link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="canonical" href="{here}">
<link rel="alternate" hreflang="{'en' if lang=='en' else 'ja'}" href="{here}">
<link rel="alternate" hreflang="{'ja' if lang=='en' else 'en'}" href="{other}">
<link rel="alternate" hreflang="x-default" href="{url('en', path)}">
<meta property="og:type" content="{page.get('og_type','website')}">
<meta property="og:site_name" content="Spot">
<meta property="og:url" content="{here}">
<meta property="og:locale" content="{'en_US' if lang=='en' else 'ja_JP'}">
<meta property="og:locale:alternate" content="{'ja_JP' if lang=='en' else 'en_US'}">
<meta property="og:title" content="{esc(og_title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{SITE}/og/spot-cover.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Spot — the AI commercial studio for marketing teams.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(og_title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{SITE}/og/spot-cover.png">
{FONTS}
<style>{CSS}</style>
{''.join(jsonld(x) for x in ld)}
<script>var _d=document.documentElement;_d.classList.add('js');addEventListener('DOMContentLoaded',function(){{var e=document.querySelectorAll('.reveal'),r=function(x){{x.classList.add('in')}};if(!('IntersectionObserver'in window)){{e.forEach(r);return}}var io=new IntersectionObserver(function(es){{es.forEach(function(en){{if(en.isIntersecting){{r(en.target);io.unobserve(en.target)}}}})}},{{rootMargin:'0px 0px -8% 0px'}});e.forEach(function(x){{io.observe(x)}});setTimeout(function(){{e.forEach(r)}},1500);}});</script>
</head>
<body>"""


def nav(lang: str, current: str) -> str:
    t = common.T[lang]
    links = "".join(
        f'<a href="{url(lang, p)}"{" aria-current=\"page\"" if current.strip("/").split("/")[0] == p else ""}>{esc(n)}</a>'
        for n, p in t["nav"]
    )
    en_here, ja_here = url("en", current), url("ja", current)
    return f"""<nav class="top"><div class="wrap nav-in">
  <a class="brand" href="{url(lang, '')}" aria-label="Spot home">{LOGO_SVG}<span class="word">Spot</span></a>
  <div class="nav-links">{links}</div>
  <div class="nav-right">
    <div class="lang" role="group" aria-label="Language"><a href="{en_here}" hreflang="en"{' aria-current="true"' if lang=='en' else ''}>EN</a><a href="{ja_here}" hreflang="ja"{' aria-current="true"' if lang=='ja' else ''}>日本語</a></div>
    <a class="btn btn-primary" style="padding:10px 18px" href="{common.DEMO_URL}">{esc(t['demo'])}</a>
  </div>
</div></nav>"""


def crumbs(lang: str, page: dict) -> str:
    if not page.get("crumbs"):
        return ""
    t = common.T[lang]
    items = [(t["home"], "")] + page["crumbs"]
    parts = [f'<a href="{url(lang, p)}">{esc(n)}</a>' for n, p in items]
    return '<div class="wrap crumbs">' + "<span>/</span>".join(parts) + f"<span>/</span>{esc(page['h1_plain'])}</div>"


def footer(lang: str) -> str:
    t = common.T[lang]
    cols = ""
    for title, links in t["footer"]:
        lis = "".join(f'<li><a href="{url(lang, p)}">{esc(n)}</a></li>' for n, p in links)
        cols += f"<div><h4>{esc(title)}</h4><ul>{lis}</ul></div>"
    return f"""<footer><div class="wrap">
  <div class="foot-in">
    <div><div class="brand"><span class="word">Spot</span></div><p style="margin-top:12px;max-width:30ch">{esc(t['tagline'])}</p></div>
    {cols}
  </div>
  <div class="foot-bottom"><span>© 2026 Spot</span><span>{esc(t['foot_note'])}</span></div>
</div></footer>
</body></html>"""


def final_cta(lang: str, page: dict) -> str:
    t = common.T[lang]
    h, p = page.get("cta", (t["cta_h"], t["cta_p"]))
    return f"""<section class="final"><div class="wrap">
  <h2>{esc(h)}</h2><p>{esc(p)}</p>
  <a class="btn btn-primary" style="padding:15px 28px;font-size:16px" href="{common.app_link('final')}">{esc(t['start'])}</a>
  <a class="btn btn-ghost" style="padding:15px 28px;font-size:16px;margin-left:10px" href="{common.DEMO_URL}">{esc(t['demo'])}</a>
</div></section>"""


def related(lang: str, page: dict) -> str:
    if not page.get("related"):
        return ""
    t = common.T[lang]
    lis = "".join(f'<li><a href="{url(lang, p)}">{esc(n)}</a></li>' for n, p in page["related"])
    return f'<div class="wrap narrow related"><h2>{esc(t["related"])}</h2><ul>{lis}</ul></div>'


# --------------------------------------------------------------------------- blocks
def block_answer(b):
    return f'<div class="answer"><h2>{esc(b["q"])}</h2><p>{md_inline(b["a"])}</p></div>'


def block_qa(b):
    items = "".join(f'<div class="q"><h3>{esc(q)}</h3><p>{md_inline(a)}</p></div>' for q, a in b["items"])
    head_ = f'<div class="sec-head"><span class="eyebrow">{esc(b.get("eyebrow",""))}</span><h2>{esc(b["h"])}</h2></div>' if b.get("h") else ""
    return f'{head_}<div class="qa">{items}</div>'


def block_table(b):
    ths = "".join(f"<th>{esc(c)}</th>" for c in b["cols"])
    trs = ""
    for row in b["rows"]:
        tds = ""
        for i, cell in enumerate(row):
            cls = ' class="hl"' if (b.get("hl_col") == i) else ""
            tds += f"<td{cls}>{md_inline(str(cell))}</td>"
        trs += f"<tr>{tds}</tr>"
    head_ = f'<div class="sec-head"><span class="eyebrow">{esc(b.get("eyebrow",""))}</span><h2>{esc(b["h"])}</h2>{("<p>"+md_inline(b["p"])+"</p>") if b.get("p") else ""}</div>' if b.get("h") else ""
    cap = f'<p class="cap">{md_inline(b["cap"])}</p>' if b.get("cap") else ""
    return f'{head_}<div class="tw"><table><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table></div>{cap}'


def block_facts(b):
    items = ""
    for f in b["items"]:
        src = f'<div class="s"><a href="{esc(f["url"])}" rel="noopener">{esc(f["src"])}</a></div>' if f.get("url") else ""
        items += f'<div class="fact"><div class="n">{esc(f["n"])}</div><div class="k">{md_inline(f["k"])}</div>{src}</div>'
    head_ = f'<div class="sec-head"><span class="eyebrow">{esc(b.get("eyebrow",""))}</span><h2>{esc(b["h"])}</h2></div>' if b.get("h") else ""
    return f'{head_}<div class="facts">{items}</div>'


def block_quote(b):
    return f'<blockquote class="pull">{md_inline(b["text"])}<cite>{esc(b["who"])}</cite></blockquote>'


def block_prose(b):
    head_ = f'<div class="sec-head"><span class="eyebrow">{esc(b.get("eyebrow",""))}</span><h2>{esc(b["h"])}</h2></div>' if b.get("h") else ""
    body = ""
    for para in b["paras"]:
        if isinstance(para, list):
            body += "<ul>" + "".join(f"<li>{md_inline(x)}</li>" for x in para) + "</ul>"
        else:
            body += f"<p>{md_inline(para)}</p>"
    return f'{head_}<div class="prose">{body}</div>'


def block_cards(b, lang):
    items = ""
    for c in b["items"]:
        more = f'<a class="more" href="{url(lang, c["path"])}">{esc(c.get("more", common.T[lang]["more"]))} →</a>' if c.get("path") else ""
        items += f'<div class="card"><h3>{esc(c["h"])}</h3><p>{md_inline(c["p"])}</p>{more}</div>'
    head_ = f'<div class="sec-head"><span class="eyebrow">{esc(b.get("eyebrow",""))}</span><h2>{esc(b["h"])}</h2>{("<p>"+md_inline(b["p"])+"</p>") if b.get("p") else ""}</div>' if b.get("h") else ""
    return f'{head_}<div class="{b.get("cls","grid3")}">{items}</div>'


def block_steps(b):
    items = "".join(f'<div class="step"><div class="no">{esc(no)}</div><h3>{esc(h)}</h3><p>{md_inline(p)}</p></div>' for no, h, p in b["items"])
    head_ = f'<div class="sec-head"><span class="eyebrow">{esc(b.get("eyebrow",""))}</span><h2>{esc(b["h"])}</h2>{("<p>"+md_inline(b["p"])+"</p>") if b.get("p") else ""}</div>' if b.get("h") else ""
    return f'{head_}<div class="steps">{items}</div>'


def block_band(b):
    items = "".join(f'<div class="metric"><div class="n">{n}</div><div class="k">{esc(k)}</div></div>' for n, k in b["items"])
    return f'<div class="band">{items}</div>'


def block_plans(b, lang):
    t = common.T[lang]
    poplabel = {"en": "Most popular", "ja": "人気"}[lang]
    cards = ""
    for p in common.PLANS:
        name = p["name"]
        price = f'${p["usd"]:,}' if isinstance(p["usd"], int) else p["usd"]
        jp = f'¥{p["jpy"]:,}' if isinstance(p["jpy"], int) else p["jpy"]
        per = t["per_month"] if isinstance(p["usd"], int) else ""
        feats = "".join(f"<li>{esc(x)}</li>" for x in p["features"][lang])
        hl = ' hl' if p.get("hl") else ""
        badge = f'<span class="pop">{poplabel}</span>' if p.get("hl") else ""
        cta_href = common.DEMO_URL if p["id"] in ("business", "enterprise") else common.app_link("pricing", p["id"])
        cta_txt = t["talk"] if p["id"] in ("business", "enterprise") else t["start"]
        cards += f"""<div class="plan{hl}">{badge}<div class="nm">{esc(name)}</div>
  <div class="pr">{esc(price)}<small> {per}</small></div><div class="jp">{esc(jp)}{(' ' + t['per_month']) if isinstance(p['jpy'], int) else ''}</div>
  <div class="sp"><strong>{esc(p['spots'][lang])}</strong></div><ul>{feats}</ul>
  <a class="btn {'btn-primary' if p.get('hl') else 'btn-ghost'}" href="{cta_href}">{esc(cta_txt)}</a></div>"""
    plain = "<br>".join(md_inline(x) for x in common.PLAIN_PRICE[lang])
    head_ = f'<div class="sec-head"><span class="eyebrow">{esc(b.get("eyebrow",""))}</span><h2>{esc(b["h"])}</h2>{("<p>"+md_inline(b["p"])+"</p>") if b.get("p") else ""}</div>' if b.get("h") else ""
    return f'{head_}<div class="plans">{cards}</div><div class="plain">{plain}</div>'


def render_blocks(blocks, lang):
    out = ""
    for b in blocks:
        k = b["type"]
        if k == "answer": out += f'<div class="wrap narrow">{block_answer(b)}</div>'
        elif k == "qa": out += f'<section class="blk reveal"><div class="wrap narrow">{block_qa(b)}</div></section>'
        elif k == "table": out += f'<section class="blk reveal"><div class="wrap">{block_table(b)}</div></section>'
        elif k == "facts": out += f'<section class="blk reveal"><div class="wrap">{block_facts(b)}</div></section>'
        elif k == "quote": out += f'<div class="wrap narrow">{block_quote(b)}</div>'
        elif k == "prose": out += f'<section class="blk reveal"><div class="wrap narrow">{block_prose(b)}</div></section>'
        elif k == "cards": out += f'<section class="blk reveal"><div class="wrap">{block_cards(b, lang)}</div></section>'
        elif k == "steps": out += f'<section class="blk reveal"><div class="wrap">{block_steps(b)}</div></section>'
        elif k == "band": out += f'<section class="blk reveal"><div class="wrap">{block_band(b)}</div></section>'
        elif k == "plans": out += f'<section class="blk reveal"><div class="wrap">{block_plans(b, lang)}</div></section>'
        elif k == "html": out += b["html"]
        else: raise ValueError(f"unknown block type {k}")
    return out


# --------------------------------------------------------------------------- page renderers
def render_page(lang: str, page: dict) -> str:
    t = common.T[lang]
    body = head(lang, page) + nav(lang, page["path"]) + crumbs(lang, page)
    if page.get("hero"):
        body += page["hero"]
    else:
        body += f"""<header class="page-head"><div class="wrap narrow">
  <span class="eyebrow">{esc(page.get('eyebrow',''))}</span>
  <h1>{page['h1']}</h1>
  <p class="lede">{md_inline(page['lede'])}</p>
  <p class="upd">{esc(t['updated'])} {page.get('updated', TODAY)}</p>
</div></header>"""
    body += render_blocks(page["blocks"], lang)
    if page.get("faq"):
        faq_b = {"type": "qa", "eyebrow": "FAQ", "h": t["faq_h"], "items": page["faq"]}
        body += f'<section class="blk reveal"><div class="wrap narrow">{block_qa(faq_b)}</div></section>'
    body += related(lang, page)
    body += final_cta(lang, page)
    body += footer(lang)
    return body


# --------------------------------------------------------------------------- assets
def og_image(path: Path):
    """1200×630 social card — dark, branded (star logo + tagline). Uses Pillow; skips if absent."""
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
    except Exception:
        print("  (Pillow not available — skipping OG image)")
        return
    W, H = 1200, 630
    BG, INK, MUTED, FAINT, ACCENT = (19, 19, 24), (241, 237, 228), (168, 164, 154), (138, 134, 124), (74, 103, 227)
    im = Image.new("RGB", (W, H), BG)
    # accent glow top-right + cool glow bottom-left (blurred ellipses)
    for cx, cy, rw, rh, col, a in [(W - 190, 60, 380, 320, ACCENT, 120), (120, H - 60, 360, 300, (76, 194, 176), 55)]:
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(g).ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=col + (a,))
        im = Image.alpha_composite(im.convert("RGBA"), g.filter(ImageFilter.GaussianBlur(155))).convert("RGB")
    d = ImageDraw.Draw(im)

    def font(size, bold=True):
        for cand in (["/System/Library/Fonts/SF-Pro-Display-Black.otf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"]
                     if bold else ["/System/Library/Fonts/SF-Pro-Display-Regular.otf", "/System/Library/Fonts/Supplemental/Arial.ttf"]):
            if os.path.exists(cand):
                try:
                    return ImageFont.truetype(cand, size)
                except Exception:
                    pass
        return ImageFont.load_default()

    PAD = 84
    logo_p = ROOT / "static" / "spot-logo.png"
    if logo_p.is_file():
        logo = Image.open(logo_p).convert("RGBA")
        lh = 96
        logo = logo.resize((int(logo.width * lh / logo.height), lh), Image.LANCZOS)
        im.paste(logo, (PAD, 116), logo)
    d = ImageDraw.Draw(im)
    d.text((PAD, 288), "Ad videos,", font=font(96), fill=INK)
    d.text((PAD, 288 + 104), "just by choosing.", font=font(96), fill=ACCENT)
    d.text((PAD + 3, 288 + 104 + 128), "AI writes the script and generates the footage, UI and voice —", font=font(30, False), fill=MUTED)
    d.text((PAD + 3, 288 + 104 + 128 + 42), "a client-ready first cut, the same day.", font=font(30, False), fill=MUTED)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, "PNG", optimize=True)


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# --------------------------------------------------------------------------- main
def build():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    all_pages = []  # (lang, page)
    for mod in (core, usecases, compare, guides):
        for lang in ("en", "ja"):
            for page in mod.pages(lang):
                page.setdefault("h1_plain", page["h1"].replace("<br>", " "))
                all_pages.append((lang, page))

    # sanity: every EN path must exist in JA and vice versa (hreflang pairs)
    paths = {lang: {p["path"] for lang_, p in all_pages if lang_ == lang} for lang in ("en", "ja")}
    missing = (paths["en"] ^ paths["ja"])
    if missing:
        raise SystemExit(f"hreflang pair missing for: {sorted(missing)}")

    for lang, page in all_pages:
        write(out_path(lang, page["path"]), render_page(lang, page))

    # sitemaps (one per language) + index
    for lang in ("en", "ja"):
        urls = "".join(
            f"<url><loc>{url(lang, p['path'])}</loc><lastmod>{p.get('updated', TODAY)}</lastmod>"
            f'<xhtml:link rel="alternate" hreflang="en" href="{url("en", p["path"])}"/>'
            f'<xhtml:link rel="alternate" hreflang="ja" href="{url("ja", p["path"])}"/>'
            f'<xhtml:link rel="alternate" hreflang="x-default" href="{url("en", p["path"])}"/></url>'
            for l, p in all_pages if l == lang
        )
        write(DIST / ("sitemap.xml" if lang == "en" else "sitemap-ja.xml"),
              '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">' + urls + "</urlset>")
    write(DIST / "sitemap-index.xml",
          '<?xml version="1.0" encoding="UTF-8"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
          f"<sitemap><loc>{SITE}/sitemap.xml</loc></sitemap><sitemap><loc>{SITE}/sitemap-ja.xml</loc></sitemap></sitemapindex>")
    write(DIST / "robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap-index.xml\n")

    # llms.txt — cheap to ship, low expected impact (see spot-marketing.html §03)
    lines = [f"# Spot", "", "> " + common.T["en"]["tagline"], "", "## Pages", ""]
    for lang, page in all_pages:
        if lang == "en":
            lines.append(f"- [{page['h1_plain']}]({url('en', page['path'])}): {page['desc']}")
    lines += ["", "## 日本語", ""]
    for lang, page in all_pages:
        if lang == "ja":
            lines.append(f"- [{page['h1_plain']}]({url('ja', page['path'])}): {page['desc']}")
    write(DIST / "llms.txt", "\n".join(lines) + "\n")

    # IndexNow key file (key lives in site/indexnow.key; create one with `openssl rand -hex 16`)
    keyfile = ROOT / "indexnow.key"
    if keyfile.exists():
        key = keyfile.read_text().strip()
        write(DIST / f"{key}.txt", key)

    # copy static assets (hero thumbnails, etc.) → dist/
    static_dir = ROOT / "static"
    if static_dir.is_dir():
        for src in static_dir.rglob("*"):
            if src.is_file():
                dst = DIST / src.relative_to(static_dir)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

    og_image(DIST / "og" / "spot-cover.png")

    # url list for IndexNow / manual submission
    write(DIST / "urls.txt", "\n".join(url(l, p["path"]) for l, p in all_pages) + "\n")

    n_en = sum(1 for l, _ in all_pages if l == "en")
    print(f"built {len(all_pages)} pages ({n_en} en + {len(all_pages)-n_en} ja) → {DIST}")


if __name__ == "__main__":
    build()
    if "--serve" in sys.argv:
        import http.server, functools
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
        print("serving http://localhost:5510/")
        http.server.ThreadingHTTPServer(("", 5510), handler).serve_forever()
