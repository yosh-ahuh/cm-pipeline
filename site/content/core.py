"""Core pages: home, pricing, how-it-works, brand-safety, security."""
from . import common
from .common import SITE, APP_URL, DEMO_URL, PRICE_DATE, app_link


def _hero(lang):
    if lang == "en":
        return f"""<header class="hero"><div class="wrap">
  <span class="eyebrow">AI commercial studio for marketing teams</span>
  <h1>Every spot,<br>in a day.</h1>
  <p class="sub">The structure and the prompts live inside Spot. You pick the platform, industry and audience, then review the first cut. Built on your real app screens, with the AI-use disclosure included — the same day.</p>
  <div class="cta"><a class="btn btn-primary" href="{app_link('hero')}">Start free</a><a class="btn btn-ghost" href="{DEMO_URL}">Book a demo</a><span class="micro">No prompt writing. No editing skills.</span></div>
  <div class="stage" aria-hidden="true">
    <div class="fr vert"><span class="lbl">9:16</span><div class="cap">Done on site.</div><span class="play"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></span></div>
    <div class="fr wide"><span class="lbl">16:9</span><div class="cap">Every spot, in a day.</div><span class="play"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></span></div>
    <div class="fr square"><span class="lbl">1:1</span><div class="cap">Ship it today.</div><span class="play"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></span></div>
  </div>
  <div class="trust"><span class="cap">Built for in-house teams</span><div class="row"><b>SaaS</b><b>Apps</b><b>D2C</b><b>Fintech</b><b>Marketplaces</b></div></div>
</div></header>"""
    return f"""<header class="hero"><div class="wrap">
  <span class="eyebrow">マーケティングチームのための AI 動画広告・CM 制作ツール</span>
  <h1>動画広告が、<br>その日のうちに。</h1>
  <p class="sub">構成もプロンプトも、Spot が持っています。あなたは配信先・業種・ターゲットを選んで、できた初稿を確認するだけ。実際のアプリ画面を使い、AI 利用の表記までついて、その日のうちに。</p>
  <div class="cta"><a class="btn btn-primary" href="{app_link('hero')}">無料ではじめる</a><a class="btn btn-ghost" href="{DEMO_URL}">デモを予約</a><span class="micro">プロンプトも動画編集スキルも必要ありません。</span></div>
  <div class="stage" aria-hidden="true">
    <div class="fr vert"><span class="lbl">9:16</span><div class="cap">現場で、その場で。</div><span class="play"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></span></div>
    <div class="fr wide"><span class="lbl">16:9</span><div class="cap">動画広告が、その日のうちに。</div><span class="play"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></span></div>
    <div class="fr square"><span class="lbl">1:1</span><div class="cap">今日、公開。</div><span class="play"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></span></div>
  </div>
  <div class="trust"><span class="cap">こんなチームのために</span><div class="row"><b>SaaS</b><b>アプリ</b><b>D2C</b><b>フィンテック</b><b>マーケットプレイス</b></div></div>
</div></header>"""


def pages(lang):
    return [home(lang), pricing(lang), how_it_works(lang), brand_safety(lang), security(lang)]


