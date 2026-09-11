"""Shared strings, plans, competitor data, and Organization JSON-LD."""

# ---- Replace once the real domain / app / booking URLs are confirmed ----------
SITE = "https://spot.video"
APP_URL = "https://app.spot.video/"
DEMO_URL = "mailto:hello@spot.video?subject=SPOT%20demo"
PRICE_DATE = "2026-09-10"   # date competitor prices were checked

T = {
    "en": {
        "home": "Home",
        "nav": [("How it works", "how-it-works"), ("Use cases", "use-cases"), ("Compare", "compare"), ("Guides", "guides"), ("Pricing", "pricing")],
        "demo": "Book a demo", "start": "Start free", "talk": "Talk to sales", "more": "Read more", "related": "Related",
        "updated": "Last updated", "faq_h": "Frequently asked questions", "per_month": "/ month",
        "cta_h": "Ship your next spot today.", "cta_p": "Pick platform, industry and audience. SPOT delivers a ready-to-ship commercial the same day.",
        "tagline": "The AI commercial studio for marketing teams. Every spot, in a day.",
        "foot_note": "English · 日本語 — AI video ad & commercial generator",
        "footer": [
            ("Product", [("How it works", "how-it-works"), ("Pricing", "pricing"), ("Brand safety", "brand-safety"), ("Security", "security")]),
            ("Use cases", [("SaaS demo ads", "use-cases/saas-demo-ads"), ("App install ads", "use-cases/app-install-ads"), ("YouTube bumper ads", "use-cases/youtube-bumper-ads"), ("CTV / OTT spots", "use-cases/ctv-ott-spots"), ("In-house teams", "use-cases/in-house-teams")]),
            ("Compare", [("SPOT vs Creatify", "compare/creatify"), ("SPOT vs HeyGen", "compare/heygen"), ("SPOT vs Waymark", "compare/waymark"), ("SPOT vs an agency", "compare/spot-vs-agency"), ("All alternatives", "compare")]),
            ("Guides", [("Cost of a 15-second commercial", "guides/how-much-does-a-15-second-commercial-cost"), ("Video ad specs 2026", "guides/video-ad-specs-2026"), ("Best AI video ad generators", "guides/best-ai-video-ad-generators-2026"), ("AI ads: copyright & compliance", "guides/ai-commercial-copyright-and-compliance")]),
        ],
    },
    "ja": {
        "home": "ホーム",
        "nav": [("使い方", "how-it-works"), ("ユースケース", "use-cases"), ("比較", "compare"), ("ガイド", "guides"), ("料金", "pricing")],
        "demo": "デモを予約", "start": "無料ではじめる", "talk": "営業に相談", "more": "詳しく見る", "related": "関連ページ",
        "updated": "最終更新", "faq_h": "よくある質問", "per_month": "/ 月",
        "cta_h": "次の動画広告も、その日のうちに。", "cta_p": "配信先・業種・ターゲットを選ぶだけ。SPOT がその日のうちに公開できる CM をお届けします。",
        "tagline": "マーケティングチームのための AI 動画広告・CM 制作ツール。",
        "foot_note": "日本語 · English — AI 動画広告・CM 制作ツール SPOT",
        "footer": [
            ("プロダクト", [("使い方", "how-it-works"), ("料金", "pricing"), ("ブランドセーフ", "brand-safety"), ("セキュリティ", "security")]),
            ("ユースケース", [("SaaS のデモ広告", "use-cases/saas-demo-ads"), ("アプリ獲得広告", "use-cases/app-install-ads"), ("YouTube バンパー広告", "use-cases/youtube-bumper-ads"), ("CTV / 運用型テレビ CM", "use-cases/ctv-ott-spots"), ("内製チーム", "use-cases/in-house-teams")]),
            ("比較", [("SPOT と Creatify", "compare/creatify"), ("SPOT と HeyGen", "compare/heygen"), ("SPOT と Waymark", "compare/waymark"), ("SPOT と制作会社", "compare/spot-vs-agency"), ("すべての比較", "compare")]),
            ("ガイド", [("15 秒 CM の制作費用と相場", "guides/how-much-does-a-15-second-commercial-cost"), ("動画広告の入稿規定 2026", "guides/video-ad-specs-2026"), ("AI 動画広告ツール おすすめ", "guides/best-ai-video-ad-generators-2026"), ("AI CM の著作権と景表法", "guides/ai-commercial-copyright-and-compliance")]),
        ],
    },
}

