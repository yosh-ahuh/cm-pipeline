"""Comparison pages (/compare/*) and the alternatives hub. Facts are fair to the competitor and dated."""
from .common import COMPETITORS, SPOT_ROW, PRICE_DATE

CRUMB = {"en": [("Compare", "compare")], "ja": [("比較", "compare")]}

ROWS = {
    "en": [("Entry plan", "entry"), ("Mid plan", "mid"), ("Metering unit", "unit"), ("Per finished video", "per_video"), ("Free plan", "free"), ("What you get", "output"), ("Seats", "seats"), ("Positioning", "positioning")],
    "ja": [("入口プラン", "entry"), ("中位プラン", "mid"), ("課金単位", "unit"), ("完成動画 1 本あたり", "per_video"), ("無料プラン", "free"), ("できあがるもの", "output"), ("席", "seats"), ("ポジショニング", "positioning")],
}

# Per-competitor prose: when to choose them, when to choose SPOT.
CP = {
    "creatify": {
        "en": {"title": "SPOT vs Creatify — finished commercials vs UGC avatar ads (2026)",
               "desc": "SPOT vs Creatify compared on price, metering, output and fit. Creatify makes avatar UGC ads from $39 a month; SPOT makes full commercials with your real product UI, 3 patterns × 3 formats per spot, from $99.",
               "h1": "SPOT vs Creatify", "lede": "Two different products for two different jobs. Creatify is a fast UGC-style ad generator. SPOT is a commercial studio. Here is how they compare, with prices checked on " + PRICE_DATE + ".",
               "q": "Should I choose Creatify or SPOT?",
               "a": "Choose Creatify when you need many creator-style talking-avatar ads quickly and cheaply, especially for DTC and e-commerce on Meta and TikTok. Choose SPOT when you need a finished commercial with live-action shots, your real product interface, voiceover and music, delivered in three patterns and three formats per spot, and when brand and legal review are part of the workflow.",
               "choose_them": ["Creator-style testimonial ads with a talking avatar", "Very high volume of near-identical variants", "Lowest entry price ($39 a month)", "Product-link-to-video for e-commerce catalogs"],
               "choose_us": ["A commercial format: hook, product in use, proof, CTA, sound logo", "Real product UI composited in — never generated", "Nine files per spot across 16:9, 9:16 and 1:1", "Brand kit, pronunciation guide, approval flow for legal", "CTV and YouTube spots at 15 and 30 seconds"],
               "faq": [("Is Creatify cheaper than SPOT?", "Per talking-avatar video, yes: about $3.30–3.90 per 30-second render at list prices. Per finished commercial with nine files, SPOT’s Team plan works out to $16 per spot. They are not the same unit."),
                       ("Can I use both?", "Many teams do: Creatify for volume UGC variants, SPOT for the brand spot and the CTV or YouTube commercial."),
                       ("Does Creatify have a free plan?", "Creatify offers 10 free credits, about two watermarked ads. SPOT’s free plan is one watermarked spot a month.")]},
        "ja": {"title": "SPOT と Creatify の比較｜完成 CM と UGC アバター広告（2026 年）",
               "desc": "SPOT と Creatify を価格・課金単位・成果物・向き不向きで比較。Creatify は月額 $39 からのアバター UGC 広告、SPOT は実際のプロダクト UI を使った完成 CM を 1 スポット 3 パターン × 3 フォーマットで、月額 ¥14,800 から。",
               "h1": "SPOT と Creatify", "lede": "目的が違う 2 つの製品です。Creatify は速い UGC 風広告ジェネレーター、SPOT は CM スタジオ。" + PRICE_DATE + " 時点の価格で比較します。",
               "q": "Creatify と SPOT、どちらを選ぶべきですか？",
               "a": "Meta や TikTok 向けにクリエイター風のアバター広告を大量に安く作りたいなら Creatify。実写カット・実際のプロダクト画面・ナレーション・BGM を備えた完成 CM を、1 スポットあたり 3 パターン × 3 フォーマットで欲しい、そしてブランドと法務の確認がワークフローに含まれるなら SPOT です。",
               "choose_them": ["アバターが話すクリエイター風の体験談広告", "ほぼ同じバリエーションを大量に", "最も安い入口価格（月額 $39）", "EC カタログの商品リンクからの動画化"],
               "choose_us": ["CM の構成：フック・使用シーン・証拠・CTA・サウンドロゴ", "実際のプロダクト UI を合成。生成しない", "1 スポットで 16:9・9:16・1:1 の 9 ファイル", "ブランドキット・読み仮名辞書・法務向け承認フロー", "15 秒・30 秒の CTV・YouTube スポット"],
               "faq": [("Creatify のほうが安いですか？", "アバター動画 1 本あたりでは安く、公開価格で 30 秒あたり約 $3.3〜3.9 です。9 ファイルの完成 CM 1 本あたりでは SPOT の Team プランが約 ¥2,400。単位が違います。"),
                       ("両方使えますか？", "多くのチームがそうしています。量産の UGC バリエーションは Creatify、ブランドスポットや CTV・YouTube の CM は SPOT。"),
                       ("Creatify に無料プランはありますか？", "10 クレジット（透かし入り約 2 本）の無料枠があります。SPOT の無料プランは月 1 スポット（透かし入り）です。")]},
    },
    "arcads": {
        "en": {"title": "SPOT vs Arcads — AI actor UGC ads vs finished commercials (2026)",
               "desc": "SPOT vs Arcads: Arcads renders AI-actor UGC ads for performance marketers from about $110 a month with no free plan; SPOT produces full commercials with real product UI, 9 files per spot, from $99 with a free plan.",
               "h1": "SPOT vs Arcads", "lede": "Arcads is the performance marketer’s UGC engine. SPOT is the marketing team’s commercial studio. Arcads publishes pricing only inside the app, so its figures below are from third-party reviews checked on " + PRICE_DATE + ".",
               "q": "Should I choose Arcads or SPOT?",
               "a": "Choose Arcads if your creative is AI-actor UGC for Meta and TikTok and you want a large actor library and unlimited seats on the top plan. Choose SPOT if you need a finished commercial rather than a talking actor, want your real product interface on screen, and want three patterns in three formats per spot with a brand kit and approval flow.",
               "choose_them": ["AI-actor UGC for direct-response Meta and TikTok", "Large library of actors and voices", "Unlimited seats on the Pro plan", "Volume pricing above 40 videos a month"],
               "choose_us": ["Commercial format with live-action, product UI, music", "Free plan and a $99 entry point", "Nine files per spot for all placements", "Brand kit, pronunciation guide, legal approval", "CTV and YouTube spots"],
               "faq": [("Where does Arcads publish pricing?", "Inside the app after sign-up; its public /pricing page returned an error when checked. The figures here come from third-party reviews and may change."),
                       ("Which is cheaper per video?", "Arcads works out to roughly $11 per talking-actor video at list prices. SPOT is $16 per spot on Team, where a spot is nine files. Different units."),
                       ("Does Arcads have a free trial?", "No free plan was found. SPOT includes one watermarked spot a month free.")]},
        "ja": {"title": "SPOT と Arcads の比較｜AI 俳優の UGC 広告と完成 CM（2026 年）",
               "desc": "SPOT と Arcads：Arcads は運用型マーケター向けの AI 俳優 UGC 広告で月額約 $110 から、無料プランなし。SPOT は実際のプロダクト UI を使った完成 CM を 1 スポット 9 ファイルで、月額 ¥14,800 から、無料プランあり。",
               "h1": "SPOT と Arcads", "lede": "Arcads は運用型マーケターの UGC エンジン、SPOT はマーケティングチームの CM スタジオ。Arcads の料金はアプリ内でのみ公開されているため、以下の数値は " + PRICE_DATE + " 時点の第三者レビューによるものです。",
               "q": "Arcads と SPOT、どちらを選ぶべきですか？",
               "a": "Meta・TikTok 向けの AI 俳優 UGC が主なクリエイティブで、豊富な俳優ライブラリと上位プランの席無制限が欲しいなら Arcads。話す俳優ではなく完成した CM が必要で、実際のプロダクト画面を画面に出し、ブランドキットと承認フロー付きで 1 スポット 3 パターン × 3 フォーマットが欲しいなら SPOT です。",
               "choose_them": ["Meta・TikTok のダイレクトレスポンス向け AI 俳優 UGC", "豊富な俳優・音声ライブラリ", "Pro プランで席無制限", "月 40 本以上のボリューム価格"],
               "choose_us": ["実写・プロダクト UI・BGM を備えた CM 形式", "無料プランと月額 ¥14,800 の入口", "全配信面向けの 1 スポット 9 ファイル", "ブランドキット・読み仮名辞書・法務承認", "CTV・YouTube スポット"],
               "faq": [("Arcads の料金はどこで公開されていますか？", "登録後のアプリ内です。公開の料金ページは確認時にエラーを返しました。ここでの数値は第三者レビューによるもので、変わる可能性があります。"),
                       ("動画 1 本あたりはどちらが安いですか？", "Arcads は公開価格で俳優動画 1 本あたり約 $11。SPOT は Team で 1 スポット約 ¥2,400 で、1 スポットは 9 ファイルです。単位が違います。"),
                       ("Arcads に無料トライアルはありますか？", "無料プランは見つかりませんでした。SPOT は月 1 スポット（透かし入り）が無料です。")]},
    },
    "heygen": {
        "en": {"title": "SPOT vs HeyGen — avatar videos vs finished commercials (2026)",
               "desc": "SPOT vs HeyGen: HeyGen is an avatar and localization video platform from $29 a month, metered in credits per minute; SPOT produces finished commercials with live-action and real product UI, 9 files per spot, from $99.",
               "h1": "SPOT vs HeyGen", "lede": "HeyGen is excellent at what it does: presenter avatars, translation, and long-form explainer video. It is not a commercial format. Prices checked on " + PRICE_DATE + ".",
               "q": "Should I choose HeyGen or SPOT?",
               "a": "Choose HeyGen for presenter-led videos, multilingual dubbing, training and explainer content, or when you want a digital twin of a real spokesperson. Choose SPOT for paid-media commercials: a hook, live-action shots, your real product on screen, voiceover, music, and three patterns in three formats delivered the same day.",
               "choose_them": ["Presenter avatars and digital twins", "Translation and lip-synced dubbing", "Long-form explainer and training video", "Lowest entry price ($29 a month)"],
               "choose_us": ["Commercials for YouTube, Shorts, Reels, TikTok and CTV", "Live-action scenes, not a presenter on a background", "Real product UI composited in", "Nine files per spot, three hooks to test", "Brand kit, pronunciation guide, approval flow"],
               "faq": [("Can HeyGen make video ads?", "Yes — HeyGen markets an AI ad generator and Video Agent. The output is avatar-presenter style, one format per render, metered per minute (30–120 credits a minute for Video Agent as of July 2026). SPOT’s unit is a finished commercial in nine files."),
                       ("Which is cheaper?", "HeyGen’s Creator plan is $29 a month and works out to roughly $1–1.50 per avatar minute. SPOT starts at $99 for six spots. For presenter videos HeyGen is cheaper; for commercials the units are not comparable."),
                       ("Does SPOT support Japanese?", "Yes. Script and voiceover in Japanese and English, with a pronunciation guide for product names.")]},
        "ja": {"title": "SPOT と HeyGen の比較｜アバター動画と完成 CM（2026 年）",
               "desc": "SPOT と HeyGen：HeyGen は月額 $29 からのアバター・翻訳動画プラットフォームで、分あたりクレジット課金。SPOT は実写と実際のプロダクト UI を使った完成 CM を 1 スポット 9 ファイルで、月額 ¥14,800 から。",
               "h1": "SPOT と HeyGen", "lede": "HeyGen は得意分野で優れています。プレゼンター型アバター、翻訳、長尺の解説動画。ただし CM のフォーマットではありません。" + PRICE_DATE + " 時点の価格で比較します。",
               "q": "HeyGen と SPOT、どちらを選ぶべきですか？",
               "a": "プレゼンターが話す動画、多言語吹き替え、研修・解説コンテンツ、実在の広報担当者のデジタルツインが欲しいなら HeyGen。有料媒体向けの CM、つまりフック・実写カット・実際のプロダクト画面・ナレーション・BGM を 3 パターン × 3 フォーマットでその日のうちに欲しいなら SPOT です。",
               "choose_them": ["プレゼンター型アバターとデジタルツイン", "翻訳とリップシンク吹き替え", "長尺の解説・研修動画", "最も安い入口価格（月額 $29）"],
               "choose_us": ["YouTube・ショート・リール・TikTok・CTV 向けの CM", "背景の前のプレゼンターではなく、実写シーン", "実際のプロダクト UI を合成", "1 スポット 9 ファイル、テスト用の 3 フック", "ブランドキット・読み仮名辞書・承認フロー"],
               "faq": [("HeyGen で動画広告は作れますか？", "作れます。HeyGen は AI 広告ジェネレーターと Video Agent を提供しています。成果物はアバターが話す形式で、1 回の生成で 1 フォーマット、分単位のクレジット課金（Video Agent は 2026 年 7 月時点で 1 分 30〜120 クレジット）です。SPOT の単位は 9 ファイルの完成 CM です。"),
                       ("どちらが安いですか？", "HeyGen の Creator プランは月額 $29 で、アバター動画 1 分あたり約 $1〜1.5。SPOT は月額 ¥14,800 で 6 スポットから。プレゼンター動画なら HeyGen が安く、CM では単位が比較できません。"),
                       ("SPOT は日本語に対応していますか？", "対応しています。台本とナレーションは日本語・英語で、商品名の読み仮名辞書付きです。")]},
    },
    "waymark": {
        "en": {"title": "SPOT vs Waymark — AI commercials for marketing teams vs for media sellers (2026)",
               "desc": "SPOT vs Waymark: Waymark makes template-driven local TV and CTV spots for broadcasters from $399 a month for 2 finalized videos; SPOT makes live-action commercials with real product UI for in-house teams, 25 spots for $399.",
               "h1": "SPOT vs Waymark", "lede": "Waymark and SPOT both make commercials, and both start at $399 a month. Waymark sells to broadcasters and media sales teams; SPOT sells to the marketing team. Prices checked on " + PRICE_DATE + ".",
               "q": "Should I choose Waymark or SPOT?",
               "a": "Choose Waymark if you are a broadcaster, station group or media sales team producing local-advertiser spots from business data and stock, with CRM automations. Choose SPOT if you are a brand or in-house team that needs live-action commercials with your real product interface, three hooks per spot, and a volume of 25 spots a month rather than 2.",
               "choose_them": ["Local TV and CTV spots for small advertisers at scale", "Template and stock-driven production from business listings", "Sales-team workflows, CRM automations, white-label for stations", "Broadcast delivery built into the product"],
               "choose_us": ["Live-action generation and your real product UI", "25 spots for $399 versus 2 finalized videos", "Three patterns × three formats per spot", "Free plan and a $99 entry point", "Brand kit, pronunciation guide, approval flow"],
               "faq": [("Which is cheaper?", "At $399 a month, Waymark includes 2 finalized downloads (4 on an annual promotion), or roughly $87–200 per video. SPOT’s Team plan includes 25 spots at $399, or $16 per spot with nine files each."),
                       ("Does Waymark have a free plan?", "Waymark offers a 7-day trial without a card. SPOT offers one watermarked spot a month free."),
                       ("Which is better for CTV?", "Both export broadcast-format 16:9. Waymark’s templates suit local advertisers; SPOT’s generated live-action suits brand and product spots.")]},
        "ja": {"title": "SPOT と Waymark の比較｜マーケティングチーム向けと放送局向けの AI CM（2026 年）",
               "desc": "SPOT と Waymark：Waymark は放送局向けにテンプレート型のローカル TV・CTV スポットを月額 $399・完成 2 本で提供。SPOT は内製チーム向けに実写と実際のプロダクト UI の CM を、¥59,800 で 25 スポット。",
               "h1": "SPOT と Waymark", "lede": "どちらも CM を作り、どちらも月額 $399 前後から始まります。Waymark は放送局とメディア営業に、SPOT はマーケティングチームに売っています。" + PRICE_DATE + " 時点の価格で比較します。",
               "q": "Waymark と SPOT、どちらを選ぶべきですか？",
               "a": "放送局・局グループ・メディア営業チームで、事業者データとストック素材からローカル広告主のスポットを CRM 連携で量産するなら Waymark。ブランドや内製チームで、実際のプロダクト画面を使った実写 CM、1 スポット 3 フック、月 2 本ではなく 25 スポットが必要なら SPOT です。",
               "choose_them": ["小規模広告主向けのローカル TV・CTV スポットを大量に", "事業者情報とストック素材によるテンプレート制作", "営業チームのワークフロー、CRM 連携、局向けホワイトラベル", "放送納品が製品に組み込まれている"],
               "choose_us": ["実写生成と実際のプロダクト UI", "完成 2 本に対して ¥59,800 で 25 スポット", "1 スポット 3 パターン × 3 フォーマット", "無料プランと ¥14,800 の入口", "ブランドキット・読み仮名辞書・承認フロー"],
               "faq": [("どちらが安いですか？", "Waymark は月額 $399 に完成 2 本（年契約キャンペーンで 4 本）が含まれ、1 本あたり約 $87〜200。SPOT の Team は ¥59,800 に 25 スポットが含まれ、1 スポット（9 ファイル）約 ¥2,400 です。"),
                       ("Waymark に無料プランはありますか？", "カード不要の 7 日間トライアルがあります。SPOT は月 1 スポット（透かし入り）が無料です。"),
                       ("CTV にはどちらが向いていますか？", "どちらも放送フォーマットの 16:9 を書き出します。Waymark のテンプレートはローカル広告主向け、SPOT の生成実写はブランド・プロダクトのスポット向けです。")]},
    },
    "poolday": {
        "en": {"title": "SPOT vs Poolday — enterprise UGC volume vs finished commercials (2026)",
               "desc": "SPOT vs Poolday: Poolday sells high-volume UGC and performance video for apps and games from $1,250 a month with onboarding; SPOT delivers finished commercials with real product UI at $399 for 25 spots, self-serve.",
               "h1": "SPOT vs Poolday", "lede": "Poolday is a sales-assisted, high-volume video engine priced for performance teams spending heavily on apps and games. SPOT is a self-serve commercial studio. Prices checked on " + PRICE_DATE + ".",
               "q": "Should I choose Poolday or SPOT?",
               "a": "Choose Poolday if you need hundreds of performance videos a month for app or game campaigns, want one-to-one onboarding and custom workflows, and have a budget above $1,250 a month. Choose SPOT if you need finished commercials with your real product interface, want to start self-serve at $99 or $399, and value three hooks in three formats per spot with brand and legal controls.",
               "choose_them": ["Hundreds of UGC-style videos a month", "Dedicated onboarding and custom workflows", "Enterprise contracts with SSO, MSA and API from the start", "App and game performance creative at scale"],
               "choose_us": ["Finished commercials, not only performance UGC", "Self-serve from $99, Team at $399", "Real product UI, brand kit, approval flow", "Nine files per spot for every placement", "CTV and YouTube spots"],
               "faq": [("How does Poolday price?", "Business is $1,250 a month (first month $500) including $1,250 of credits, with extra credits billed at a higher rate; Enterprise starts at $2,500. Poolday states $5–25 per finished video."),
                       ("Which is cheaper?", "For a team making fewer than about 80 videos a month, SPOT’s Team or Business plans cost less. Above that, compare Poolday’s per-video rate against SPOT Business at $15 per extra spot."),
                       ("Does SPOT offer onboarding?", "Enterprise includes onboarding and a customer success manager; Business includes a shared Slack channel.")]},
        "ja": {"title": "SPOT と Poolday の比較｜エンタープライズ向け UGC 量産と完成 CM（2026 年）",
               "desc": "SPOT と Poolday：Poolday はアプリ・ゲーム向けの UGC・運用型動画を月額 $1,250 からオンボーディング付きで提供。SPOT は実際のプロダクト UI の完成 CM を ¥59,800 で 25 スポット、セルフサーブで。",
               "h1": "SPOT と Poolday", "lede": "Poolday は営業同伴で、アプリ・ゲームに大きく投資する運用チーム向けに価格設定された量産エンジン。SPOT はセルフサーブの CM スタジオ。" + PRICE_DATE + " 時点の価格で比較します。",
               "q": "Poolday と SPOT、どちらを選ぶべきですか？",
               "a": "アプリ・ゲームのキャンペーンで月に数百本の運用型動画が必要で、1 対 1 のオンボーディングとカスタムワークフローを望み、月 $1,250 以上の予算があるなら Poolday。実際のプロダクト画面を使った完成 CM が必要で、¥14,800 や ¥59,800 からセルフサーブで始めたく、1 スポット 3 フック × 3 フォーマットとブランド・法務の管理を重視するなら SPOT です。",
               "choose_them": ["月に数百本の UGC 風動画", "専任のオンボーディングとカスタムワークフロー", "最初から SSO・MSA・API 付きのエンタープライズ契約", "アプリ・ゲームの運用型クリエイティブの量産"],
               "choose_us": ["運用型 UGC だけでなく、完成 CM", "¥14,800 からセルフサーブ、Team は ¥59,800", "実際のプロダクト UI・ブランドキット・承認フロー", "全配信面向けの 1 スポット 9 ファイル", "CTV・YouTube スポット"],
               "faq": [("Poolday の料金体系は？", "Business は月額 $1,250（初月 $500）で $1,250 分のクレジット込み、追加クレジットは割高。Enterprise は $2,500 から。Poolday は完成動画 1 本 $5〜25 と明示しています。"),
                       ("どちらが安いですか？", "月 80 本未満のチームなら SPOT の Team か Business のほうが安くなります。それ以上は、Poolday の 1 本あたり単価と SPOT Business の追加スポット ¥2,200 を比べてください。"),
                       ("SPOT にオンボーディングはありますか？", "Enterprise にオンボーディングと CSM が含まれ、Business には Slack 共有チャンネルが含まれます。")]},
    },
}