# --------------------------------------------------------------------------- home
def home(lang):
    if lang == "en":
        return {
            "path": "", "hero": _hero("en"),
            "title": "Spot — AI video ad & commercial studio for marketing teams",
            "og_title": "Spot — Every spot, in a day.",
            "desc": "Spot turns three choices into a finished video ad. AI generates the footage, your real product UI, the voiceover and the music, then delivers a ready-to-ship commercial the same day — 3 patterns × 3 formats, from $99 a month.",
            "h1": "Every spot, in a day.", "jsonld": [common.software_jsonld("en")],
            "blocks": [
                {"type": "steps", "eyebrow": "How it works", "h": "Three choices. One finished commercial.",
                 "p": "The expertise lives in the options, not in a prompt box — so anyone on the team can ship broadcast-quality work.",
                 "items": [("01", "Choose", "Platform, industry, audience, tone. Spot applies the winning ad structure behind the scenes — length, format, hook, all decided for you."),
                           ("02", "Generate", "AI writes the script and a shot list, then produces the live-action, your real product UI, voiceover and music — routing each shot to the best model."),
                           ("03", "Ship", "Review three intro patterns, tweak in plain words, and export nine files — three patterns across landscape, vertical and square.")]},
                {"type": "cards", "eyebrow": "Why Spot", "h": "Enterprise-ready, by design.", "items": [
                    {"h": "Brand-safe", "p": "Your real product screens are composited in — never fake UI. A brand kit and pronunciation guide keep your tone and product names exactly right.", "path": "brand-safety"},
                    {"h": "Same-day", "p": "Brief to first cut in a day. Revisions in minutes with plain language. Refresh creative before it fatigues.", "path": "how-it-works"},
                    {"h": "Built to scale", "p": "Spin one concept into dozens of angles and formats for always-on A/B testing. Team seats and approval flows included.", "path": "use-cases/ab-testing-at-scale"}]},
                {"type": "band", "items": [("1/<em>400</em>", "of typical agency production cost"), ("Same day", "vs. an industry average of 3 weeks"), ("3 × 3", "patterns × formats, generated at once")]},
                {"type": "cards", "eyebrow": "Use cases", "h": "Built for the teams that ship ads every week.", "items": [
                    {"h": "SaaS demo ads", "p": "Show the real product doing the real thing, in 15 seconds, on every platform.", "path": "use-cases/saas-demo-ads"},
                    {"h": "App install ads", "p": "Vertical-first creative for TikTok, Reels and Shorts, refreshed before it fatigues.", "path": "use-cases/app-install-ads"},
                    {"h": "CTV / OTT spots", "p": "Broadcast-format 15s and 30s commercials without the broadcast budget.", "path": "use-cases/ctv-ott-spots"}]},
                {"type": "facts", "eyebrow": "Outcomes", "h": "What changes when the studio is built in.", "items": [
                    {"n": "9", "k": "ready-to-ship files per spot — 3 patterns × 3 formats"},
                    {"n": "0", "k": "prompts to write, ever"},
                    {"n": "Minutes", "k": "to revise, in plain words like “make shot 2 brighter”"},
                    {"n": "100%", "k": "real product UI composited in — never fake screens"}]},
                {"type": "plans", "eyebrow": "Pricing", "h": "Plans that count in spots, not seconds.",
                 "p": "One spot is one finished commercial: 3 intro patterns × 3 formats = 9 files. [See full pricing](/pricing/)."},
            ],
            "faq": [
                ("What is Spot?", "Spot is an AI commercial studio for in-house marketing teams. You choose platform, industry, audience and tone; Spot writes the script, generates live-action footage, composites your real product UI, adds voiceover and music, and exports a finished commercial in three patterns and three formats."),
                ("How is Spot different from UGC ad generators like Creatify or Arcads?", "UGC tools render a talking avatar reading a script, one format at a time. Spot produces a full commercial with live-action shots, your actual product screens and a sound design, and delivers nine files per spot. See the [comparison](/compare/)."),
                ("How much does Spot cost?", "Starter is $99 a month for 6 spots, Team is $399 for 25 spots and 5 seats, Business is $1,199 for 80 spots with unlimited seats, SSO and API. A free plan gives one watermarked spot a month."),
                ("Do I need to write prompts?", "No. The expertise is built into the options. You pick from menus, review three intro patterns, and tweak in plain language such as “make the second shot brighter”."),
            ],
        }
    return {
        "path": "", "hero": _hero("ja"),
        "title": "Spot（スポット）｜選ぶだけの AI 動画広告・CM 制作ツール",
        "og_title": "Spot｜AI 動画広告・CM 制作ツール",
        "desc": "Spot（スポット）は、選ぶだけで動画広告・CM をつくれる AI 制作ツール。実写・アプリ画面・ナレーション・BGM まで自動生成し、3 パターン × 3 フォーマットの動画広告をその日のうちに納品。月額 ¥14,800 から。",
        "h1": "動画広告が、その日のうちに。", "jsonld": [common.software_jsonld("ja")],
        "blocks": [
            {"type": "steps", "eyebrow": "使い方", "h": "3 つ選ぶだけで、動画広告が 1 本完成。",
             "p": "広告制作の勝ちパターンは、選択肢の中に。プロンプトを書かなくても、チームの誰もが放送品質の動画広告をつくれます。",
             "items": [("01", "選ぶ", "配信先・業種・ターゲット・トーンを選択するだけ。尺・縦横比・冒頭フックといった勝ちパターンは自動で最適化されます。"),
                       ("02", "つくる", "AI が構成台本と撮影指示を作成し、実写・アプリ画面・ナレーション・BGM まで生成。カットごとに最適な AI を使い分けます。"),
                       ("03", "公開する", "3 つのイントロ案から選び、気になる点は言葉で修正。横型・縦型・正方形 × 3 パターンの計 9 本を書き出せます。")]},
            {"type": "cards", "eyebrow": "選ばれる理由", "h": "はじめから、企業仕様。", "items": [
                {"h": "ブランドセーフ", "p": "実際のアプリ画面を合成し、偽の UI は作りません。ブランドガイドラインと読み仮名辞書で、トーンと商品名を守ります。景表法にも配慮。", "path": "brand-safety"},
                {"h": "当日納品", "p": "ブリーフから初稿まで最短当日。修正は「もっと明るく」のひと言で数分。広告が疲弊する前に、素材を差し替え続けられます。", "path": "how-it-works"},
                {"h": "量産にも対応", "p": "1 つの企画を訴求軸・フォーマット違いで量産し、常時 A/B テストへ。チームでの利用や承認フローにも対応します。", "path": "use-cases/ab-testing-at-scale"}]},
            {"type": "band", "items": [("1/<em>400</em>", "一般的な制作会社の外注費に対して"), ("当日", "業界平均は約 3 週間"), ("3 × 3", "パターン × フォーマットを一括生成")]},
            {"type": "cards", "eyebrow": "ユースケース", "h": "毎週広告を出すチームのために。", "items": [
                {"h": "SaaS のデモ広告", "p": "実際のプロダクトが実際に動く 15 秒を、すべての配信先に。", "path": "use-cases/saas-demo-ads"},
                {"h": "アプリ獲得広告", "p": "TikTok・リール・ショート向けの縦型素材を、疲弊する前に差し替え続ける。", "path": "use-cases/app-install-ads"},
                {"h": "CTV / 運用型テレビ CM", "p": "放送フォーマットの 15 秒・30 秒 CM を、放送予算なしで。", "path": "use-cases/ctv-ott-spots"}]},
            {"type": "facts", "eyebrow": "導入効果", "h": "スタジオを内蔵すると、何が変わるか。", "items": [
                {"n": "9", "k": "1 スポットの納品ファイル数 — 3 パターン × 3 フォーマット"},
                {"n": "0", "k": "書くプロンプトはゼロ"},
                {"n": "数分", "k": "修正は「2 カット目を明るく」の言葉で数分"},
                {"n": "100%", "k": "実際のアプリ画面を合成 — 偽の UI は作らない"}]},
            {"type": "plans", "eyebrow": "料金", "h": "秒でもクレジットでもなく、「スポット」で数える料金。",
             "p": "1 スポット＝完成した CM 1 本。3 つのイントロ案 × 3 フォーマット＝9 ファイル。[料金の詳細](/ja/pricing/)。"},
        ],
        "faq": [
            ("Spot とは何ですか？", "内製マーケティングチーム向けの AI CM 制作ツールです。配信先・業種・ターゲット・トーンを選ぶと、AI が台本を書き、実写映像を生成し、実際のプロダクト画面を合成、ナレーションと BGM を付けて、3 パターン × 3 フォーマットの完成 CM を書き出します。"),
            ("Creatify や Arcads のような UGC 広告ツールと何が違いますか？", "UGC ツールはアバターが台本を読む動画を 1 フォーマットずつ生成します。Spot は実写カット・実際のプロダクト画面・音響設計を含む「CM」を、1 スポットあたり 9 ファイルで納品します。[比較ページ](/ja/compare/)をご覧ください。"),
            ("料金はいくらですか？", "Starter は月額 ¥14,800 で 6 スポット、Team は ¥59,800 で 25 スポット・5 席、Business は ¥178,000 で 80 スポット・席無制限・SSO・API。無料プランは月 1 スポット（透かし入り）です。"),
            ("プロンプトを書く必要はありますか？", "ありません。専門知識は選択肢に埋め込まれています。メニューから選び、3 つのイントロ案を確認し、「2 カット目をもう少し明るく」のように言葉で修正します。"),
        ],
    }