# ---- Plans (the unit is a spot: 3 patterns × 3 formats = 9 files) -------------
PLANS = [
    {"id": "free", "name": "Free", "usd": 0, "jpy": 0,
     "spots": {"en": "1 spot / month", "ja": "月 1 スポット"},
     "features": {"en": ["Watermark, 720p", "1 seat, 1 brand", "Community support"],
                  "ja": ["透かし入り・720p", "1 席・1 ブランド", "コミュニティサポート"]}},
    {"id": "starter", "name": "Starter", "usd": 99, "jpy": 14800,
     "spots": {"en": "6 spots / month", "ja": "月 6 スポット"},
     "features": {"en": ["1080p, no watermark", "2 seats, 1 brand", "Basic brand kit", "Extra spots $19 each", "Email support"],
                  "ja": ["1080p・透かしなし", "2 席・1 ブランド", "ブランドキット（基本）", "追加スポット $19（¥2,800）", "メールサポート"]}},
    {"id": "team", "name": "Team", "usd": 399, "jpy": 59800, "hl": True,
     "spots": {"en": "25 spots / month", "ja": "月 25 スポット"},
     "features": {"en": ["1080p", "5 seats, 3 brands", "Brand kit + pronunciation guide", "Approval flow", "Extra spots $19 each", "Priority support"],
                  "ja": ["1080p", "5 席・3 ブランド", "ブランドキット＋読み仮名辞書", "承認フロー", "追加スポット $19（¥2,800）", "優先サポート"]}},
    {"id": "business", "name": "Business", "usd": 1199, "jpy": 178000,
     "spots": {"en": "80 spots / month", "ja": "月 80 スポット"},
     "features": {"en": ["4K + Premium quality models", "Unlimited seats, 10 brands", "SSO, API, audit log", "Extra spots $15 each", "Shared Slack channel"],
                  "ja": ["4K・Premium quality モデル", "席無制限・10 ブランド", "SSO・API・監査ログ", "追加スポット $15（¥2,200）", "Slack 共有チャンネル"]}},
    {"id": "enterprise", "name": "Enterprise", "usd": "From $2,500", "jpy": "¥380,000〜",
     "spots": {"en": "Committed volume", "ja": "コミット制"},
     "features": {"en": ["Unlimited brands (agencies)", "White-label, DPA, security review", "Custom brand models", "Onboarding + CSM", "Invoice billing"],
                  "ja": ["ブランド無制限（代理店向け）", "ホワイトラベル・DPA・セキュリティ審査", "カスタムブランドモデル", "オンボーディング＋CSM", "請求書払い・年一括"]}},
]

# Plain-text pricing sentences: what an AI assistant should quote.
PLAIN_PRICE = {
    "en": [
        "**SPOT pricing (USD, per month, updated " + PRICE_DATE + "):** Free $0 for 1 spot with watermark · Starter $99 for 6 spots · Team $399 for 25 spots and 5 seats · Business $1,199 for 80 spots, unlimited seats, SSO and API · Enterprise from $2,500 with committed volume.",
        "One spot is one finished commercial delivered as 3 intro patterns × 3 formats (16:9, 9:16, 1:1) = 9 files. Extra spots cost $19 (Starter, Team) or $15 (Business). Annual billing gives 2 months free.",
    ],
    "ja": [
        "**SPOT の料金（税別・月額、" + PRICE_DATE + " 更新）:** Free ¥0（月 1 スポット・透かし入り）· Starter ¥14,800（月 6 スポット）· Team ¥59,800（月 25 スポット・5 席）· Business ¥178,000（月 80 スポット・席無制限・SSO・API）· Enterprise ¥380,000〜（コミット制）。",
        "1 スポット＝完成した CM 1 本。3 つのイントロ案 × 3 フォーマット（横 16:9・縦 9:16・正方形 1:1）＝9 ファイルを書き出します。追加スポットは ¥2,800（Starter・Team）または ¥2,200（Business）。年契約は 2 か月分無料、請求書払いに対応。",
    ],
}

