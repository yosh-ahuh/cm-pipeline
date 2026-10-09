"""Shared strings, plans, competitor data, and Organization JSON-LD."""

# ---- ドメインは仮（2026-10-08）。本番ドメインが決まったら DOMAIN だけ差し替える --------
# ランディング/サイト = https://spot.<DOMAIN>/   アプリ = https://app.spot.<DOMAIN>/
# （spot-landing.html と spot-app の _headers / README、Supabase の Site URL も同時に更新すること）
DOMAIN = "creativepunx.com"
SITE = f"https://spot.{DOMAIN}"
APP_URL = f"https://app.spot.{DOMAIN}/"
# デモ導線は廃止（2026-10-08）。Enterprise の問い合わせだけメールで受ける。
CONTACT_URL = f"mailto:hello@{DOMAIN}?subject=Spot%20Enterprise"


def app_link(campaign: str, plan: str | None = None, source: str = "site") -> str:
    """ランディング/サイトの CTA → アプリ。流入元を utm_* で付け、アプリ側が signup 時に保存する。"""
    q = f"utm_source={source}&utm_medium=cta&utm_campaign={campaign}"
    if plan:
        q += f"&plan={plan}"
    return f"{APP_URL}?{q}"
PRICE_DATE = "2026-09-10"   # date competitor prices were checked

T = {
    "en": {
        "home": "Home",
        "nav": [("How it works", "how-it-works"), ("Use cases", "use-cases"), ("Compare", "compare"), ("Guides", "guides"), ("Pricing", "pricing")],
        "start": "Start free trial", "talk": "Talk to sales", "pricing_cta": "See pricing", "bill_m": "Monthly", "bill_y": "Annual · 1 month free", "billed_year": "{y} billed yearly · 1 month free", "trial": "Every plan starts with a 7-day free trial — 2 spots included, cancel anytime.", "per_spot": "≈ ${usd:,.2f} per spot · 9 files", "more": "Read more", "related": "Related",
        "updated": "Last updated", "faq_h": "Frequently asked questions", "per_month": "/ month",
        "cta_h": "Ship your next spot today.", "cta_p": "Pick platform, industry and audience. Spot delivers a ready-to-ship commercial the same day.",
        "tagline": "The AI commercial studio for marketing teams. Every spot, in a day.",
        "foot_note": "English · 日本語 — AI video ad & commercial generator",
        "footer": [
            ("Product", [("How it works", "how-it-works"), ("Pricing", "pricing"), ("Brand safety", "brand-safety"), ("Security", "security")]),
            ("Use cases", [("SaaS demo ads", "use-cases/saas-demo-ads"), ("App install ads", "use-cases/app-install-ads"), ("YouTube bumper ads", "use-cases/youtube-bumper-ads"), ("CTV / OTT spots", "use-cases/ctv-ott-spots"), ("In-house teams", "use-cases/in-house-teams")]),
            ("Compare", [("Spot vs Creatify", "compare/creatify"), ("Spot vs HeyGen", "compare/heygen"), ("Spot vs Waymark", "compare/waymark"), ("Spot vs an agency", "compare/spot-vs-agency"), ("All alternatives", "compare")]),
            ("Guides", [("Cost of a 15-second commercial", "guides/how-much-does-a-15-second-commercial-cost"), ("Video ad specs 2026", "guides/video-ad-specs-2026"), ("Best AI video ad generators", "guides/best-ai-video-ad-generators-2026"), ("AI ads: copyright & compliance", "guides/ai-commercial-copyright-and-compliance")]),
        ],
    },
    "ja": {
        "home": "ホーム",
        "nav": [("使い方", "how-it-works"), ("ユースケース", "use-cases"), ("比較", "compare"), ("ガイド", "guides"), ("料金", "pricing")],
        "start": "7 日間無料で試す", "talk": "営業に相談", "pricing_cta": "料金を見る", "bill_m": "月払い", "bill_y": "年払い・1 か月分無料", "billed_year": "年額 {y}（1 か月分無料）", "trial": "全プラン、7 日間の無料トライアル付き。2 スポット込み、いつでも解約できます。", "per_spot": "1 本あたり 約 ¥{jpy:,}・9 ファイル", "more": "詳しく見る", "related": "関連ページ",
        "updated": "最終更新", "faq_h": "よくある質問", "per_month": "/ 月",
        "cta_h": "次の動画広告も、その日のうちに。", "cta_p": "配信先・業種・ターゲットを選ぶだけ。Spot がその日のうちに公開できる CM をお届けします。",
        "tagline": "マーケティングチームのための AI 動画広告・CM 制作ツール。",
        "foot_note": "日本語 · English — AI 動画広告・CM 制作ツール Spot",
        "footer": [
            ("プロダクト", [("使い方", "how-it-works"), ("料金", "pricing"), ("ブランドセーフ", "brand-safety"), ("セキュリティ", "security")]),
            ("ユースケース", [("SaaS のデモ広告", "use-cases/saas-demo-ads"), ("アプリ獲得広告", "use-cases/app-install-ads"), ("YouTube バンパー広告", "use-cases/youtube-bumper-ads"), ("CTV / 運用型テレビ CM", "use-cases/ctv-ott-spots"), ("内製チーム", "use-cases/in-house-teams")]),
            ("比較", [("Spot と Creatify", "compare/creatify"), ("Spot と HeyGen", "compare/heygen"), ("Spot と Waymark", "compare/waymark"), ("Spot と制作会社", "compare/spot-vs-agency"), ("すべての比較", "compare")]),
            ("ガイド", [("15 秒 CM の制作費用と相場", "guides/how-much-does-a-15-second-commercial-cost"), ("動画広告の入稿規定 2026", "guides/video-ad-specs-2026"), ("AI 動画広告ツール おすすめ", "guides/best-ai-video-ad-generators-2026"), ("AI CM の著作権と景表法", "guides/ai-commercial-copyright-and-compliance")]),
        ],
    },
}