# --------------------------------------------------------------------------- pricing
def pricing(lang):
    if lang == "en":
        return {
            "path": "pricing", "crumbs": [], "eyebrow": "Pricing",
            "title": "Spot pricing — plans from $99 a month, priced per finished commercial",
            "desc": "Spot plans: Free (1 spot), Starter $99 for 6 spots, Team $399 for 25 spots and 5 seats, Business $1,199 for 80 spots with SSO and API, Enterprise from $2,500. One spot = one finished commercial in 3 patterns × 3 formats.",
            "h1": "Priced per spot.<br>Not per second.", "jsonld": [common.software_jsonld("en")],
            "lede": "One spot is one finished commercial — 3 intro patterns × 3 formats (16:9, 9:16, 1:1) = 9 ready-to-ship files. Every plan includes the script, live-action generation, your real product UI, voiceover and music.",
            "updated": PRICE_DATE,
            "blocks": [
                {"type": "plans"},
                {"type": "table", "eyebrow": "What a spot includes", "h": "Everything below ships with every spot.",
                 "cols": ["Included", "Detail"],
                 "rows": [["Script and shot list", "Written from your platform, industry, audience and tone choices, using proven ad structures (hook, proof, CTA)."],
                          ["Live-action footage", "Generated per shot and routed to the best model for the job; each shot passes an automated quality review before it is used."],
                          ["Your real product UI", "Upload screenshots or a screen recording; Spot composites the real interface — never a fake UI."],
                          ["Voiceover and music", "Natural voice in English or Japanese with your pronunciation guide; licensed-for-ads music bed and sound logo slot."],
                          ["3 intro patterns", "Three different openings so you can A/B test the hook without re-briefing."],
                          ["3 formats", "16:9 for YouTube and CTV, 9:16 for Shorts, Reels and TikTok, 1:1 for feed."],
                          ["Revisions", "Plain-language tweaks re-render in minutes. A re-render of one pattern costs 0.25 spot; regenerating a single shot costs 0.1 spot."]]},
                {"type": "table", "eyebrow": "Compare", "h": "How Spot pricing compares.",
                 "p": "Public list prices as of " + PRICE_DATE + ". Competitors meter credits or avatar minutes; the last column is what one finished 30-second video works out to.",
                 "cols": ["Product", "Entry plan", "Unit", "Per finished video", "Output"],
                 "rows": [["**Spot**", "$99 / 6 spots", "Spot (9 files)", "$16 on Team", "Full commercial, 3 patterns × 3 formats"],
                          ["[Creatify](https://creatify.ai/pricing)", "$39 / 100 credits", "Credits", "≈ $3.30–3.90", "Avatar UGC ad, one format"],
                          ["[HeyGen](https://www.heygen.com/pricing)", "$29 / 600 credits", "Credits", "≈ $1–1.50 per minute", "Avatar presenter video"],
                          ["[Waymark](https://cms.waymark.com/marketing/pricing)", "$399 / 2 videos", "Finalized videos", "≈ $87–200", "Template TV / CTV spot"],
                          ["[Poolday](https://poolday.ai/pricing)", "$1,250", "Dollar credits", "$5–25", "UGC performance videos"],
                          ["Agency (15 s spot)", "—", "Project", "$5,000–15,000", "One commercial, one format, ~3 weeks"]],
                 "cap": "Sources are linked. Agency range from published production-cost guides; see the [cost guide](/guides/how-much-does-a-15-second-commercial-cost/)."},
            ],
            "faq": [
                ("What exactly is a spot?", "A spot is one finished commercial: three intro patterns rendered in three formats, so nine files. It is the unit on every plan, and the balance in the app is shown in spots."),
                ("What happens if I use all my spots?", "You can buy extra spots at $19 each on Starter and Team, or $15 on Business, without changing plans. Unused spots do not roll over on monthly billing; annual plans pool spots across the year."),
                ("Is there a free plan?", "Yes. The Free plan gives one watermarked 720p spot a month, with one seat and one brand, so you can see a real result before paying."),
                ("Do you offer annual billing and invoicing?", "Annual billing gives two months free. Business and Enterprise can pay by invoice; Japanese customers can be billed in JPY."),
                ("Which plan has SSO and an API?", "Business and Enterprise include SSO, an API and an audit log. Enterprise adds white-label output for agencies, a DPA and a security review."),
                ("Do prices include the AI models?", "Yes. Model costs are included. Business and Enterprise unlock Premium quality models and 4K output; other plans use Spot’s default model routing."),
            ],
            "related": [("How it works", "how-it-works"), ("Spot vs Creatify", "compare/creatify"), ("Spot vs an agency", "compare/spot-vs-agency")],
        }
    return {
        "path": "pricing", "crumbs": [], "eyebrow": "料金",
        "title": "Spot の料金｜月額 ¥14,800 から、完成 CM 1 本単位の料金プラン",
        "desc": "Spot の料金プラン：Free（月 1 スポット）、Starter ¥14,800（6 スポット）、Team ¥59,800（25 スポット・5 席）、Business ¥178,000（80 スポット・SSO・API）、Enterprise ¥380,000〜。1 スポット＝完成 CM 1 本（3 パターン × 3 フォーマット）。",
        "h1": "秒ではなく、<br>スポットで。", "jsonld": [common.software_jsonld("ja")],
        "lede": "1 スポット＝完成した CM 1 本。3 つのイントロ案 × 3 フォーマット（16:9・9:16・1:1）＝すぐ入稿できる 9 ファイル。台本・実写生成・実際のプロダクト画面・ナレーション・BGM は全プランに含まれます。",
        "updated": PRICE_DATE,
        "blocks": [
            {"type": "plans"},
            {"type": "table", "eyebrow": "1 スポットに含まれるもの", "h": "以下はすべてのスポットに含まれます。",
             "cols": ["含まれるもの", "内容"],
             "rows": [["台本とカット表", "配信先・業種・ターゲット・トーンの選択から、実績のある広告構成（フック・証拠・CTA）で作成。"],
                      ["実写映像", "カットごとに最適なモデルへ振り分けて生成。各カットは自動の品質検品を通過してから使われます。"],
                      ["実際のプロダクト画面", "スクリーンショットや画面録画をアップロードすると、実際の UI を合成。偽の UI は作りません。"],
                      ["ナレーションと BGM", "日本語・英語の自然な音声に読み仮名辞書を適用。広告利用可能な BGM とサウンドロゴ枠。"],
                      ["3 つのイントロ案", "冒頭フックを 3 通り。ブリーフし直さずに A/B テストできます。"],
                      ["3 フォーマット", "YouTube・CTV 向け 16:9、ショート・リール・TikTok 向け 9:16、フィード向け 1:1。"],
                      ["修正", "言葉で指示すると数分で再レンダリング。1 パターンの再レンダは 0.25 スポット、1 カットの再生成は 0.1 スポット。"]]},
            {"type": "table", "eyebrow": "比較", "h": "Spot の料金を他と比べると。",
             "p": PRICE_DATE + " 時点の公開価格。他社はクレジットやアバター分数で課金するため、右の列は「完成動画 1 本あたり」に換算しています。",
             "cols": ["製品", "入口プラン", "課金単位", "完成動画 1 本あたり", "できあがるもの"],
             "rows": [["**Spot**", "¥14,800 / 6 スポット", "スポット（9 ファイル）", "Team で約 ¥2,400", "3 パターン × 3 フォーマットの完成 CM"],
                      ["[Creatify](https://creatify.ai/pricing)", "$39 / 100 クレジット", "クレジット", "約 $3.3〜3.9", "アバター UGC 広告・1 フォーマット"],
                      ["[HeyGen](https://www.heygen.com/pricing)", "$29 / 600 クレジット", "クレジット", "1 分 約 $1〜1.5", "アバター解説動画"],
                      ["[Waymark](https://cms.waymark.com/marketing/pricing)", "$399 / 2 本", "完成動画の本数", "約 $87〜200", "テンプレート型 TV / CTV スポット"],
                      ["[Kaizen Ad](https://kaizenplatform.com/contents/video-advertising-costs)", "¥50,000 / 本〜", "本", "¥50,000〜", "制作代行・5 営業日"],
                      ["制作会社（15 秒 CM）", "—", "案件", "¥500,000〜3,000,000", "1 本・1 フォーマット・約 3 週間"]],
             "cap": "出典は各リンク先。制作会社の相場は[費用ガイド](/ja/guides/how-much-does-a-15-second-commercial-cost/)を参照。"},
        ],
        "faq": [
            ("スポットとは何ですか？", "完成した CM 1 本のことです。3 つのイントロ案を 3 フォーマットで書き出すので 9 ファイルになります。全プラン共通の単位で、アプリ内の残高もスポットで表示されます。"),
            ("スポットを使い切ったらどうなりますか？", "プランを変えずに追加スポットを購入できます（Starter・Team は ¥2,800、Business は ¥2,200）。月払いでは未使用分は繰り越されません。年契約は年間分をまとめて使えます。"),
            ("無料プランはありますか？", "あります。月 1 スポット（透かし入り・720p）、1 席・1 ブランドで、支払い前に実際の仕上がりを確認できます。"),
            ("年契約や請求書払いはできますか？", "年契約は 2 か月分無料です。Business 以上は請求書払い・日本円請求に対応します。"),
            ("SSO や API はどのプランですか？", "Business と Enterprise に SSO・API・監査ログが含まれます。Enterprise は代理店向けのホワイトラベル出力、DPA、セキュリティ審査対応が加わります。"),
            ("AI モデルの利用料は含まれていますか？", "含まれています。Business 以上は Premium quality モデルと 4K 出力が使えます。その他のプランは Spot 標準のモデル振り分けです。"),
        ],
        "related": [("使い方", "how-it-works"), ("Spot と Creatify", "compare/creatify"), ("Spot と制作会社", "compare/spot-vs-agency")],
    }