def _competitor_page(lang, key):
    c = COMPETITORS[key]
    d = CP[key][lang]
    s = SPOT_ROW[lang]
    rows = [[label, s[f], c[f]] for label, f in ROWS[lang]]
    cap = (f"Prices as of {PRICE_DATE}. {c['name']} figures from [{c['name']} pricing]({c['url']})" + ("" if c["verified"] else " and third-party reviews (not verifiable on the vendor site)") + ". SPOT figures from [SPOT pricing](/pricing/).") if lang == "en" else \
          (f"{PRICE_DATE} 時点の価格。{c['name']} の数値は [{c['name']} の料金ページ]({c['url']})" + ("" if c["verified"] else " と第三者レビュー（ベンダーサイトでは確認不可）") + " から。SPOT の数値は [SPOT の料金](/ja/pricing/)から。")
    blocks = [
        {"type": "answer", "q": d["q"], "a": d["a"]},
        {"type": "table", "eyebrow": "Side by side" if lang == "en" else "比較表", "h": ("SPOT and " + c["name"] + " at a glance") if lang == "en" else ("SPOT と " + c["name"] + " の一覧"),
         "cols": ["", "SPOT", c["name"]], "hl_col": 1, "rows": rows, "cap": cap},
        {"type": "cards", "cls": "grid2", "items": [
            {"h": (f"Choose {c['name']} when" if lang == "en" else f"{c['name']} を選ぶ場面"), "p": " · ".join(d["choose_them"])},
            {"h": ("Choose SPOT when" if lang == "en" else "SPOT を選ぶ場面"), "p": " · ".join(d["choose_us"])}]},
    ]
    others = [k for k in COMPETITORS if k != key][:3]
    rel = [((f"SPOT vs {COMPETITORS[k]['name']}" if lang == "en" else f"SPOT と {COMPETITORS[k]['name']}"), f"compare/{k}") for k in others]
    rel.append(("All alternatives" if lang == "en" else "すべての比較", "compare"))
    return {"path": f"compare/{key}", "crumbs": CRUMB[lang], "eyebrow": "Compare" if lang == "en" else "比較",
            "title": d["title"], "desc": d["desc"], "h1": d["h1"], "lede": d["lede"], "updated": PRICE_DATE,
            "blocks": blocks, "faq": d["faq"], "related": rel,
            "jsonld": [{"@context": "https://schema.org", "@type": "ItemList", "name": d["h1"],
                        "itemListElement": [{"@type": "ListItem", "position": 1, "name": "SPOT"}, {"@type": "ListItem", "position": 2, "name": c["name"], "url": c["url"]}]}]}


