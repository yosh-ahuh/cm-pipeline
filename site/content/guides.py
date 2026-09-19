"""Guides (/guides/*): buying-intent explainers with sourced numbers, plus the hub."""
from .common import COMPETITORS, PRICE_DATE

CRUMB = {"en": [("Guides", "guides")], "ja": [("ガイド", "guides")]}


def _g(lang, slug, d, jsonld_type="Article"):
    return {"path": f"guides/{slug}", "crumbs": CRUMB[lang], "eyebrow": "Guide" if lang == "en" else "ガイド",
            "title": d["title"], "desc": d["desc"], "h1": d["h1"], "lede": d["lede"], "updated": d.get("updated", PRICE_DATE),
            "og_type": "article", "blocks": d["blocks"], "faq": d["faq"], "related": d["related"],
            "jsonld": [{"@context": "https://schema.org", "@type": jsonld_type, "headline": d["h1"].replace("<br>", " "),
                        "datePublished": "2026-09-10", "dateModified": d.get("updated", PRICE_DATE), "inLanguage": lang,
                        "author": {"@type": "Organization", "name": "Spot"}, "publisher": {"@type": "Organization", "name": "Spot"}}]}


# --------------------------------------------------------------------------- cost
def cost(lang):
    if lang == "en":
        return _g("en", "how-much-does-a-15-second-commercial-cost", {
            "title": "How much does a 15-second commercial cost in 2026? Agency, freelancer and AI prices",
            "desc": "A 15-second commercial costs $5,000–15,000 from a US agency, $50,000+ for broadcast-grade production, and about $16 per spot with an AI commercial studio. Japan ranges and what drives the price, with sources.",
            "h1": "How much does a<br>15-second commercial cost?",
            "lede": "Short answer: anywhere from $16 to $50,000, depending on who makes it and what is on screen. Here are the ranges, what drives them, and what changed in 2026.",
            "blocks": [
                {"type": "answer", "q": "How much does a 15-second commercial cost?",
                 "a": "In the US, a 15-second commercial from a production agency typically costs **$5,000–15,000**; broadcast-grade spots with talent and locations run **$50,000 and up**. Freelancers and template tools sit at **$500–3,000**. An AI commercial studio like Spot produces a spot for **$16** on a $399 Team plan (25 spots a month), including three variations in three formats. Media costs are separate."},
                {"type": "table", "h": "Cost ranges by production method (2026)", "cols": ["Method", "Typical cost per 15 s spot", "Time to first cut", "What is included"],
                 "rows": [["Broadcast agency, talent and locations", "$50,000+", "4–8 weeks", "Director, crew, talent, original music, one master"],
                          ["Mid-size agency or studio", "$5,000–15,000", "About 3 weeks", "Concept, stock or light shoot, edit, one format; extra formats billed"],
                          ["Freelancer or small studio", "$500–3,000", "1–2 weeks", "Edit from your assets and stock, one format"],
                          ["Template video tools", "$20–400 a month", "Hours", "Stock and text templates; no live-action generation"],
                          ["AI commercial studio (Spot)", "$16 per spot (Team)", "Same day", "Generated live-action, real product UI, voiceover, music, 3 patterns × 3 formats"]],
                 "cap": "US agency ranges are the consensus of published production-cost guides from studios such as Vidico; Spot figure from [Spot pricing](/pricing/)."},
                {"type": "table", "h": "Japan: 15-second commercial production costs", "cols": ["Type", "Range (JPY)", "Source"],
                 "rows": [["TV commercial production, talent excluded", "¥1,000,000–5,000,000", "[動画幹事](https://douga-kanji.com/posts/commercial-price)"],
                          ["Web / social 15–30 s ad video", "¥50,000–500,000; average order ¥798,000, median ¥600,000", "[0120.co.jp](https://0120.co.jp/blog/video-33/)"],
                          ["AI-assisted production studios", "¥100,000–500,000; high-end AI brand spots ¥500,000–1,500,000", "[movieimpact](https://movieimpact.net/columns/2026-04-05-ai-video-production-cost-2026-latest-guide)"],
                          ["Managed AI creative (Kaizen Ad)", "From ¥50,000 per video, 5 business days", "[Kaizen Platform](https://kaizenplatform.com/contents/video-advertising-costs)"],
                          ["Generative-AI TV spots (CyberAgent)", "¥3,000,000 for 3 videos", "[CyberAgent](https://www.cyberagent.co.jp/news/detail/id=32619)"]]},
                {"type": "prose", "h": "What actually drives the price", "paras": [
                    "Four things move a commercial’s cost more than anything else:",
                    ["**People on screen.** Real talent means casting, usage rights and a shoot day. Synthetic people remove all three.",
                     "**Locations and crew.** A shoot day with crew is the single largest line in an agency quote. Generated footage has no shoot day.",
                     "**Formats and versions.** Agencies bill each aspect ratio and each variant as a change order. AI studios generate them from the same brief.",
                     "**Revisions.** Rounds of feedback over days are billed in hours. Plain-language re-renders take minutes."],
                    "Media is always separate. A 15-second slot on a Tokyo key station starts around ¥750,000 per airing; a YouTube view costs ¥3–20; TikTok CPMs run ¥400–1,000. Production is now often the smaller half of a small campaign, which is why teams are moving it in-house."]},
                {"type": "facts", "h": "Numbers to remember", "items": [
                    {"n": "$5k–15k", "k": "Typical US agency cost for one 15-second spot, one format.", "src": "Production cost guides", "url": ""},
                    {"n": "¥600,000", "k": "Median order value for a web ad video in Japan.", "src": "0120.co.jp", "url": "https://0120.co.jp/blog/video-33/"},
                    {"n": "$16", "k": "Cost of one Spot spot (nine files) on the Team plan.", "src": "Spot pricing", "url": "/pricing/"}]},
            ],
            "faq": [("Does the price include media?", "No. All figures above are production only. Media buying is billed separately by the platform or your agency."),
                    ("Why is there such a wide range?", "Talent, locations and crew. A spot with real people in real places costs ten times one built from stock or generated footage."),
                    ("Is AI-generated video cheaper only because it is lower quality?", "It is cheaper because there is no shoot day, no crew and no change orders. Quality depends on the tool: Spot reviews every shot before animation and composites your real product UI, which is where most AI video looks wrong."),
                    ("How much should a small SaaS budget for video ads?", "Japanese app and SaaS teams typically spend ¥100,000–300,000 a month testing creative before scaling; with AI production the majority of that can go to media.")],
            "related": [("Spot vs an agency", "compare/spot-vs-agency"), ("Pricing", "pricing"), ("How long should a video ad be?", "guides/how-long-should-a-video-ad-be")],
        })
    return _g("ja", "how-much-does-a-15-second-commercial-cost", {
        "title": "15 秒 CM の制作費用と相場（2026 年）｜制作会社・フリーランス・AI の価格",
        "desc": "15 秒 CM の制作費は、Web 用で ¥5 万〜50 万、テレビ CM で ¥100 万〜500 万（タレント別）、AI CM スタジオなら 1 スポット約 ¥2,400。相場の内訳、価格を左右する要因、2026 年に変わったことを出典付きで。",
        "h1": "15 秒 CM の制作費は、<br>いくらかかる？",
        "lede": "結論から言うと ¥2,400 から ¥500 万まで。誰が作るか、画面に何が映るかで決まります。相場の幅、その理由、2026 年に変わったことをまとめます。",
        "blocks": [
            {"type": "answer", "q": "15 秒 CM の制作費はいくらですか？",
             "a": "国内では、Web・SNS 向けの 15〜30 秒動画広告は **¥5 万〜50 万**（平均発注額 ¥79.8 万、中央値 ¥60 万）、テレビ CM の制作はタレント費を除いて **¥100 万〜500 万** が相場です。AI 専業スタジオは ¥10 万〜50 万。AI CM スタジオの Spot は Team プラン（月額 ¥59,800・25 スポット）で 1 スポット **約 ¥2,400**、3 パターン × 3 フォーマット込みです。媒体費は別です。"},
            {"type": "table", "h": "制作方法別の相場（2026 年）", "cols": ["方法", "15 秒 1 本の目安", "初稿まで", "含まれるもの"],
             "rows": [["テレビ CM（タレント・ロケあり）", "¥100 万〜500 万（タレント費別）", "1〜2 か月", "企画 ¥10〜35 万、撮影 ¥10〜80 万、編集・音 ¥15〜40 万、マスター 1 本"],
                      ["制作会社（Web・SNS 用）", "¥5 万〜50 万、平均 ¥79.8 万", "約 3 週間", "企画・素材撮影か素材購入・編集・1 フォーマット。追加は別料金"],
                      ["フリーランス・小規模スタジオ", "¥3 万〜10 万", "1〜2 週間", "支給素材とストックからの編集、1 フォーマット"],
                      ["AI 専業スタジオ", "¥10 万〜50 万。高級 AI ブランド CM は ¥50 万〜150 万", "1〜2 週間", "生成 AI を使った制作、人による監修"],
                      ["制作代行（Kaizen Ad）", "¥5 万〜 / 本", "5 営業日", "発注 5 分、テンプレートベースの制作"],
                      ["AI CM スタジオ（Spot）", "約 ¥2,400 / スポット（Team）", "当日", "生成実写・実際のプロダクト UI・ナレーション・BGM・3 パターン × 3 フォーマット"]],
             "cap": "出典：[動画幹事](https://douga-kanji.com/posts/commercial-price)、[0120.co.jp](https://0120.co.jp/blog/video-33/)、[movieimpact](https://movieimpact.net/columns/2026-04-05-ai-video-production-cost-2026-latest-guide)、[Kaizen Platform](https://kaizenplatform.com/contents/video-advertising-costs)、[Spot の料金](/ja/pricing/)。"},
            {"type": "table", "h": "参考：大手の生成 AI CM サービス", "cols": ["サービス", "価格", "出典"],
             "rows": [["CyberAgent「ブランド 300 万動画」", "3 本で ¥300 万、1.5〜2 週間", "[CyberAgent](https://www.cyberagent.co.jp/news/detail/id=32619)"],
                      ["制作会社の AI 活用プラン（VIDWEB ほか）", "広告・CM ¥50 万〜300 万", "[VIDWEB](https://vidweb.co.jp/price/)"]]},
            {"type": "prose", "h": "価格を左右するもの", "paras": [
                "CM の費用を最も大きく動かすのは次の 4 つです。",
                ["**画面に映る人。** 実在のタレントはキャスティング・肖像権・撮影日が必要です。合成の人物なら 3 つとも不要になります。",
                 "**ロケと撮影クルー。** 撮影日は制作会社の見積で最大の項目です。生成映像には撮影日がありません。",
                 "**フォーマットとバージョン。** 制作会社は縦横比ごと、バリエーションごとに追加費用を請求します。AI スタジオは同じブリーフから生成します。",
                 "**修正。** 日をまたぐフィードバックの往復は工数で請求されます。言葉での再レンダリングは数分です。"],
                "媒体費は常に別です。関東キー局の 15 秒枠は 1 回 ¥30 万〜100 万、YouTube は 1 視聴 ¥3〜20、TikTok の CPM は ¥400〜1,000。小規模キャンペーンでは制作費のほうが小さくなることが多く、内製化が進む理由です。"]},
            {"type": "facts", "h": "覚えておきたい数字", "items": [
                {"n": "¥60 万", "k": "国内の Web 動画広告の発注額の中央値。", "src": "0120.co.jp", "url": "https://0120.co.jp/blog/video-33/"},
                {"n": "¥100〜500 万", "k": "テレビ CM の制作費の相場（タレント費別）。", "src": "動画幹事", "url": "https://douga-kanji.com/posts/commercial-price"},
                {"n": "約 ¥2,400", "k": "Spot の Team プランでの 1 スポット（9 ファイル）。", "src": "Spot の料金", "url": "/ja/pricing/"}]},
        ],
        "faq": [("媒体費は含まれますか？", "含まれません。上記はすべて制作費のみです。媒体費は各プラットフォームか代理店から別途請求されます。"),
                ("なぜこれほど幅があるのですか？", "タレント・ロケ・クルーです。実在の人物が実在の場所で映るスポットは、ストックや生成映像で作るものの 10 倍かかります。"),
                ("AI 動画が安いのは品質が低いからですか？", "安いのは撮影日・クルー・追加請求がないからです。品質はツール次第で、Spot は動画化の前にすべてのカットを検品し、実際のプロダクト UI を合成します。AI 動画が不自然に見える原因の多くはここです。"),
                ("小規模な SaaS は動画広告にいくら予算を取るべきですか？", "国内のアプリ・SaaS チームは、スケール前のクリエイティブテストに月 ¥10〜30 万を使うのが一般的です。AI 制作なら、その大半を媒体費に回せます。")],
        "related": [("Spot と制作会社", "compare/spot-vs-agency"), ("料金", "pricing"), ("動画広告の最適な尺", "guides/how-long-should-a-video-ad-be")],
    })