# --------------------------------------------------------------------------- how it works
def how_it_works(lang):
    if lang == "en":
        return {
            "path": "how-it-works", "crumbs": [], "eyebrow": "How it works",
            "title": "How Spot works — from three choices to a finished commercial in a day",
            "desc": "How Spot makes a commercial: choose platform, industry, audience and tone; AI writes the script, generates and reviews each shot, composites your real product UI, adds voice and music, and exports 3 patterns × 3 formats.",
            "h1": "Three choices.<br>One finished commercial.",
            "lede": "Spot hides the prompt box. The craft of a good ad — structure, length, hook, pacing — lives in the options you pick, so anyone on the team can brief and ship.",
            "blocks": [
                {"type": "answer", "q": "How does Spot make a video ad?",
                 "a": "You pick platform, industry, audience and tone. Spot writes a script and shot list, generates a still for every shot, reviews each still with a vision model and retakes failures, animates approved stills, composites your real product screens, generates voiceover and music, then renders three intro patterns in three formats. First cut arrives the same day."},
                {"type": "steps", "h": "The pipeline, step by step",
                 "items": [("01", "Brief by choosing", "Platform (YouTube, Shorts, Reels, TikTok, CTV), industry, audience and tone. Spot sets length, aspect ratios and hook style from proven ad structures."),
                           ("02", "Script and shot list", "A structured script with a hook, a proof beat and a call to action, broken into shots with a visual direction for each."),
                           ("03", "Stills, reviewed", "Every shot starts as a still image. A vision model checks it against a quality checklist (no AI artifacts, correct product, on-brand look) and retakes automatically."),
                           ("04", "Animate", "Approved stills are animated, routing each shot to the best model for that kind of motion. Your uploaded product UI is composited as a real screen."),
                           ("05", "Voice and music", "Voiceover in English or Japanese, with your pronunciation guide applied. A licensed music bed and an optional sound logo."),
                           ("06", "Render nine files", "Three intro patterns × 16:9, 9:16 and 1:1. Review, tweak in plain words, approve, download.")]},
                {"type": "table", "eyebrow": "Model routing", "h": "Each stage uses the model that is best for it.",
                 "p": "Spot chooses per shot; you never pick a model. Business and Enterprise can turn on Premium quality models for 4K output.",
                 "cols": ["Stage", "What runs", "Why"],
                 "rows": [["Stills", "Image models (photoreal or documentary looks)", "Cheap to iterate; quality is decided before any video is rendered"],
                          ["Review", "Vision model with a checklist", "Catches artifacts, wrong products and off-brand looks before animation"],
                          ["Animate", "Video models chosen per shot type", "Talking shots, product shots and B-roll each have a best model"],
                          ["Product UI", "Compositing from your screenshots or recording", "Real interface, never hallucinated"],
                          ["Voice", "Neural TTS with pronunciation guide", "Product names pronounced right, every time"],
                          ["Build", "Programmatic video composition", "Deterministic layout for all nine files"]]},
                {"type": "facts", "h": "What that means for a marketing team", "items": [
                    {"n": "Same day", "k": "Brief to first cut. Industry average for an agency-produced spot is about three weeks.", "src": "Spot pipeline", "url": ""},
                    {"n": "9 files", "k": "Per spot: 3 patterns × 3 formats, ready for YouTube, Shorts, Reels, TikTok, CTV and feed.", "src": "", "url": ""},
                    {"n": "Minutes", "k": "Plain-language revision such as “make the second shot warmer” re-renders in minutes.", "src": "", "url": ""}]},
            ],
            "faq": [
                ("What do I need to provide?", "A product name, a one-line description, screenshots or a screen recording of the product, and your brand kit (logo, colors, fonts) if you have one. Everything else is generated."),
                ("Can I edit the script?", "Yes. You can edit any line before generation and re-render a single pattern afterwards for 0.25 spot."),
                ("What languages are supported?", "English and Japanese for script and voiceover today. Both come with a pronunciation guide for product names."),
                ("How long is a spot?", "Standard lengths are 6, 15 and 30 seconds, set by the platform you choose. Bumper ads are 6 seconds; YouTube and CTV spots are 15 or 30."),
                ("What if a shot looks wrong?", "Every still is reviewed automatically before animation. If something still looks off, describe it in plain words and Spot regenerates that shot for 0.1 spot."),
            ],
            "related": [("Pricing", "pricing"), ("Brand safety", "brand-safety"), ("Video ad specs 2026", "guides/video-ad-specs-2026")],
        }
    return {
        "path": "how-it-works", "crumbs": [], "eyebrow": "使い方",
        "title": "Spot の使い方｜3 つ選ぶだけで、その日のうちに完成 CM",
        "desc": "Spot で CM ができるまで：配信先・業種・ターゲット・トーンを選ぶと、AI が台本を書き、カットごとに生成と検品を行い、実際のプロダクト画面を合成、音声と BGM を付けて、3 パターン × 3 フォーマットを書き出します。",
        "h1": "3 つ選ぶだけで、<br>CM が 1 本。",
        "lede": "Spot にはプロンプト欄がありません。良い広告の作法（構成・尺・フック・テンポ）は選択肢の側に入っているので、チームの誰でもブリーフして公開できます。",
        "blocks": [
            {"type": "answer", "q": "Spot はどうやって動画広告をつくるのですか？",
             "a": "配信先・業種・ターゲット・トーンを選びます。Spot が台本とカット表を書き、カットごとにスチルを生成、視覚モデルで検品して NG は自動リテイク、承認されたスチルを動画化し、実際のプロダクト画面を合成、ナレーションと BGM を生成して、3 つのイントロ案 × 3 フォーマットをレンダリングします。初稿はその日のうちに届きます。"},
            {"type": "steps", "h": "パイプラインの各段階",
             "items": [("01", "選んでブリーフ", "配信先（YouTube・ショート・リール・TikTok・CTV）、業種、ターゲット、トーン。尺・縦横比・フックの型は実績ある広告構成から自動で決まります。"),
                       ("02", "台本とカット表", "フック・証拠・CTA の構成で台本を作り、カットごとに画づくりの指示を付けます。"),
                       ("03", "スチルを生成し、検品", "各カットはまず静止画から。視覚モデルがチェックリスト（AI 感・破綻・商品の正しさ・トンマナ）で検品し、NG は自動で撮り直します。"),
                       ("04", "動画化", "承認スチルを動画化。カットの種類ごとに最適なモデルへ振り分けます。アップロードしたプロダクト画面は実物として合成されます。"),
                       ("05", "音声と BGM", "日本語・英語のナレーションに読み仮名辞書を適用。広告利用可能な BGM と、任意のサウンドロゴ。"),
                       ("06", "9 ファイルを書き出し", "3 つのイントロ案 × 16:9・9:16・1:1。確認して、言葉で修正して、承認、ダウンロード。")]},
            {"type": "table", "eyebrow": "モデルの配役", "h": "工程ごとに、最適なモデルを使い分けます。",
             "p": "カット単位で Spot が選びます。ユーザーがモデルを選ぶことはありません。Business 以上は Premium quality モデルと 4K 出力を有効にできます。",
             "cols": ["工程", "使うもの", "理由"],
             "rows": [["スチル", "画像モデル（実写調・ドキュメンタリー調）", "安く試行でき、動画化の前に品質を確定できる"],
                      ["検品", "チェックリスト付きの視覚モデル", "動画化の前に破綻・誤った商品・トンマナ違反を弾く"],
                      ["動画化", "カット種別ごとの動画モデル", "人物・商品・B ロールで最適なモデルが違う"],
                      ["プロダクト画面", "スクリーンショット・録画からの合成", "実物の UI。生成で捏造しない"],
                      ["音声", "読み仮名辞書付きの音声合成", "商品名を毎回正しく発音する"],
                      ["ビルド", "プログラムによる動画合成", "9 ファイルのレイアウトが常に一定"]]},
            {"type": "facts", "h": "マーケティングチームにとっての意味", "items": [
                {"n": "当日", "k": "ブリーフから初稿まで。制作会社に依頼した場合の業界平均は約 3 週間。", "src": "", "url": ""},
                {"n": "9 ファイル", "k": "1 スポットあたり 3 パターン × 3 フォーマット。YouTube・ショート・リール・TikTok・CTV・フィードにそのまま。", "src": "", "url": ""},
                {"n": "数分", "k": "「2 カット目をもう少し暖かく」のような言葉での修正が数分で再レンダリング。", "src": "", "url": ""}]},
        ],
        "faq": [
            ("何を用意すればいいですか？", "商品名、一行の説明、プロダクトのスクリーンショットか画面録画、あればブランドキット（ロゴ・色・書体）。それ以外は生成されます。"),
            ("台本は編集できますか？", "できます。生成前にどの行でも編集でき、生成後は 1 パターンを 0.25 スポットで再レンダリングできます。"),
            ("対応言語は？", "台本とナレーションは日本語と英語です。どちらも商品名の読み仮名辞書に対応しています。"),
            ("尺は何秒ですか？", "配信先に応じて 6 秒・15 秒・30 秒が標準です。バンパー広告は 6 秒、YouTube と CTV は 15 秒または 30 秒。"),
            ("カットがおかしいときは？", "動画化の前にすべてのスチルを自動検品します。それでも気になる場合は言葉で指摘すると、そのカットだけを 0.1 スポットで再生成します。"),
        ],
        "related": [("料金", "pricing"), ("ブランドセーフ", "brand-safety"), ("動画広告の入稿規定 2026", "guides/video-ad-specs-2026")],
    }