def agency(lang):
    if lang == "en":
        return {"path": "compare/spot-vs-agency", "crumbs": CRUMB["en"], "eyebrow": "Compare",
                "title": "SPOT vs a production agency — cost, time and control for a 15-second spot",
                "desc": "SPOT compared with a video production agency: same-day vs about three weeks, $16 per spot vs $5,000–15,000, nine files vs one, and where an agency is still the right choice.",
                "h1": "SPOT vs an agency", "lede": "An agency is the right answer for a talent-led, high-concept campaign. For the weekly flow of product, performance and CTV spots, the numbers point the other way.",
                "blocks": [
                    {"type": "answer", "q": "When should a marketing team use SPOT instead of an agency?",
                     "a": "Use SPOT for the recurring creative: product spots, app and SaaS ads, bumpers, CTV cutdowns, A/B variants and localized versions. Use an agency for campaigns that need real talent, location shoots, original music or a big idea that will run for a year. Many teams keep the agency for the anchor campaign and move everything downstream of it to SPOT."},
                    {"type": "table", "h": "For one 15-second spot", "cols": ["", "Production agency", "SPOT (Team)"], "hl_col": 2,
                     "rows": [["Time to first cut", "About 3 weeks", "Same day"], ["Cost", "$5,000–15,000 (US); ¥500,000–3,000,000 (Japan)", "$16 per spot; $399 a month for 25"], ["Formats", "One; extra formats re-billed", "16:9, 9:16, 1:1 included"], ["Variants", "One; each extra is a change order", "Three intro patterns included"], ["Revisions", "Rounds over days", "Plain language, minutes, 0.25 spot"], ["Product UI", "Screen-recorded or mocked in post", "Your real UI composited automatically"], ["Talent and locations", "Real people, real places", "Synthetic people and generated scenes"], ["Original music", "Composed", "Licensed music bed and your sound logo"]],
                     "cap": "Agency ranges from published production-cost guides; see the [cost guide](/guides/how-much-does-a-15-second-commercial-cost/)."},
                    {"type": "cards", "cls": "grid2", "items": [
                        {"h": "Keep the agency for", "p": "Brand campaigns with real talent · location shoots · original scores · the yearly anchor idea · anything that needs a director’s eye on set"},
                        {"h": "Move to SPOT", "p": "Product and feature spots · app install and SaaS ads · bumpers and CTV cutdowns · A/B hooks and audience variants · Japanese and English versions of the same spot"}]},
                ],
                "faq": [("Is AI-generated video good enough for paid media?", "For product-led and message-led spots, yes. SPOT reviews every shot before animation and composites your real product, which is where most AI video fails. Talent-led emotional storytelling is still an agency job."),
                        ("What about the 1/400 claim?", "A $399 Team plan divided by 25 spots is $16 per spot. Against a $5,000–15,000 agency spot that is between 1/300 and 1/900; we round to about 1/400 for a mid-range agency spot."),
                        ("Can our agency use SPOT for us?", "Yes. Enterprise supports agency workspaces with white-label output and unlimited brands.")],
                "related": [("In-house teams", "use-cases/in-house-teams"), ("Cost of a 15-second commercial", "guides/how-much-does-a-15-second-commercial-cost"), ("Pricing", "pricing")]}
    return {"path": "compare/spot-vs-agency", "crumbs": CRUMB["ja"], "eyebrow": "比較",
            "title": "SPOT と制作会社の比較｜15 秒スポットの費用・納期・コントロール",
            "desc": "SPOT と動画制作会社を比較：当日と約 3 週間、1 スポット約 ¥2,400 と ¥50 万〜300 万、9 ファイルと 1 ファイル。そして制作会社が今も正解である場面。",
            "h1": "SPOT と制作会社", "lede": "タレント起用の高いコンセプトのキャンペーンには制作会社が正解です。毎週流れるプロダクト・運用型・CTV のスポットでは、数字は逆を指します。",
            "blocks": [
                {"type": "answer", "q": "マーケティングチームは、いつ制作会社ではなく SPOT を使うべきですか？",
                 "a": "繰り返し発生するクリエイティブに SPOT を使います。プロダクトスポット、アプリ・SaaS 広告、バンパー、CTV の尺違い、A/B バリエーション、多言語版。実在のタレント、ロケ撮影、オリジナル楽曲、1 年間走る大きなアイデアが必要なキャンペーンには制作会社を使います。多くのチームは基幹キャンペーンを制作会社に残し、その下流をすべて SPOT に移しています。"},
                {"type": "table", "h": "15 秒スポット 1 本で比べると", "cols": ["", "制作会社", "SPOT（Team）"], "hl_col": 2,
                 "rows": [["初稿までの時間", "約 3 週間", "当日"], ["費用", "¥50 万〜300 万（Web 用）、TV CM は ¥100 万〜500 万", "1 スポット約 ¥2,400。月額 ¥59,800 で 25 スポット"], ["フォーマット", "1 つ。追加は別料金", "16:9・9:16・1:1 を同梱"], ["バリエーション", "1 つ。追加は変更依頼", "3 つのイントロ案を同梱"], ["修正", "往復で数日", "言葉で、数分、0.25 スポット"], ["プロダクト画面", "画面録画か、ポストでモック", "実際の UI を自動合成"], ["タレント・ロケ", "実在の人物・場所", "合成の人物・生成したシーン"], ["音楽", "作曲", "許諾済み BGM と自社サウンドロゴ"]],
                 "cap": "制作会社の相場は公開されている費用ガイドから。[費用ガイド](/ja/guides/how-much-does-a-15-second-commercial-cost/)を参照。"},
                {"type": "cards", "cls": "grid2", "items": [
                    {"h": "制作会社に残すもの", "p": "実在タレントのブランドキャンペーン · ロケ撮影 · オリジナル楽曲 · 年間の基幹アイデア · 現場でディレクターの目が必要なもの"},
                    {"h": "SPOT に移すもの", "p": "プロダクト・機能のスポット · アプリ獲得・SaaS 広告 · バンパーと CTV の尺違い · A/B フックとターゲット違い · 同じスポットの日本語版と英語版"}]},
            ],
            "faq": [("AI 生成の動画は有料媒体に耐えますか？", "プロダクト主導・メッセージ主導のスポットなら耐えます。SPOT は動画化の前にすべてのカットを検品し、実際のプロダクトを合成します。AI 動画の失敗の多くはここで起きます。タレント主導の情緒的なストーリーは、引き続き制作会社の仕事です。"),
                    ("「1/400」の根拠は？", "Team の月額 ¥59,800 を 25 スポットで割ると 1 スポット約 ¥2,400。¥100 万〜500 万の TV CM 制作費に対して約 1/400〜1/2,000、Web 動画の ¥50 万に対して約 1/200 です。中位の制作費に対して「約 1/400」としています。"),
                    ("うちの代理店が SPOT を使うことはできますか？", "できます。Enterprise はホワイトラベル出力とブランド無制限の代理店ワークスペースに対応します。")],
            "related": [("内製チーム", "use-cases/in-house-teams"), ("15 秒 CM の制作費用と相場", "guides/how-much-does-a-15-second-commercial-cost"), ("料金", "pricing")]}