# --------------------------------------------------------------------------- specs
def specs(lang):
    rows_en = [["YouTube bumper", "16:9", "6 s (fixed)", "Non-skippable"], ["YouTube skippable in-stream", "16:9 (9:16 for Shorts)", "12 s+; 15–30 s typical", "Skippable after 5 s"], ["YouTube non-skippable in-stream", "16:9", "15 s (20 s in some markets)", ""], ["YouTube Shorts ads", "9:16", "Up to 60 s; 15 s typical", "Vertical"], ["TikTok in-feed", "9:16", "5–60 s; 9–15 s recommended", "Sound on"], ["Instagram / Facebook Reels", "9:16", "Under 30 s recommended", "Safe zones for UI overlays"], ["Instagram / Facebook feed", "1:1 or 4:5", "Under 15 s recommended", ""], ["LinkedIn video ads", "16:9, 1:1, 9:16", "Under 15 s recommended for awareness", "Captions on"], ["CTV / OTT", "16:9, 1080p+", "15 s or 30 s", "Loudness-normalized audio"]]
    rows_ja = [["YouTube バンパー", "16:9", "6 秒（固定）", "スキップ不可"], ["YouTube スキップ可能インストリーム", "16:9（ショートは 9:16）", "12 秒以上。15〜30 秒が一般的", "5 秒後にスキップ可"], ["YouTube スキップ不可インストリーム", "16:9", "15 秒（一部地域 20 秒）", ""], ["YouTube ショート広告", "9:16", "最大 60 秒。15 秒が一般的", "縦型"], ["TikTok インフィード", "9:16", "5〜60 秒。9〜15 秒推奨", "音声オン前提"], ["Instagram / Facebook リール", "9:16", "30 秒未満推奨", "UI 重なりのセーフゾーン"], ["Instagram / Facebook フィード", "1:1 または 4:5", "15 秒未満推奨", ""], ["LinkedIn 動画広告", "16:9・1:1・9:16", "認知目的は 15 秒未満推奨", "字幕オン"], ["CTV / 運用型テレビ CM", "16:9・1080p 以上", "15 秒または 30 秒", "ラウドネス正規化"]]
    links = "[Google Ads Help](https://support.google.com/google-ads/answer/2375464) · [TikTok Ads Manager](https://ads.tiktok.com/help/) · [Meta Ads Guide](https://www.facebook.com/business/ads-guide) · [LinkedIn Marketing](https://www.linkedin.com/help/lms)"
    if lang == "en":
        return _g("en", "video-ad-specs-2026", {
            "title": "Video ad specs 2026 — lengths, aspect ratios and formats by platform",
            "desc": "Video ad specs for 2026 in one table: YouTube bumper, in-stream and Shorts, TikTok, Reels, feed, LinkedIn and CTV. Lengths, aspect ratios and what to watch for, with links to each platform’s current spec page.",
            "h1": "Video ad specs, 2026.", "lede": "The one table to check before you brief. Platforms revise limits, so every row links to the source; lengths marked “typical” are what performs, not the maximum.",
            "blocks": [
                {"type": "answer", "q": "What are the standard video ad specs in 2026?",
                 "a": "Three aspect ratios cover almost every placement: **16:9** for YouTube in-stream and CTV, **9:16** for Shorts, Reels and TikTok, and **1:1** (or 4:5) for feed. Three lengths cover almost every objective: **6 seconds** for bumpers, **15 seconds** as the default for paid social and in-stream, **30 seconds** for CTV and storytelling. Spot exports every spot in all three ratios."},
                {"type": "table", "h": "Specs by placement", "cols": ["Placement", "Aspect ratio", "Length", "Notes"], "rows": rows_en, "cap": "Check the current platform pages before delivery: " + links + "."},
                {"type": "prose", "h": "Production rules that survive spec changes", "paras": [
                    ["**Brand in the first 2 seconds.** Skippable and scroll placements decide in that window.",
                     "**Design for sound off, deliver with sound on.** Captions or on-screen copy carry the message; the voiceover and sound logo reward the viewer who unmutes.",
                     "**Keep UI overlays out of the safe zones.** Vertical placements cover the bottom 20–25% and right edge with platform controls.",
                     "**One message per 6 seconds.** Bumpers get one; a 15-second spot gets hook, product, proof, CTA; a 30-second spot gets room for a story.",
                     "**Export all three ratios from one master.** Re-cropping a 16:9 for 9:16 loses the subject; generate the vertical as its own composition."]]},
            ],
            "faq": [("What resolution should I deliver?", "1080p minimum for all placements; 4K for CTV when the platform accepts it. Spot exports 1080p on all paid plans and 4K on Business."),
                    ("Do I need captions?", "Yes for feed and vertical placements, where most views start muted. Burn them in or upload a caption file where the platform supports it."),
                    ("How do I get all formats from one brief?", "With Spot, every spot is generated in 16:9, 9:16 and 1:1 as separate compositions, so nothing is cropped.")],
            "related": [("How long should a video ad be?", "guides/how-long-should-a-video-ad-be"), ("YouTube bumper ads", "use-cases/youtube-bumper-ads"), ("App install ads", "use-cases/app-install-ads")],
        })
    return _g("ja", "video-ad-specs-2026", {
        "title": "動画広告の入稿規定 2026｜プラットフォーム別の尺・アスペクト比・フォーマット",
        "desc": "2026 年の動画広告の仕様を 1 つの表に：YouTube バンパー・インストリーム・ショート、TikTok、リール、フィード、LinkedIn、CTV。尺、アスペクト比、注意点と、各プラットフォームの最新仕様ページへのリンク。",
        "h1": "動画広告の入稿規定、2026 年版。", "lede": "ブリーフの前に確認する 1 枚の表。プラットフォームは上限を改定するので、各行に出典を付けています。「一般的」と書いた尺は上限ではなく、効く長さです。",
        "blocks": [
            {"type": "answer", "q": "2026 年の動画広告の標準的な仕様は？",
             "a": "3 つのアスペクト比でほぼすべての配信面を賄えます。YouTube インストリームと CTV は **16:9**、ショート・リール・TikTok は **9:16**、フィードは **1:1**（または 4:5）。尺は 3 つでほぼすべての目的を賄えます。バンパーは **6 秒**、有料ソーシャルとインストリームの標準は **15 秒**、CTV とストーリー訴求は **30 秒**。Spot はすべてのスポットを 3 つの比率で書き出します。"},
            {"type": "table", "h": "配信面別の仕様", "cols": ["配信面", "アスペクト比", "尺", "注意点"], "rows": rows_ja, "cap": "入稿前に各プラットフォームの最新ページを確認してください：" + links + "。"},
            {"type": "prose", "h": "仕様が変わっても残る制作ルール", "paras": [
                ["**最初の 2 秒でブランドを。** スキップ可能枠とスクロール面はこの窓で判断されます。",
                 "**音なしで設計し、音ありで納品する。** 字幕と画面上のコピーがメッセージを運び、ナレーションとサウンドロゴはミュートを解除した人への報酬です。",
                 "**セーフゾーンに UI を重ねない。** 縦型面は下 20〜25% と右端がプラットフォームの UI で隠れます。",
                 "**6 秒に 1 メッセージ。** バンパーは 1 つ、15 秒はフック・プロダクト・証拠・CTA、30 秒はストーリーの余地。",
                 "**3 つの比率は 1 つのマスターから、別々に組む。** 16:9 を 9:16 に切り抜くと被写体が失われます。縦型は独立した構図として生成します。"]]},
        ],
        "faq": [("解像度はどうすべきですか？", "全配信面で 1080p 以上。CTV はプラットフォームが受け付ければ 4K。Spot は有料プランで 1080p、Business で 4K を書き出します。"),
                ("字幕は必要ですか？", "フィードと縦型面では必要です。大半の視聴がミュートで始まります。焼き込むか、対応プラットフォームでは字幕ファイルをアップロードしてください。"),
                ("1 つのブリーフから全フォーマットを作るには？", "Spot では、すべてのスポットが 16:9・9:16・1:1 の別々の構図として生成されるので、切り抜きは発生しません。")],
        "related": [("動画広告の最適な尺", "guides/how-long-should-a-video-ad-be"), ("YouTube バンパー広告", "use-cases/youtube-bumper-ads"), ("アプリ獲得広告", "use-cases/app-install-ads")],
    })


