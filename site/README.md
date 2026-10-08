# SPOT marketing site（静的生成）

`spot-landing.html`（1 ページ・JS 翻訳）を、英日それぞれ実体のある多ページ構成に置き換えたもの。
設計の根拠は [`../spot-marketing.html`](../spot-marketing.html)（SEO/GEO 構成案・料金調査）。

```
site/
  build.py              # 生成器（依存なし・Python 3）。→ dist/
  content/common.py     # ドメイン・URL・ナビ・料金プラン・競合データ・Organization/Software JSON-LD
  content/core.py       # / /pricing /how-it-works /brand-safety /security
  content/usecases.py   # /use-cases/* ×8 ＋ハブ
  content/compare.py    # /compare/* ×6 ＋ハブ
  content/guides.py     # /guides/* ×5 ＋ハブ
  dist/                 # 出力（コミットしない）
```

## ビルド・確認

```
python3 site/build.py            # → site/dist/（54 ページ = 27 × 英日）
python3 site/build.py --serve    # http://localhost:5510/
```

生成物: 各ページの `index.html`（canonical / hreflang / OGP / JSON-LD をサーバ側 HTML に）、
`sitemap.xml`・`sitemap-ja.xml`・`sitemap-index.xml`、`robots.txt`、`llms.txt`、`og/spot-cover.png`、`urls.txt`。
英日のパスは 1 対 1 で、片方が欠けるとビルドが失敗する（hreflang の対を保証）。

## 公開前に置き換えるもの（`content/common.py`）

- `DOMAIN` — 本番ドメイン（現在 `creativepunx.com` は仮。`SITE` = `https://spot.<DOMAIN>`、`APP_URL` = `https://app.spot.<DOMAIN>/` が派生）
- `DEMO_URL` — デモ予約（現在は mailto）
- CTA は `app_link(campaign, plan)` で `utm_source=site&utm_medium=cta&utm_campaign=…&plan=…` を付けてアプリへ送る（アプリが登録時に保存）
- `org_jsonld()` の `sameAs` — G2 / LinkedIn / YouTube / X のプロフィール URL ができたら追加
- `PRICE_DATE` — 競合価格を再確認した日付。比較ページ・料金ページ・ガイドの「最終更新」に出る

## デプロイ

`dist/` をそのまま Vercel に配置（アプリと同じアカウント。手順は [`../docs/hosting.md`](../docs/hosting.md)。トレーリングスラッシュの URL＝`static/vercel.json` の `trailingSlash`）。
公開後:

1. Google Search Console と **Bing Webmaster Tools** に `sitemap-index.xml` を登録。
2. IndexNow: `openssl rand -hex 16 > site/indexnow.key` → 再ビルドで `dist/<key>.txt` が出る → `site/publish_indexnow.sh` で送信。
3. 旧 `spot-landing.html` の URL は `/` と `/ja/` に 301。

## コンテンツの運用ルール

- 価格・競合の数値は各社の料金ページから取り、必ずリンクを付ける。第三者情報は本文でそう書く。
- 8〜12 週ごとに競合価格を再確認し、`PRICE_DATE` を更新して再ビルド。
- 各ページの骨格（H1 = 検索意図 / 直答 / 表 / 数字＋出典 / FAQ / 更新日）を崩さない。
- 事例（/customers）は実顧客の許諾が取れてから追加する。架空の事例・体験談は載せない。
- デモ動画ができたら `VideoObject` を how-it-works と各 tools ページに追加する（`build.py` の head で対応）。