# --------------------------------------------------------------------------- brand safety
def brand_safety(lang):
    if lang == "en":
        return {
            "path": "brand-safety", "crumbs": [], "eyebrow": "Brand safety",
            "title": "Brand safety in Spot — real product UI, brand kit, pronunciation guide, ad-law checks",
            "desc": "How Spot keeps AI-generated commercials on-brand and compliant: real product screens composited in (never fake UI), brand kit and pronunciation guide, automated quality review, and checks for misleading claims.",
            "h1": "Never a fake UI.<br>Never a wrong name.",
            "lede": "The two things legal and brand teams worry about with AI video are hallucinated product screens and mangled product names. Spot is built so neither can happen.",
            "blocks": [
                {"type": "answer", "q": "How does Spot keep AI ads brand-safe?",
                 "a": "Spot never generates your product interface. You upload real screenshots or a recording, and the pipeline composites them as a screen inside the generated footage. Product names come from a pronunciation guide you control, colors and fonts from your brand kit, and every generated shot passes an automated review against a quality checklist before it is animated."},
                {"type": "cards", "h": "Four guarantees", "cls": "grid2", "items": [
                    {"h": "Real product UI", "p": "Interfaces are composited from your assets, never imagined by a model. What the viewer sees is what your customer will see."},
                    {"h": "Brand kit", "p": "Logo, colors, typography, do-not-do rules. Applied to every pattern and format, so nine files look like one campaign."},
                    {"h": "Pronunciation guide", "p": "Product and company names with phonetic spellings in English and Japanese. The voiceover reads them your way, every time."},
                    {"h": "Review before render", "p": "A vision model checks each shot for artifacts, wrong products and off-brand looks, and retakes automatically. Nothing broken reaches the cut."}]},
                {"type": "table", "eyebrow": "Compliance", "h": "Claims, disclosures and ad law.",
                 "p": "Spot’s script structures avoid the claim types that most often trigger regulator action. Final legal review stays with you.",
                 "cols": ["Risk", "How Spot handles it"],
                 "rows": [["Unsubstantiated superlatives (“No.1”, “best”)", "Script templates avoid superlatives unless you supply a source; a note flags any claim that needs substantiation."],
                          ["Misleading pricing or “free” claims", "Price lines are entered by you and rendered verbatim; conditions can be added as on-screen text."],
                          ["Fake testimonials or fake UI", "No synthetic testimonials in templates; product UI is always your real asset."],
                          ["Japan: Act against Unjustifiable Premiums and Misleading Representations (景品表示法)", "Templates avoid 優良誤認 / 有利誤認 patterns; the Japanese script pass flags unsupported comparatives. See the [copyright and compliance guide](/guides/ai-commercial-copyright-and-compliance/)."],
                          ["US: FTC endorsement and advertising rules", "No undisclosed endorsements are generated; disclosure text can be locked into the brand kit."],
                          ["Music and voice licensing", "Music beds are licensed for advertising use; voices are synthetic and cleared for commercial use."]]},
                {"type": "table", "eyebrow": "Approval", "h": "Approval flow on Team and above.",
                 "cols": ["Role", "Can"],
                 "rows": [["Editor", "Brief, generate, request revisions"], ["Approver", "Approve or reject a spot; comments are stored with the version"], ["Admin", "Manage brand kits, pronunciation guide, seats; audit log on Business"]]},
            ],
            "faq": [
                ("Does Spot train models on my product screenshots?", "No. Your assets are used only to render your spots and are not used to train models."),
                ("Can legal review a spot before it is published?", "Yes. On Team and above, an approver role must sign off before download, and every version keeps its comments."),
                ("Can I lock certain words or claims out of scripts?", "Yes. The brand kit accepts a do-not-say list and required disclosures, applied to every script."),
                ("What about the people in the footage?", "Generated people are synthetic and not based on real individuals. If you need real talent, you can supply your own footage for the live-action shots."),
            ],
            "related": [("Security", "security"), ("How it works", "how-it-works"), ("AI ads: copyright and compliance", "guides/ai-commercial-copyright-and-compliance")],
        }
    return {
        "path": "brand-safety", "crumbs": [], "eyebrow": "ブランドセーフ",
        "title": "Spot のブランドセーフ｜実際のプロダクト画面・ブランドキット・読み仮名辞書・景表法への配慮",
        "desc": "AI 生成の CM をブランド通り・法令通りに保つ仕組み：実際のプロダクト画面を合成（偽 UI を作らない）、ブランドキットと読み仮名辞書、自動検品、誤認表示のチェック。",
        "h1": "偽の UI は作らない。<br>名前は間違えない。",
        "lede": "AI 動画で法務とブランド担当が心配するのは、捏造されたプロダクト画面と、読み間違えられた商品名。Spot はどちらも起きない構造になっています。",
        "blocks": [
            {"type": "answer", "q": "Spot はどうやって AI 広告をブランドセーフに保ちますか？",
             "a": "Spot はプロダクトの画面を生成しません。実際のスクリーンショットや録画をアップロードすると、生成した映像の中に画面として合成します。商品名は管理者が編集できる読み仮名辞書から、色と書体はブランドキットから適用され、生成したすべてのカットは動画化の前にチェックリストによる自動検品を通ります。"},
            {"type": "cards", "h": "4 つの約束", "cls": "grid2", "items": [
                {"h": "実際のプロダクト画面", "p": "UI はお客様の素材から合成し、モデルには描かせません。視聴者が見るものは、実際の顧客が見るものと同じです。"},
                {"h": "ブランドキット", "p": "ロゴ・色・書体・禁止事項。すべてのパターンとフォーマットに適用され、9 ファイルが 1 つのキャンペーンに見えます。"},
                {"h": "読み仮名辞書", "p": "商品名・社名の読みを日本語と英語で登録。ナレーションは毎回、指定通りに読みます。"},
                {"h": "レンダ前の検品", "p": "視覚モデルが各カットの破綻・誤った商品・トンマナ違反を確認し、自動で撮り直します。壊れたカットは完成品に入りません。"}]},
            {"type": "table", "eyebrow": "コンプライアンス", "h": "表示・開示・広告規制。",
             "p": "Spot の台本構成は、行政指導の対象になりやすい表現の型を避けています。最終的な法務確認はお客様側で行ってください。",
             "cols": ["リスク", "Spot での扱い"],
             "rows": [["根拠のない最上級表現（「No.1」「最高」）", "出典の入力がない限りテンプレートは最上級表現を使わず、根拠が必要な主張には注記を付けます。"],
                      ["価格・「無料」の誤認", "価格の文言はお客様が入力したものをそのまま表示し、条件は画面上のテキストとして追加できます。"],
                      ["偽の体験談・偽の UI", "テンプレートに合成の体験談はなく、プロダクト UI は常にお客様の実素材です。"],
                      ["景品表示法（優良誤認・有利誤認）", "テンプレートは優良誤認・有利誤認の型を避け、日本語台本の検査で根拠のない比較表現に印を付けます。[著作権と景表法のガイド](/ja/guides/ai-commercial-copyright-and-compliance/)も参照。"],
                      ["ステマ規制（2023 年 10 月〜）", "広告である旨の表示をブランドキットに固定でき、すべてのパターンに入ります。"],
                      ["音楽・音声のライセンス", "BGM は広告利用の許諾済み、音声は商用利用可能な合成音声です。"]]},
            {"type": "table", "eyebrow": "承認", "h": "Team 以上の承認フロー。",
             "cols": ["ロール", "できること"],
             "rows": [["編集者", "ブリーフ、生成、修正依頼"], ["承認者", "スポットの承認・差し戻し。コメントはバージョンごとに保存"], ["管理者", "ブランドキット・読み仮名辞書・席の管理。Business では監査ログ"]]},
        ],
        "faq": [
            ("プロダクトのスクリーンショットはモデルの学習に使われますか？", "使われません。お客様の素材はスポットのレンダリングにのみ使用し、学習には使いません。"),
            ("公開前に法務が確認できますか？", "できます。Team 以上では承認者ロールの承認がないとダウンロードできず、すべてのバージョンにコメントが残ります。"),
            ("使ってはいけない言葉や表現を指定できますか？", "できます。ブランドキットに禁止語リストと必須の開示文を登録すると、すべての台本に適用されます。"),
            ("映像に出てくる人物は？", "生成された人物は合成で、実在の個人に基づいていません。実在のタレントが必要な場合は、実写カットにお客様の素材を使えます。"),
        ],
        "related": [("セキュリティ", "security"), ("使い方", "how-it-works"), ("AI CM の著作権と景表法", "guides/ai-commercial-copyright-and-compliance")],
    }