# --------------------------------------------------------------------------- length
def length(lang):
    if lang == "en":
        return _g("en", "how-long-should-a-video-ad-be", {
            "title": "How long should a video ad be? 6, 15 or 30 seconds, by platform and objective",
            "desc": "How long a video ad should be in 2026: 6 seconds for reach bumpers, 15 seconds as the default for paid social and YouTube, 30 seconds for CTV and storytelling. Rules by objective, with platform sources.",
            "h1": "How long should<br>a video ad be?",
            "lede": "Fifteen seconds, unless you have a reason. Here are the reasons, by objective and platform.",
            "blocks": [
                {"type": "answer", "q": "How long should a video ad be?",
                 "a": "Default to **15 seconds**. Use **6 seconds** when the objective is reach or frequency and the message is a single line (YouTube bumpers). Use **30 seconds** when the placement is non-skippable (CTV, some in-stream) and the story needs a setup. Anything longer belongs in organic or retargeting, not cold paid media."},
                {"type": "table", "h": "Length by objective", "cols": ["Objective", "Length", "Structure", "Where"],
                 "rows": [["Reach and frequency", "6 s", "One message, brand by second 2, sound logo", "YouTube bumpers, pre-roll"], ["Consideration, app installs, SaaS demo", "15 s", "Hook 0–3, product 3–10, proof 10–13, CTA 13–15", "Shorts, Reels, TikTok, in-stream, feed"], ["Brand storytelling, CTV", "30 s", "Setup, product in use, payoff, CTA", "CTV / OTT, non-skippable in-stream"], ["Retargeting and product education", "30–60 s", "Objection, answer, proof, CTA", "Feed, retargeting placements"]]},
                {"type": "prose", "h": "Three rules", "paras": [
                    ["**The hook does not scale with length.** Two seconds to earn the view is the rule at every length. A 30-second spot with a slow open loses the same viewers a 15-second one does.",
                     "**Cut for the placement, not from the master.** A 6-second bumper is a different composition from a 15-second spot, not the first six seconds of it.",
                     "**Test hooks before testing lengths.** Three openings on the same 15-second spot tell you more than one opening at three lengths. Spot ships three intro patterns per spot for this reason."]]},
            ],
            "faq": [("Is 15 seconds too short for B2B?", "No. It is enough for one problem, one product moment and one proof. Save the detail for the landing page and retargeting."),
                    ("Should I make a 6-second version of every spot?", "If you run YouTube, yes: bumpers are the cheapest reach. Spot’s bumper use case generates 6-second variations alongside the 15-second spot."),
                    ("Do vertical ads need to be shorter?", "Usually. Scroll placements reward 9–15 seconds; TikTok recommends 9–15 seconds for in-feed.")],
            "related": [("Video ad specs 2026", "guides/video-ad-specs-2026"), ("YouTube bumper ads", "use-cases/youtube-bumper-ads"), ("A/B testing at scale", "use-cases/ab-testing-at-scale")],
        })
    return _g("ja", "how-long-should-a-video-ad-be", {
        "title": "動画広告の最適な尺は何秒？｜6 秒・15 秒・30 秒を目的と配信面で選ぶ",
        "desc": "2026 年の動画広告の尺の選び方：リーチ目的のバンパーは 6 秒、有料ソーシャルと YouTube の標準は 15 秒、CTV とストーリー訴求は 30 秒。目的別のルールとプラットフォームの出典。",
        "h1": "動画広告の尺は、<br>何秒がいい？",
        "lede": "理由がなければ 15 秒。その「理由」を、目的と配信面ごとに整理します。",
        "blocks": [
            {"type": "answer", "q": "動画広告の尺は何秒にすべきですか？",
             "a": "標準は **15 秒**。目的がリーチやフリークエンシーで、メッセージが 1 行なら **6 秒**（YouTube バンパー）。配信面がスキップ不可（CTV、一部のインストリーム）で、ストーリーに前振りが要るなら **30 秒**。それより長いものはオーガニックやリターゲティング向けで、コールドな有料媒体には向きません。"},
            {"type": "table", "h": "目的別の尺", "cols": ["目的", "尺", "構成", "配信面"],
             "rows": [["リーチ・フリークエンシー", "6 秒", "1 メッセージ、2 秒目までにブランド、サウンドロゴ", "YouTube バンパー、プリロール"], ["比較検討、アプリ獲得、SaaS デモ", "15 秒", "フック 0–3、プロダクト 3–10、証拠 10–13、CTA 13–15", "ショート、リール、TikTok、インストリーム、フィード"], ["ブランドストーリー、CTV", "30 秒", "前振り、使用シーン、オチ、CTA", "CTV / OTT、スキップ不可インストリーム"], ["リターゲティング、商品理解", "30〜60 秒", "反論、回答、証拠、CTA", "フィード、リターゲティング面"]]},
            {"type": "prose", "h": "3 つのルール", "paras": [
                ["**フックは尺に比例しない。** 視聴を勝ち取る 2 秒はどの尺でも同じ。出だしの遅い 30 秒は、15 秒と同じだけ視聴者を失います。",
                 "**マスターから切るのではなく、配信面に合わせて組む。** 6 秒バンパーは 15 秒スポットの最初の 6 秒ではなく、別の構図です。",
                 "**尺の前にフックをテストする。** 同じ 15 秒スポットの 3 つの冒頭は、3 つの尺の 1 つの冒頭より多くを教えてくれます。Spot が 1 スポットに 3 つのイントロ案を付けるのはそのためです。"]]},
        ],
        "faq": [("B2B に 15 秒は短すぎませんか？", "短すぎません。1 つの課題、1 つのプロダクトの瞬間、1 つの証拠には十分です。詳細はランディングページとリターゲティングに回します。"),
                ("すべてのスポットに 6 秒版を作るべきですか？", "YouTube を使うなら作るべきです。バンパーは最も安いリーチです。Spot のバンパー用途では 15 秒スポットと並行して 6 秒案を生成します。"),
                ("縦型広告は短くすべきですか？", "多くの場合そうです。スクロール面は 9〜15 秒が効き、TikTok はインフィードに 9〜15 秒を推奨しています。")],
        "related": [("動画広告の入稿規定 2026", "guides/video-ad-specs-2026"), ("YouTube バンパー広告", "use-cases/youtube-bumper-ads"), ("A/B テストの量産", "use-cases/ab-testing-at-scale")],
    })