# ---- Trial / billing (2026-10-09 決定: Free プラン廃止、7 日間トライアル、年契約は 1 か月分無料) ----
TRIAL = {"days": 7, "spots": 2}
ANNUAL_MONTHS = 11          # 年契約 = 11 か月分の請求（1 か月分無料）

# ---- Plans (the unit is a spot: 3 patterns × 3 formats = 9 files) -------------
PLANS = [
    {"id": "starter", "name": "Starter", "usd": 99, "jpy": 14800, "n": 6,
     "spots": {"en": "6 spots / month", "ja": "月 6 スポット"},
     "features": {"en": ["1080p, no watermark", "2 seats, 1 brand", "Basic brand kit", "Extra spots $19 each", "Email support"],
                  "ja": ["1080p・透かしなし", "2 席・1 ブランド", "ブランドキット（基本）", "追加スポット $19（¥2,800）", "メールサポート"]}},
    {"id": "team", "name": "Team", "usd": 399, "jpy": 59800, "hl": True, "n": 25,
     "spots": {"en": "25 spots / month", "ja": "月 25 スポット"},
     "features": {"en": ["1080p", "5 seats, 3 brands", "Brand kit + pronunciation guide", "Approval flow", "Extra spots $19 each", "Priority support"],
                  "ja": ["1080p", "5 席・3 ブランド", "ブランドキット＋読み仮名辞書", "承認フロー", "追加スポット $19（¥2,800）", "優先サポート"]}},
    {"id": "business", "name": "Business", "usd": 1199, "jpy": 178000, "n": 80,
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
        "**Spot pricing (USD, per month, updated " + PRICE_DATE + "):** Starter $99 for 6 spots · Team $399 for 25 spots and 5 seats · Business $1,199 for 80 spots, unlimited seats, SSO and API · Enterprise from $2,500 with committed volume. Every plan starts with a 7-day free trial (2 spots). There is no free plan.",
        "One spot is one finished commercial delivered as 3 intro patterns × 3 formats (16:9, 9:16, 1:1) = 9 files. Extra spots cost $19 (Starter, Team) or $15 (Business). Annual billing gives 1 month free: Starter $1,089, Team $4,389, Business $13,189 per year.",
    ],
    "ja": [
        "**Spot の料金（税別・月額、" + PRICE_DATE + " 更新）:** Starter ¥14,800（月 6 スポット）· Team ¥59,800（月 25 スポット・5 席）· Business ¥178,000（月 80 スポット・席無制限・SSO・API）· Enterprise ¥380,000〜（コミット制）。全プランに 7 日間の無料トライアル（2 スポット）。無料プランはありません。",
        "1 スポット＝完成した CM 1 本。3 つのイントロ案 × 3 フォーマット（横 16:9・縦 9:16・正方形 1:1）＝9 ファイルを書き出します。追加スポットは ¥2,800（Starter・Team）または ¥2,200（Business）。年契約は 1 か月分無料（Starter ¥162,800・Team ¥657,800・Business ¥1,958,000 / 年）、請求書払いに対応。",
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
           "per_video": "$16 per spot on Team (9 files)", "free": "7-day free trial (2 spots); no free plan",
           "output": "Finished commercials: live-action footage, your real product UI, voiceover, music — 3 patterns × 3 formats",
           "seats": "5 on Team, unlimited on Business", "positioning": "AI commercial studio for in-house marketing teams"},
    "ja": {"entry": "¥14,800 / 月（6 スポット）", "mid": "¥59,800 / 月（25 スポット・5 席）", "unit": "スポット（1 スポット＝完成 CM 1 本＝9 ファイル）",
           "per_video": "Team で 1 スポット ¥2,400 相当（9 ファイル）", "free": "7 日間の無料トライアル（2 スポット）。無料プランなし",
           "output": "完成した CM：実写・実際のプロダクト画面・ナレーション・BGM を 3 パターン × 3 フォーマットで",
           "seats": "Team 5 席、Business 無制限", "positioning": "内製マーケティングチームのための AI CM スタジオ"},
}