def hub(lang):
    items = []
    for k, c in COMPETITORS.items():
        items.append({"h": (f"SPOT vs {c['name']}" if lang == "en" else f"SPOT と {c['name']}"), "p": c["positioning"] if lang == "en" else CP[k]["ja"]["lede"].split("。")[0] + "。", "path": f"compare/{k}"})
    items.append({"h": "SPOT vs an agency" if lang == "en" else "SPOT と制作会社", "p": ("Cost, time and control for one 15-second spot." if lang == "en" else "15 秒スポット 1 本の費用・納期・コントロール。"), "path": "compare/spot-vs-agency"})
    if lang == "en":
        return {"path": "compare", "crumbs": [], "eyebrow": "Compare",
                "title": "SPOT alternatives and comparisons — Creatify, Arcads, HeyGen, Waymark, Poolday, agencies",
                "desc": "Honest comparisons of SPOT with AI video ad tools and production agencies: pricing, metering, output and fit, with prices checked on " + PRICE_DATE + ".",
                "h1": "Compare SPOT<br>with the alternatives.", "lede": "Each comparison states where the other option is the better choice. Prices are checked on the date shown and linked to the vendor’s own page.",
                "blocks": [{"type": "cards", "cls": "grid2", "items": items},
                           {"type": "table", "h": "All at a glance", "cols": ["Product", "Entry", "Unit", "Per finished video", "Output"],
                            "rows": [["**SPOT**", SPOT_ROW["en"]["entry"], "Spot (9 files)", "$16 on Team", SPOT_ROW["en"]["output"]]] + [[f"[{c['name']}]({c['url']})", c["entry"], c["unit"], c["per_video"], c["output"]] for c in COMPETITORS.values()],
                            "cap": "As of " + PRICE_DATE + ". Arcads figures are third-party."}],
                "related": [("Best AI video ad generators 2026", "guides/best-ai-video-ad-generators-2026"), ("Pricing", "pricing")]}
    return {"path": "compare", "crumbs": [], "eyebrow": "比較",
            "title": "SPOT の代替と比較｜Creatify・Arcads・HeyGen・Waymark・Poolday・制作会社",
            "desc": "SPOT と AI 動画広告ツール・制作会社の公正な比較：価格・課金単位・成果物・向き不向き。価格は " + PRICE_DATE + " 時点。",
            "h1": "SPOT と、<br>他の選択肢。", "lede": "各比較では、相手のほうが良い場面も明記します。価格は記載日に確認し、各社の料金ページにリンクしています。",
            "blocks": [{"type": "cards", "cls": "grid2", "items": items},
                       {"type": "table", "h": "一覧", "cols": ["製品", "入口", "課金単位", "完成動画 1 本あたり", "できあがるもの"],
                        "rows": [["**SPOT**", SPOT_ROW["ja"]["entry"], "スポット（9 ファイル）", "Team で約 ¥2,400", SPOT_ROW["ja"]["output"]]] + [[f"[{c['name']}]({c['url']})", c["entry"], c["unit"], c["per_video"], c["output"]] for c in COMPETITORS.values()],
                        "cap": PRICE_DATE + " 時点。Arcads の数値は第三者情報。"}],
            "related": [("AI 動画広告ツール おすすめ 2026", "guides/best-ai-video-ad-generators-2026"), ("料金", "pricing")]}


def pages(lang):
    out = [hub(lang)]
    for k in COMPETITORS:
        out.append(_competitor_page(lang, k))
    out.append(agency(lang))
    return out