# --------------------------------------------------------------------------- listicle
def best(lang):
    c = COMPETITORS
    if lang == "en":
        rows = [["**Spot**", "Finished commercials for in-house teams", "$99 (6 spots); Team $399 (25 spots)", "Spot = 9 files", "Live-action + real product UI + voice + music, 3 patterns × 3 formats, same day", "Not for creator-testimonial UGC at volume"],
                [f"[Creatify]({c['creatify']['url']})", "UGC avatar ads for DTC and e-commerce", "$39 (100 credits); Pro $99", "Credits, 5 per 15 s", "Fast, cheap variants; product-link-to-video; API", "One format per render; avatar look"],
                ["Arcads (pricing in-app)", "AI-actor UGC for performance marketers", "≈ $110 list, $77 promo", "800 credits per actor-minute", "Large actor library; unlimited seats on Pro", "No free plan; pricing not public"],
                [f"[HeyGen]({c['heygen']['url']})", "Avatars, translation, explainers", "$29 (600 credits); Business $149 + seats", "Credits per minute", "Best avatars and dubbing; Video Agent", "Presenter format, not a commercial"],
                [f"[Waymark]({c['waymark']['url']})", "Local TV and CTV spots for media sellers", "$399 (2 finalized videos)", "Finalized downloads", "Broadcast workflow; station white-label", "2 videos a month at entry"],
                [f"[Poolday]({c['poolday']['url']})", "High-volume UGC for apps and games", "$1,250 (first month $500)", "Dollar credits", "Onboarding; enterprise terms; $5–25 per video", "Sales-assisted; high entry price"],
                ["[MakeUGC](https://www.makeugc.ai/pricing)", "UGC avatar videos", "$59; Pro $149", "Credits (per-video not disclosed)", "Product-in-hand shots; API tiers", "Credits per video undisclosed"],
                ["[Pencil](https://www.trypencil.com/pricing)", "Ad generation for enterprise brands", "$14 (50 generations); Growth $55", "Generations", "Cheapest per generation; enterprise terms on Pro", "Static-leaning; video depth varies"],
                ["[AdCreative.ai](https://www.adcreative.ai/)", "Static and product-video creatives", "$39 (10 downloads); Pro $249", "Downloads", "Large template library; scoring", "Credits halved in 2026 at same price"],
                ["[Predis](https://predis.ai/pricing/)", "Social posts and short ads for SMB", "$24 (1,300 credits)", "Credits", "Unlimited seats; very low price", "SMB-grade output"]]
        return _g("en", "best-ai-video-ad-generators-2026", {
            "title": "Best AI video ad generators in 2026 — 10 tools compared by output, price and fit",
            "desc": "The best AI video ad generators in 2026, compared honestly: Spot, Creatify, Arcads, HeyGen, Waymark, Poolday, MakeUGC, Pencil, AdCreative.ai and Predis. Entry price, metering unit, what each produces and who it suits.",
            "h1": "The best AI video ad<br>generators in 2026.",
            "lede": "Ten tools, one table, no affiliate links. We make one of them, so we say where each of the others is the better choice. Prices checked on " + PRICE_DATE + " and linked to each vendor.",
            "blocks": [
                {"type": "answer", "q": "What is the best AI video ad generator in 2026?",
                 "a": "It depends on what you need to ship. For **finished commercials** with live-action, your real product UI and multiple formats, **Spot**. For **UGC avatar ads at volume**, **Creatify** or **Arcads**. For **presenter videos and dubbing**, **HeyGen**. For **local TV spots sold by media teams**, **Waymark**. For **hundreds of performance videos a month with onboarding**, **Poolday**. The table below shows the entry price, the metering unit and the trade-offs of each."},
                {"type": "table", "h": "Ten AI video ad tools, side by side", "cols": ["Tool", "Best for", "Entry price / month", "Unit", "Strengths", "Trade-offs"], "hl_col": 0, "rows": rows,
                 "cap": "Prices as of " + PRICE_DATE + ", USD, monthly billing. Arcads and MakeUGC per-video figures are third-party or undisclosed."},
                {"type": "prose", "h": "How we ranked", "paras": [
                    "We sorted by the job, not by a score. The four questions that decide the right tool:",
                    ["**What is the output?** A talking avatar, a template edit, or a commercial with generated footage and your real product.",
                     "**What is the unit?** Credits per second, avatar minutes, downloads, or finished spots. Compare cost per finished, usable video, not per credit.",
                     "**Who reviews it?** Tools with a brand kit, do-not-say list and approval flow fit teams with legal review.",
                     "**How many formats per render?** One means re-rendering for every placement; three means one brief covers YouTube, vertical and feed."],
                    "We update this page every eight to twelve weeks. Vendors change credit allowances at the same price often — AdCreative.ai halved Professional credits in 2026, HeyGen raised Video Agent consumption in July 2026 — so check the linked pages before buying."]},
            ],
            "faq": [("Which tool is cheapest per video?", "Predis and Pencil are cheapest per generation for simple social output. Among commercial-grade tools, Spot’s Team plan is $16 per spot with nine files, versus $87–200 per finalized video on Waymark."),
                    ("Which tools have a free plan?", "Spot (1 spot a month), Creatify (10 credits), HeyGen (3 videos), Pencil (6 ads), Predis and Captions have free tiers. Arcads and Poolday do not."),
                    ("Which is best for Japanese-language ads?", "Spot generates scripts and voiceover in Japanese with a pronunciation guide. HeyGen supports Japanese dubbing. Most UGC tools are English-first.")],
            "related": [("All comparisons", "compare"), ("Pricing", "pricing"), ("Cost of a 15-second commercial", "guides/how-much-does-a-15-second-commercial-cost")],
        })
    rows = [["**Spot**", "内製チーム向けの完成 CM", "¥14,800（6 スポット）、Team ¥59,800（25 スポット）", "スポット＝9 ファイル", "実写＋実際のプロダクト UI＋音声＋BGM、3 パターン × 3 フォーマット、当日", "クリエイター体験談型 UGC の量産には不向き"],
            ["[RICHKA（リチカ）](https://it-trend.jp/advertising_tool/21126/price)", "テンプレート型の広告動画 SaaS", "月額定額・要問合せ", "本数無制限", "1,400 以上のフォーマット、代理店・内製の実績 400 社", "生成 AI 型ではなくテンプレート編集"],
            ["[Video BRAIN](https://video-b.com/plan/)", "企業の広報・研修・広告の自動編集", "要問合せ（月 ¥15 万〜との情報）", "会社単位・年契約", "800 万点の素材、本数無制限", "年契約、価格帯が高め"],
            ["[Kaizen Ad](https://kaizenplatform.com/contents/video-advertising-costs)", "制作代行＋運用改善", "¥5 万〜 / 本", "本", "発注 5 分、5 営業日納品、30,000 本の実績", "ツールではなく制作サービス"],
            ["[NoLang](https://no-lang.com/pricing)", "テキスト・PDF から解説・縦型動画", "¥2,980、Premium ¥7,980", "1 分約 100 クレジット", "日本語ネイティブ、最安の入口", "広告 CM というより解説動画"],
            [f"[Creatify]({c['creatify']['url']})", "D2C・EC 向け UGC アバター広告", "$39（100 クレジット）、Pro $99", "クレジット、15 秒 5", "速く安いバリエーション、商品リンクから動画化、日本語サイトあり", "1 回の生成で 1 フォーマット、アバター調"],
            [f"[HeyGen]({c['heygen']['url']})", "アバター・翻訳・解説", "$29（600 クレジット）", "分あたりクレジット", "最良のアバターと吹き替え、日本語対応", "プレゼンター形式で CM ではない"],
            ["Arcads（料金はアプリ内）", "運用型マーケター向け AI 俳優 UGC", "約 $110（キャンペーン $77）", "俳優 1 分 800 クレジット", "豊富な俳優ライブラリ", "無料なし、英語中心、価格非公開"],
            [f"[Waymark]({c['waymark']['url']})", "放送局・メディア営業向けのローカル CM", "$399（完成 2 本）", "完成本数", "放送ワークフロー、局向けホワイトラベル", "入口で月 2 本、英語圏向け"],
            ["CyberAgent「ブランド 300 万動画」", "大手向けの生成 AI テレビ CM", "3 本 ¥300 万", "案件", "テレビ CM 品質、1.5〜2 週間", "SaaS ではなく制作サービス"]]
    return _g("ja", "best-ai-video-ad-generators-2026", {
        "title": "AI 動画広告ツール おすすめ 10 選（2026 年）｜成果物・料金・向き不向きで比較",
        "desc": "2026 年の AI 動画広告・CM 制作ツールを公正に比較：Spot、RICHKA、Video BRAIN、Kaizen Ad、NoLang、Creatify、HeyGen、Arcads、Waymark、CyberAgent。入口価格、課金単位、できあがるもの、向いているチーム。",
        "h1": "AI 動画広告ツール<br>おすすめ 10 選（2026 年）。",
        "lede": "10 のツールを 1 つの表に。アフィリエイトリンクはありません。Spot は私たちの製品なので、他のツールのほうが良い場面も明記します。価格は " + PRICE_DATE + " に確認し、各社のページにリンクしています。",
        "blocks": [
            {"type": "answer", "q": "2026 年、AI 動画広告ツールのおすすめは？",
             "a": "何を出したいかで決まります。実写・実際のプロダクト UI・複数フォーマットの**完成 CM** なら **Spot**。テンプレートで社内の動画を量産するなら **RICHKA** か **Video BRAIN**。ツールではなく**制作を任せたい**なら **Kaizen Ad**。**UGC アバター広告の量産**なら **Creatify** か **Arcads**。**プレゼンター動画と吹き替え**なら **HeyGen**。下の表に入口価格・課金単位・トレードオフをまとめました。"},
            {"type": "table", "h": "10 のツールを並べて比較", "cols": ["ツール", "向いている用途", "入口価格 / 月", "課金単位", "強み", "トレードオフ"], "hl_col": 0, "rows": rows,
             "cap": PRICE_DATE + " 時点。海外ツールは USD 月払い。RICHKA・Video BRAIN の価格は第三者情報、Arcads はアプリ内のみ公開。"},
            {"type": "prose", "h": "選び方", "paras": [
                "スコアではなく、仕事で並べました。ツールを決める 4 つの問い：",
                ["**成果物は何か。** 話すアバターか、テンプレート編集か、生成映像と実際のプロダクトを使った CM か。",
                 "**単位は何か。** 秒あたりクレジット、アバター分数、ダウンロード数、完成スポット数。クレジット単価ではなく、使える完成動画 1 本あたりで比べる。",
                 "**誰が確認するか。** ブランドキット・禁止語リスト・承認フローがあるツールは、法務確認のあるチームに向く。",
                 "**1 回の生成で何フォーマットか。** 1 つなら配信面ごとに再生成、3 つなら 1 つのブリーフで YouTube・縦型・フィードを賄える。"],
                "このページは 8〜12 週ごとに更新します。同じ価格でクレジット付与を減らす改定が多く（AdCreative.ai は 2026 年に Professional のクレジットを半減、HeyGen は 2026 年 7 月に Video Agent の消費を増加）、購入前にリンク先を確認してください。"]},
        ],
        "faq": [("動画 1 本あたり最も安いのは？", "解説動画なら NoLang、SNS 投稿なら Predis や Pencil が最安です。CM 品質のツールでは、Spot の Team が 1 スポット（9 ファイル）約 ¥2,400、Waymark は完成 1 本 $87〜200、Kaizen Ad は 1 本 ¥5 万〜です。"),
                ("無料プランがあるのは？", "Spot（月 1 スポット）、NoLang（3 本）、Creatify（10 クレジット）、HeyGen（3 本）に無料枠があります。Arcads・Poolday にはありません。RICHKA は無料トライアルがあります。"),
                ("日本語のナレーションに対応しているのは？", "Spot は日本語の台本とナレーションを読み仮名辞書付きで生成します。NoLang は日本語ネイティブ、HeyGen は日本語吹き替えに対応。UGC ツールの多くは英語中心です。")],
        "related": [("すべての比較", "compare"), ("料金", "pricing"), ("15 秒 CM の制作費用と相場", "guides/how-much-does-a-15-second-commercial-cost")],
    })