# --------------------------------------------------------------------------- security
def security(lang):
    if lang == "en":
        return {
            "path": "security", "crumbs": [], "eyebrow": "Security",
            "title": "Spot security — data handling, access control, SSO, retention",
            "desc": "How Spot handles your data: per-customer row-level isolation, encrypted storage, no model training on customer assets, SSO and audit log on Business, DPA and security review on Enterprise.",
            "h1": "Built for the security review.",
            "lede": "What IT and procurement ask before approving a new tool, answered in one page. Items marked “roadmap” are not yet available; we would rather say so than overstate.",
            "blocks": [
                {"type": "table", "h": "Controls",
                 "cols": ["Area", "Today", "Plan"],
                 "rows": [["Tenant isolation", "Every table is protected by row-level security; a user can only read and write rows they own", "All plans"],
                          ["Authentication", "Email and password with verified email", "SSO (SAML / OIDC) rolling out on Business and Enterprise"],
                          ["Encryption", "TLS in transit; encrypted at rest on managed Postgres and object storage", "All plans"],
                          ["Model training", "Customer assets and outputs are never used to train models", "All plans"],
                          ["Generation workers", "Run server-side with a service key that never reaches the browser", "All plans"],
                          ["Audit log", "Generation and credit ledger per workspace", "Full approve / download audit log rolling out on Business and Enterprise"],
                          ["Data retention", "Assets and renders kept while the account is active; deletion on request within 30 days", "All plans"],
                          ["DPA and sub-processor list", "Available on request", "Enterprise"],
                          ["Security questionnaire", "We complete standard questionnaires (SIG Lite, CAIQ)", "Enterprise"],
                          ["SOC 2", "Roadmap", "—"]]},
                {"type": "prose", "h": "Sub-processors", "paras": [
                    "Spot runs on managed infrastructure and calls third-party AI models for generation. Model providers receive only the prompt and reference assets for the shot being generated, under terms that do not permit training on the data. The current sub-processor list is available on request and is included in the DPA.",
                ]},
            ],
            "faq": [
                ("Where is data stored?", "In managed Postgres and object storage. Region selection is available on Enterprise."),
                ("Can we delete everything when we leave?", "Yes. Account deletion removes projects, assets, renders and ledger entries within 30 days."),
                ("Do you have SOC 2?", "Not yet. It is on the roadmap. We complete standard security questionnaires for Enterprise customers today."),
                ("Is the API key scoped?", "API keys on Business and Enterprise are scoped to a workspace and can be rotated by an admin."),
            ],
            "related": [("Brand safety", "brand-safety"), ("Pricing", "pricing")],
        }
    return {
        "path": "security", "crumbs": [], "eyebrow": "セキュリティ",
        "title": "Spot のセキュリティ｜データの取り扱い・アクセス制御・SSO・保持期間",
        "desc": "Spot のデータの扱い：顧客ごとの行レベル分離、暗号化ストレージ、顧客素材を学習に使わない方針、Business の SSO と監査ログ、Enterprise の DPA とセキュリティ審査対応。",
        "h1": "情シス審査を前提に、つくりました。",
        "lede": "新しいツールの導入前に情報システム部門と購買が確認する項目を 1 ページに。「予定」と書いた項目は未提供です。誇張するより正直に書きます。",
        "blocks": [
            {"type": "table", "h": "管理策",
             "cols": ["領域", "現在", "対象"],
             "rows": [["テナント分離", "すべてのテーブルに行レベルセキュリティ。ユーザーは自分が所有する行のみ読み書き可能", "全プラン"],
                      ["認証", "メールアドレス確認付きのメール＋パスワード", "SSO（SAML / OIDC）は Business・Enterprise で順次提供"],
                      ["暗号化", "通信は TLS。マネージド Postgres とオブジェクトストレージで保存時暗号化", "全プラン"],
                      ["モデル学習", "顧客の素材と生成物をモデルの学習に使用しない", "全プラン"],
                      ["生成ワーカー", "サーバ側で実行。サービスキーはブラウザに渡らない", "全プラン"],
                      ["監査ログ", "ワークスペースごとの生成・クレジット台帳", "承認・ダウンロードを含む完全な監査ログは Business・Enterprise で順次提供"],
                      ["データ保持", "アカウント有効期間中は保持。依頼から 30 日以内に削除", "全プラン"],
                      ["DPA・再委託先一覧", "依頼に応じて提供", "Enterprise"],
                      ["セキュリティチェックシート", "標準的な質問票（SIG Lite・CAIQ・経産省様式）に回答", "Enterprise"],
                      ["SOC 2", "予定", "—"]]},
            {"type": "prose", "h": "再委託先", "paras": [
                "Spot はマネージドインフラ上で動作し、生成のために外部の AI モデルを呼び出します。モデル提供者に渡るのは生成対象カットのプロンプトと参照素材のみで、学習利用を認めない条件で利用しています。再委託先の一覧は依頼に応じて提供し、DPA にも含まれます。",
            ]},
        ],
        "faq": [
            ("データはどこに保存されますか？", "マネージド Postgres とオブジェクトストレージです。リージョン指定は Enterprise で対応します。"),
            ("解約時にすべて削除できますか？", "できます。アカウント削除で、プロジェクト・素材・レンダリング結果・台帳を 30 日以内に削除します。"),
            ("SOC 2 は取得していますか？", "まだです。ロードマップに入っています。現在は Enterprise のお客様向けに標準的なセキュリティ質問票に回答しています。"),
            ("API キーの権限範囲は？", "Business・Enterprise の API キーはワークスペース単位で、管理者がローテーションできます。"),
        ],
        "related": [("ブランドセーフ", "brand-safety"), ("料金", "pricing")],
    }