# ---- Competitor facts used on /compare and the listicle (checked PRICE_DATE) ----
# verified: True = read from the vendor's own pricing page; False = third-party only.
COMPETITORS = {
    "creatify": {"name": "Creatify", "url": "https://creatify.ai/pricing", "verified": True,
                 "entry": "$39 / mo (100 credits)", "mid": "$99 / mo (300 credits)", "unit": "Credits (5 per 15 s of video)",
                 "per_video": "≈ $3.30–3.90 per 30 s", "free": "10 credits (about 2 ads, watermarked)",
                 "output": "UGC-style talking-avatar ads, product videos, one format per render",
                 "seats": "2 seats on Pro (max 5)", "positioning": "AI ads that win — DTC, e-commerce, gaming, agencies"},
    "arcads": {"name": "Arcads", "url": "https://arcads.ai", "verified": False,
               "entry": "$110 / mo list ($77 with promo), 8,000 credits", "mid": "$220 / mo (16,000 credits)", "unit": "Credits (800 per billed actor-minute)",
               "per_video": "≈ $11 per talking-actor video", "free": "No free plan",
               "output": "AI actor UGC ads for Meta / TikTok; one format per render",
               "seats": "Unlimited on Pro ($550)", "positioning": "Create winning ads with AI — performance marketers"},
    "heygen": {"name": "HeyGen", "url": "https://www.heygen.com/pricing", "verified": True,
               "entry": "$29 / mo (Creator, 600 credits)", "mid": "$149 / mo + $20 per seat (Business, 1,500 credits)", "unit": "Credits (Video Agent 30–120 per minute)",
               "per_video": "≈ $1–1.50 per avatar minute", "free": "3 videos per month",
               "output": "Avatar presenter videos, translation, Video Agent; not a commercial format",
               "seats": "$20 per additional seat", "positioning": "AI video platform — avatars, localization"},
    "waymark": {"name": "Waymark", "url": "https://cms.waymark.com/marketing/pricing", "verified": True,
                "entry": "$399 / mo (2 finalized videos)", "mid": "From $1,125 / mo (Team, annual)", "unit": "Finalized downloads per month",
                "per_video": "≈ $87–200 per finished video", "free": "7-day trial",
                "output": "Template-driven local TV and CTV spots from stock and business data",
                "seats": "Team / Enterprise custom", "positioning": "AI video ad creative — broadcasters and media sales"},
    "poolday": {"name": "Poolday", "url": "https://poolday.ai/pricing", "verified": True,
                "entry": "$1,250 / mo (first month $500)", "mid": "From $2,500 / mo (Enterprise)", "unit": "Dollar credits",
                "per_video": "$5–25 per finished video (vendor statement)", "free": "No free plan",
                "output": "High-volume UGC and performance videos for apps, games, e-commerce",
                "seats": "Unlimited on Enterprise", "positioning": "Media superintelligence — apps, games, e-commerce"},
}

SPOT_ROW = {
    "en": {"entry": "$99 / mo (6 spots)", "mid": "$399 / mo (25 spots, 5 seats)", "unit": "Spots (1 spot = 1 finished commercial = 9 files)",
           "per_video": "$16 per spot on Team (9 files)", "free": "1 spot per month, watermarked",
           "output": "Finished commercials: live-action footage, your real product UI, voiceover, music — 3 patterns × 3 formats",
           "seats": "5 on Team, unlimited on Business", "positioning": "AI commercial studio for in-house marketing teams"},
    "ja": {"entry": "¥14,800 / 月（6 スポット）", "mid": "¥59,800 / 月（25 スポット・5 席）", "unit": "スポット（1 スポット＝完成 CM 1 本＝9 ファイル）",
           "per_video": "Team で 1 スポット ¥2,400 相当（9 ファイル）", "free": "月 1 スポット（透かし入り）",
           "output": "完成した CM：実写・実際のプロダクト画面・ナレーション・BGM を 3 パターン × 3 フォーマットで",
           "seats": "Team 5 席、Business 無制限", "positioning": "内製マーケティングチームのための AI CM スタジオ"},
}


def org_jsonld(lang):
    return {
        "@context": "https://schema.org", "@type": "Organization", "name": "SPOT", "url": SITE + "/",
        "logo": SITE + "/og/spot-cover.png",
        "description": T[lang]["tagline"],
        "sameAs": [],   # add G2 / LinkedIn / YouTube / X profile URLs once created
    }


def website_jsonld(lang):
    return {"@context": "https://schema.org", "@type": "WebSite", "name": "SPOT", "url": SITE + "/", "inLanguage": ["en", "ja"]}


def software_jsonld(lang):
    offers = []
    for p in PLANS:
        if isinstance(p["usd"], int):
            offers.append({"@type": "Offer", "name": p["name"], "price": str(p["usd"]), "priceCurrency": "USD",
                           "description": p["spots"]["en"] + " — billed monthly", "url": SITE + "/pricing/"})
            offers.append({"@type": "Offer", "name": p["name"], "price": str(p["jpy"]), "priceCurrency": "JPY",
                           "description": p["spots"]["ja"] + "（月額・税別）", "url": SITE + "/ja/pricing/"})
    return {
        "@context": "https://schema.org", "@type": "SoftwareApplication", "name": "SPOT",
        "applicationCategory": "MultimediaApplication", "applicationSubCategory": "AI video ad & commercial generator",
        "operatingSystem": "Web", "url": SITE + "/", "inLanguage": ["en", "ja"],
        "description": "SPOT turns three choices into a finished video ad. AI generates the footage, your real product UI, the voiceover and the music, then delivers a ready-to-ship commercial the same day.",
        "offers": {"@type": "AggregateOffer", "lowPrice": "0", "highPrice": "2500", "priceCurrency": "USD", "offerCount": str(len(offers)), "offers": offers},
        "publisher": {"@type": "Organization", "name": "SPOT", "url": SITE + "/"},
    }