# --------------------------------------------------------------------------- copyright & compliance
def compliance(lang):
    if lang == "en":
        return _g("en", "ai-commercial-copyright-and-compliance", {
            "title": "AI-generated commercials: copyright, commercial use and ad compliance (2026)",
            "desc": "What marketing and legal teams need to know before running AI-generated video ads: who owns the output, commercial-use terms of video models, FTC and Japanese ad rules, and a checklist. Not legal advice.",
            "h1": "AI commercials:<br>copyright and compliance.",
            "lede": "The questions legal asks first, answered in plain language with sources. This is general information, not legal advice; confirm with counsel for your jurisdiction.",
            "blocks": [
                {"type": "answer", "q": "Can we legally run an AI-generated commercial?",
                 "a": "Yes, in the US and Japan, provided three things hold: the model’s terms allow commercial use of outputs (major providers do), the ad does not include third-party protected material or real people’s likenesses without permission, and the claims meet ordinary advertising law. The open question is ownership: purely AI-generated footage may not be copyrightable, so protect the brand assets you add (logo, product UI, script, sound logo) and your edit."},
                {"type": "table", "h": "The four questions", "cols": ["Question", "Where things stand (2026)", "What to do"],
                 "rows": [["Who owns the output?", "The US Copyright Office’s 2025 report holds that material generated purely by AI is not copyrightable, while human-authored contributions (script, selection, arrangement, edits) can be. Japan’s Agency for Cultural Affairs takes a similar creative-contribution view.", "Keep the human contributions on record: brief, script edits, selection of patterns, brand assets."],
                          ["Can we use it commercially?", "Commercial use of outputs is permitted under the standard terms of major video and voice model providers. Terms differ on training use and indemnity.", "Use tools that publish sub-processor terms and do not train on your assets."],
                          ["Is anything in it infringing?", "Risk sits in prompts that name real brands, characters, artists or people; generated people are synthetic in Spot.", "Never reference third-party IP in briefs; composite only your own product UI, logos and music you license."],
                          ["Are the claims compliant?", "FTC rules on substantiation and endorsements apply to AI ads exactly as to any ad. Japan’s Act against Unjustifiable Premiums and Misleading Representations (景品表示法) prohibits 優良誤認 and 有利誤認; stealth-marketing rules took effect October 2023.", "Substantiate every comparative or superlative; disclose sponsorship; avoid fabricated testimonials."]],
                 "cap": "Sources: [US Copyright Office, Copyright and Artificial Intelligence, Part 2 (2025)](https://www.copyright.gov/ai/) · [文化庁 AIと著作権に関する考え方 (2024)](https://www.bunka.go.jp/seisaku/chosakuken/aiandcopyright.html) · [FTC Endorsement Guides](https://www.ftc.gov/business-guidance/resources/ftcs-endorsement-guides-what-people-are-asking) · [消費者庁 景品表示法](https://www.caa.go.jp/policies/policy/representation/fair_labeling/)."},
                {"type": "prose", "h": "Pre-flight checklist", "paras": [[
                    "Brief contains no third-party brand names, characters, artists or real people.",
                    "Product UI on screen is your own screenshot or recording.",
                    "Music is licensed for advertising; the sound logo is yours.",
                    "Every comparative or superlative claim has a source on file.",
                    "Required disclosures (fees, risks, sponsorship) are on screen in every format.",
                    "An approver has signed off on the final version, and the version history is kept.",
                    "Where AI-generated content disclosure is required by a platform or regulator, it is present."]]},
                {"type": "prose", "h": "How Spot is built for this", "paras": [
                    "Spot never generates your product interface; it composites the real one. Generated people are synthetic and not based on real individuals. Templates avoid superlatives without a source, the brand kit holds do-not-say terms and required disclosures, and Team plans and above require an approver before download. Customer assets are not used to train models. See [brand safety](/brand-safety/)."]},
            ],
            "faq": [("Do we have to label the ad as AI-generated?", "Rules vary by platform and market. YouTube requires disclosure of realistic synthetic content in some cases; the EU AI Act introduces transparency duties for deepfake-style content. Check the platform’s current policy; Spot lets you add a disclosure line to the brand kit."),
                    ("Can competitors copy our AI-generated spot?", "The generated footage alone may be hard to protect, but the composite work — your script, product UI, logo, sound logo, arrangement — carries your rights and trademarks. Register the brand assets; keep the version history."),
                    ("Is voice cloning allowed?", "Only with the consent of the person whose voice is cloned. Spot uses synthetic voices that are not clones of real people unless you supply consent and the recording.")],
            "related": [("Brand safety", "brand-safety"), ("Fintech ads", "use-cases/fintech-ads"), ("Security", "security")],
        })
    return _g("ja", "ai-commercial-copyright-and-compliance", {
        "title": "AI 生成 CM の著作権・商用利用・景表法（2026 年）｜法務が最初に聞くこと",
        "desc": "AI 生成の動画広告を配信する前にマーケと法務が知っておくこと：生成物の権利は誰のものか、動画モデルの商用利用条件、景品表示法とステマ規制、チェックリスト。法的助言ではありません。",
        "h1": "AI CM の<br>著作権と景表法。",
        "lede": "法務が最初に聞く質問に、出典付きで平易に答えます。これは一般的な情報であり法的助言ではありません。最終判断は弁護士にご確認ください。",
        "blocks": [
            {"type": "answer", "q": "AI で生成した CM を配信しても法的に問題ありませんか？",
             "a": "日本でも米国でも、3 つの条件が揃えば問題ありません。モデルの利用規約が生成物の商用利用を認めていること（主要各社は認めています）、第三者の保護された素材や実在の人物の肖像を無断で含まないこと、そして表示が通常の広告規制を満たすこと。未確定なのは権利の帰属で、AI が純粋に生成した映像は著作物と認められない可能性があるため、自社で加えた要素（ロゴ・プロダクト UI・台本・サウンドロゴ）と編集を守ることが重要です。"},
            {"type": "table", "h": "4 つの問い", "cols": ["問い", "2026 年時点の状況", "やること"],
             "rows": [["生成物は誰のものか", "文化庁「AI と著作権に関する考え方」（2024 年 3 月）は、人の創作的寄与があれば著作物性を認め得るとする立場。米国著作権局の 2025 年報告も、純粋な AI 生成部分は保護されず、人の寄与（台本・選択・配置・編集）は保護され得るとしています。", "人の寄与を記録に残す：ブリーフ、台本の編集、パターンの選択、ブランド素材。"],
                      ["商用利用できるか", "主要な動画・音声モデルの標準規約は生成物の商用利用を認めています。学習利用や補償の条件は各社で異なります。", "再委託先の条件を公開し、素材を学習に使わないツールを使う。"],
                      ["何かを侵害していないか", "リスクは実在のブランド・キャラクター・アーティスト・人物を名指しするプロンプトにあります。Spot の人物は合成です。著作権法 30 条の 4 は学習段階の利用を扱い、生成・利用段階は通常の侵害判断です。", "ブリーフで第三者の IP に言及しない。合成するのは自社のプロダクト UI・ロゴ・許諾済みの音楽のみ。"],
                      ["表示は適法か", "景品表示法は優良誤認・有利誤認を禁止。2023 年 10 月からステマ規制（広告である旨の表示義務）。薬機法・金商法など業法は通常通り適用。", "比較・最上級表現には根拠を保管、広告であることを表示、体験談を捏造しない。"]],
             "cap": "出典：[文化庁「AI と著作権に関する考え方について」](https://www.bunka.go.jp/seisaku/chosakuken/aiandcopyright.html) · [消費者庁 景品表示法](https://www.caa.go.jp/policies/policy/representation/fair_labeling/) · [消費者庁 ステルスマーケティング規制](https://www.caa.go.jp/policies/policy/representation/fair_labeling/stealth_marketing/) · [US Copyright Office, Copyright and AI, Part 2 (2025)](https://www.copyright.gov/ai/)。"},
            {"type": "prose", "h": "配信前チェックリスト", "paras": [[
                "ブリーフに第三者のブランド名・キャラクター・アーティスト・実在の人物が含まれていない。",
                "画面上のプロダクト UI は自社のスクリーンショットか録画である。",
                "音楽は広告利用の許諾済み、サウンドロゴは自社のもの。",
                "比較・最上級の表現すべてに根拠資料がある。",
                "必要な開示（手数料・リスク・広告表示）が全フォーマットの画面上にある。",
                "承認者が最終版を承認し、バージョン履歴が保存されている。",
                "プラットフォームや規制で AI 生成の表示が必要な場合、表示がある。"]]},
            {"type": "prose", "h": "Spot の設計", "paras": [
                "Spot はプロダクトの画面を生成せず、実物を合成します。登場人物は合成で、実在の個人に基づきません。テンプレートは根拠のない最上級表現を避け、ブランドキットに禁止語と必須開示文を保持し、Team 以上ではダウンロード前に承認者の承認が必要です。お客様の素材はモデルの学習に使いません。[ブランドセーフ](/ja/brand-safety/)も参照。"]},
        ],
        "faq": [("AI 生成であることを表示する必要はありますか？", "プラットフォームと市場で異なります。YouTube は写実的な合成コンテンツの一部に開示を求め、EU の AI 法はディープフェイク型コンテンツに透明性義務を課します。各プラットフォームの最新ポリシーを確認してください。Spot ではブランドキットに開示文を追加できます。"),
                ("競合に AI 生成のスポットを真似されませんか？", "生成映像そのものは保護が難しい場合がありますが、台本・プロダクト UI・ロゴ・サウンドロゴ・構成を含む合成物にはお客様の権利と商標が及びます。ブランド素材は登録し、バージョン履歴を保管してください。"),
                ("音声のクローンは使えますか？", "本人の同意がある場合のみです。Spot は実在の人物のクローンではない合成音声を使います。同意と録音の提供があればクローンにも対応します。")],
        "related": [("ブランドセーフ", "brand-safety"), ("フィンテックの広告", "use-cases/fintech-ads"), ("セキュリティ", "security")],
    })