def org_jsonld(lang):
    return {
        "@context": "https://schema.org", "@type": "Organization", "name": "Spot", "url": SITE + "/",
        "logo": SITE + "/og/spot-cover.png",
        "description": T[lang]["tagline"],
        "sameAs": [],   # add G2 / LinkedIn / YouTube / X profile URLs once created
    }


def website_jsonld(lang):
    return {"@context": "https://schema.org", "@type": "WebSite", "name": "Spot", "url": SITE + "/", "inLanguage": ["en", "ja"]}


def software_jsonld(lang):
    offers = []
    for p in PLANS:
        if isinstance(p["usd"], int):
            offers.append({"@type": "Offer", "name": p["name"], "price": str(p["usd"]), "priceCurrency": "USD",
                           "description": p["spots"]["en"] + " — billed monthly", "url": SITE + "/pricing/"})
            offers.append({"@type": "Offer", "name": p["name"], "price": str(p["jpy"]), "priceCurrency": "JPY",
                           "description": p["spots"]["ja"] + "（月額・税別）", "url": SITE + "/ja/pricing/"})
    return {
        "@context": "https://schema.org", "@type": "SoftwareApplication", "name": "Spot",
        "applicationCategory": "MultimediaApplication", "applicationSubCategory": "AI video ad & commercial generator",
        "operatingSystem": "Web", "url": SITE + "/", "inLanguage": ["en", "ja"],
        "description": "Spot turns three choices into a finished video ad. AI generates the footage, your real product UI, the voiceover and the music, then delivers a ready-to-ship commercial the same day.",
        "offers": {"@type": "AggregateOffer", "lowPrice": "99", "highPrice": "2500", "priceCurrency": "USD", "offerCount": str(len(offers)), "offers": offers},
        "publisher": {"@type": "Organization", "name": "Spot", "url": SITE + "/"},
    }