def hub(lang):
    gs = [cost(lang), specs(lang), length(lang), best(lang), compliance(lang)]
    items = [{"h": g["h1"].replace("<br>", " " if lang == "en" else ""), "p": g["lede"], "path": g["path"]} for g in gs]
    if lang == "en":
        return {"path": "guides", "crumbs": [], "eyebrow": "Guides",
                "title": "Spot guides — video ad costs, specs, length, tools and compliance",
                "desc": "Buying-side guides for marketing teams: what a 15-second commercial costs, video ad specs by platform, how long an ad should be, the best AI video ad generators, and copyright and compliance for AI ads.",
                "h1": "Guides for teams<br>that ship video ads.", "lede": "Sourced, dated, and updated every eight to twelve weeks.",
                "blocks": [{"type": "cards", "cls": "grid2", "items": items}]}
    return {"path": "guides", "crumbs": [], "eyebrow": "ガイド",
            "title": "Spot ガイド｜動画広告の費用・入稿規定・尺・ツール・法務",
            "desc": "マーケティングチーム向けの購買前ガイド：15 秒 CM の制作費用と相場、配信面別の入稿規定、最適な尺、AI 動画広告ツールの比較、AI 広告の著作権と景表法。",
            "h1": "動画広告を出すチームのための<br>ガイド。", "lede": "出典付き・日付付きで、8〜12 週ごとに更新します。",
            "blocks": [{"type": "cards", "cls": "grid2", "items": items}]}


def pages(lang):
    return [hub(lang), cost(lang), specs(lang), length(lang), best(lang), compliance(lang)]
