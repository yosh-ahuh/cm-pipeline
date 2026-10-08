# SPOT app（Supabase 版・実働）

komadori の UI（ダーク・EN/JA）を土台に、**Supabase（認証・DB・Realtime・Storage）**へ接続した実働アプリ。
生成ワーカーは既存の Python `../cm-pipeline` を再利用する（次スライスで `jobs` テーブル駆動に接続）。

> ⚠️ Supabase を繋いだ時点で **claude.ai アーティファクトでは動きません**（CSPが Supabase 通信を遮断）。
> ローカル開発サーバ、または Cloudflare Pages 等でホストして動かします（本番の配置・ドメイン・Supabase URL 設定は [`../docs/hosting.md`](../docs/hosting.md)。`build.sh` が env から `config.js` を生成）。

## セットアップ

1. **Supabase プロジェクトを作成**（https://supabase.com → New project）。
2. **スキーマ適用**: Studio → SQL Editor に [`supabase/schema.sql`](supabase/schema.sql) を貼って実行。
   - テーブル（profiles/projects/generations/jobs/renders/credit_ledger）・RLS・トリガ・
     Realtime 公開・`assets` バケットまで一括で作成されます。
3. **メール認証を有効化**: Studio → Authentication → Providers → Email を ON。
   - 開発中は Authentication → Providers → Email の "Confirm email" を OFF にすると
     確認メールなしで即ログインできて楽（本番は ON 推奨）。
4. **接続情報を設定**: Studio → Project Settings → API から
   `Project URL` と `anon public` キーを取得し、`config.example.js` を `config.js` にコピーして記入。
   （`config.js` は `.gitignore` 済み。anon キーは公開前提なのでフロント配置でOK）

## ローカル起動

```
cd spot-app
python3 -m http.server 5500      # もしくは任意の静的サーバ
# → http://localhost:5500 を開く
```

`config.js` が未設定だと、ログイン画面に「Supabase 未設定」と出て入力が無効化されます。
正しく設定すると **登録 → ログイン** ができ、ログイン後に既存の komadori UI（ダッシュボード等）が表示されます。

## 構成

```
spot-app/
  index.html            # アプリ本体（komadori UI + 認証オーバーレイ + supabase-js）
  config.example.js     # 接続情報テンプレ（config.js にコピーして記入）
  supabase/schema.sql   # DBスキーマ・RLS・トリガ・Storage・Realtime
  worker/               # （次スライス）jobs を購読して生成する Python ワーカー
```

## 生成ワーカー（本番）

`jobs` を処理する Python ワーカー。**service_role キー**を環境変数から読み、PostgREST 経由で
RLS を貫通して全プロジェクトの pending ジョブを進める（Web の DEV ランナーのサーバ版）。

```
cd worker
cp .env.example .env && $EDITOR .env    # SUPABASE_URL と SUPABASE_SERVICE_ROLE_KEY を記入
source .env
python3 worker.py            # 全プロジェクトの pending を処理して終了（既定 DRY-RUN）
python3 worker.py --watch    # 5秒間隔で常駐
python3 worker.py --live     # 実生成: cm-pipeline のステージを実行し assets へアップロード（FAL_KEY or ../../.fal_key）
# 台本ステージ（script）: --live かつ ANTHROPIC_API_KEY があれば Claude（claude-opus-5-5）が台本を書く。無ければテンプレート台本。
# 検品ステージ（review）: --live かつ ANTHROPIC_API_KEY があれば Claude が各スチルを 9 項目（指・小道具・光・文字・一貫性・コラージュ化・日本考証・実在人物・偽UI）で判定。NG は 1 回作り直して再検品。キー無しは通過。
#   依存: cm-pipeline/.venv/bin/python -m pip install -r worker/requirements.txt
# ブランド取り込み（brand_sources.status=pending）も同じループで処理。python3 worker.py --brand <brand_id> で単体実行。
```

### 常駐（コンテナ／Railway）

リポジトリ直下の `Dockerfile`（cm-pipeline ＋ Remotion ＋ ffmpeg ＋ 日本語フォント同梱）と `railway.toml` を使う。ワーカーは **1 台だけ**動かす（複数台やローカル同時起動は同じ jobs を取り合う）。

```bash
docker build -t spot-worker .                                   # 初回は手元で一度ビルドを通す
docker run --env-file spot-app/worker/.env -e FAL_KEY=... -p 8080:8080 spot-worker
railway link --project Spot && railway up                        # Railway（変数はダッシュボードで設定）
```

必要な変数: `SUPABASE_URL` `SUPABASE_SERVICE_ROLE_KEY` `FAL_KEY`。任意: `ANTHROPIC_API_KEY`（台本・検品・ブランド要約）、`RESEND_API_KEY` `RESEND_FROM` `APP_URL`（完了メール）、`STRIPE_WEBHOOK_SECRET`、`WORKER_MODE=dry`（ドライラン）、`STRIPE_WEBHOOK=0`（Webhook を同居させない）。
`/healthz` がヘルスチェック。生成物は `/app/cm-pipeline/projects` に出るので、残したければボリュームをマウントする。

`--live` の流れ: `projects.spec` → `cm-pipeline/projects/_supabase/<project_id>/project.yaml` に写像 →
still / review（NG なら 1 回再生成）/ animate / audio / build を実行 → 生成物を `assets/<owner>/<project>/` に
アップロードし `generations`（スチル・クリップ・音声）と `renders`（媒体別 mp4）に記録。
build は `spec.compliance` / `spec.delivery` を読んで、AI 利用開示テロップ・C2PA マニフェスト・媒体別セーフゾーン・
ラウドネス正規化を適用する（`cm-pipeline/styles/platform-specs.yaml`）。`_supabase/` はワーカーの作業領域（消してよい）。

> `SUPABASE_SERVICE_ROLE_KEY` はサーバ専用。フロント（config.js）やチャットに絶対に出さないこと。

## UI/UX 方針（2026-09-10 改修）

Material Design 3 と Apple HIG を基準に `index.html` の `<style>` 先頭でデザイントークンを定義している。新しい UI を足すときはトークンを使う。

| 領域 | 決めごと |
|---|---|
| 色 | M3 のトーナルサーフェス 5 段（`--ground` → `--surface-3`）。テキストは `--ink` / `--muted` / `--faint` の 3 段で、いずれも `--surface` 上で 4.5:1 以上。`--outline` は装飾専用（文字に使わない） |
| 文字 | `--t-display` 32 → `--t-label-sm` 11 の 9 段。11px 未満は使わない |
| 余白・形 | 4pt グリッド（`--s-1`〜`--s-10`）。角丸は `--r-xs` 6 / `--r-sm` 8 / `--r-md` 12 / `--r-lg` 16 / `--r-xl` 24 |
| 操作対象 | 最小 40px、タッチ環境では 44px（`--target`）。ボタンは `.btn` 44px、アイコンボタンは `.icon-btn` |
| 状態 | hover 8% / pressed 12% のステートレイヤー（`--hover` / `--pressed`）。`:focus-visible` で全要素にフォーカスリング |
| モーション | `--ease-standard` / `--ease-emphasized`、120 / 200 / 320ms。`prefers-reduced-motion` で全停止 |
| アイコン | `<body>` 直下の SVG スプライト（`#i-check` など）を `<svg class="ic"><use href="#i-…"/></svg>` で参照。絵文字・記号は使わない |
| ナビ | 上部バーは「戻る」＋クリックできるパンくず（`setCrumb`）。Esc でも戻る。ビュー切替時は新ビューへフォーカス移動 |
| キーボード | タブ・ラジオ・セグメント・フィルタ・カット列は矢印キーで移動（`roving`） |
| アカウント | サイドナビは置かず、上部バーのユーザーチップ（`#userChip`、`aria-haspopup="menu"`）から M3 メニュー / HIG ポップオーバー（`#acctMenu`、`role="menu"`）を開く。ヘッダにアバター・メール・プランバッジ・クレジット残メーター（`.u-meter`）、項目は 44px 行＋先頭アイコン（プロフィール・設定 / プランと請求 / クレジットを追加 / サインアウト）。クリック・Enter・Space・↓↑で開き、Esc・外側クリック・項目選択で閉じてチップへフォーカス復帰（メニューが開いている間は Esc で戻らない）。720px 以下はボトムシート。表示値はデータ層が `window.onAccountInfo({ email, plan, credits, max })` で更新、チップは `window.mountUserChip(email)` が生成 |
| モバイル | 720px 以下: 単一カラム、ウィザード / 書き出しの操作ボタンは下部固定バー、納品ファイルはリスト行、言語切替は `JA` 短縮 |
| i18n | 表示文字列は日本語をソースにし、辞書 `D` で英訳。JS で文字列を差し替えるときは `textContent`（新ノード生成）にする |

## 実装状況 / 次の一手

- [x] 認証（メール＋パスワードの登録/ログイン/ログアウト、セッション維持）
- [x] スキーマ・RLS・Storage・Realtime 公開
- [x] データ配線: ダッシュボードが `projects` を表示、ウィザードが project を作成
- [x] 生成: 「Generate」で `jobs`（still→review→animate＋audio＋build のDAG）を投入 →
      ワークスペースが **Realtime** で進捗表示、`credit_ledger`→残高減算まで動作
- [x] ワーカー: `worker/worker.py`（DRY-RUN で jobs を進める本番ループ。実行は service_role 必要）
- [x] **クレジットモデルの確定**＋生成前の**残高ガード**: 1 credit = 1 spot（完成CM 1本 = 3パターン×3フォーマット = 9ファイル）。
      `plans` / `credit_costs` テーブル、`profiles.plan`、残高ガード付き `spend_credits` RPC、`log_cost` RPC、
      `reset_monthly_credits` / `set_plan`（service_role 専用）、profiles.credits/plan の改ざん防止トリガ、
      台帳の書き込みを関数経由に限定。既存 DB は [`supabase/migrations/002_plans_credits.sql`](supabase/migrations/002_plans_credits.sql) を適用。
      料金設計の根拠は [`../spot-marketing.html`](../spot-marketing.html)、公開価格は [`../site/content/common.py`](../site/content/common.py) の `PLANS` と一致。
- [ ] 課金: Stripe（USD）/ 請求書（JPY）→ webhook で `set_plan`、月次 cron で `reset_monthly_credits`
- [ ] 追加スポット購入（`plans.extra_spot_usd`）と 再レンダ 0.25 / カット再生成 0.1 の消費を UI に配線
- [x] ワーカー `--live`: cm-pipeline のステージ＋`assets` Storage アップロード（`LiveRunner`）。実案件のコンポジションができるまで build は `MiraiCM` をテンプレとして使う
- [x] 上部の使用状況カード: Ads made / Credits はプラン付与量（plans.spots_per_month）を分母に実データ化済み
- [x] ワークスペースを対象プロジェクトで描画: クラム・タイトル・メタ（業種/媒体/尺/トーン）・カット構成（spec.cuts）・生成進捗（jobs Realtime）を実データ化。※プレビュー映像/バリアント/品質チェックは生成物ができるまでサンプル表示
- [x] アカウント画面: プロフィール・設定（表示名保存=update_display_name RPC）／プランと請求（現在プラン・メーター・plans一覧）を実装。要 002_plans_credits + 003_profile 適用
- [x] 生成原価の非表示化: ユーザー向けは「消費クレジット」表示に統一（¥/原価/料金/外注比較を撤去）
- [x] テーマ: **ライトを既定**（灰の地×白カード×境界・影で階層＝メリハリ）＋ダークはトグル（◐, localStorage 永続）。低ITリテラシー向けフィードバック反映
- [x] 低ITリテラシー向けUX: 専門用語の言い換え（処方箋→おすすめ構成 / 検品→チェック / 訴求→伝え方 / 媒体→配信先 / 尺→長さ / テロップ→字幕）、用意する素材のアップロード説明、初回オンボーディング（3ステップの歓迎ガイド・localStorage 記録・主アクション1つ）。EN/JA 両対応
- [x] 課金（コード完成・**あなたのStripe設定で有効化**）: アップグレード／追加スポット購入を **Stripe Payment Link 方式**で配線（`config.js` の `stripeLinks` に URL を入れるだけ）。支払い反映は `worker/stripe_webhook.py`（署名検証→`set_plan`/`add_credits`）。消費目安（credit_costs）も表示。

## セットアップ（残り：あなたの操作）

**1) DBマイグレーション（1回）** — 設定保存・請求・使用状況カードのライブ化に必須。
Supabase Studio → SQL Editor に **[`supabase/migrations/APPLY.sql`](supabase/migrations/APPLY.sql)** を貼って Run（002+003+004 を一括・冪等）。

**2) 課金（Stripe。任意・収益化する時）**
1. Stripe ダッシュボードで各プラン／追加スポットの **Payment Link** を作成。
   - 各リンクの **metadata** に `plan=starter|team|business|enterprise`（プラン）または `extra_spots=1`（追加本数）を設定。
   - リンク設定で **client reference ID を許可**（アプリが Supabase ユーザーid を付与します）。
2. 作成した URL を `config.js` の `stripeLinks` に貼る（[`config.example.js`](config.example.js) 参照）。
3. 反映用の **Webhook** を起動: `worker/stripe_webhook.py`（`STRIPE_WEBHOOK_SECRET` / `SUPABASE_*` を env に）。Stripe の Webhook を `checkout.session.completed` で `https://<host>/stripe/webhook` に向ける。
   → 支払い完了で `set_plan`（プラン変更）/ `add_credits`（追加スポット）が自動反映。

> service_role キー・`STRIPE_WEBHOOK_SECRET` はサーバ専用。フロント（config.js）には**publishable/anonのみ**。
- [x] **複数ブランド**（アカウント＞ブランド＞コレクション＞動画）: [`supabase/migrations/023_brands_multi.sql`](supabase/migrations/023_brands_multi.sql) を適用すると、
      Team 以上で複数ブランド（製品/クライアント）を作成・切替・名前変更・読取専用化・削除できる。上限は `plans.brands`（Free/Starter 1・Team 3・Business 10・Enterprise ∞）、
      コレクション上限は `plans.collections`（Free のみ 12/ブランド）。動画・コレクション・ブランドメモリはブランド単位。⚠ 適用順: 021 → 022 → 023。
- [x] ブランド単位のアクセス範囲（招待・メンバー）: [`supabase/migrations/024_brand_members.sql`](supabase/migrations/024_brand_members.sql)。席はアカウント全体のユニーク人数のまま、
      メンバーごとに「見える/作れるブランド」を限定できる（招待時の選択・チーム画面で変更）。⚠ 適用順: 023 → 024。
- [x] 用語統一: アカウント（org）／ブランド／コレクション／制作画面／サインイン（docs/design-system.md §7b）
- [x] 共有リンク・一括 ZIP・完了メール（[`supabase/migrations/025_share_notify.sql`](supabase/migrations/025_share_notify.sql)）:
      共有＝ `share.html?t=<token>`（サインイン不要・30日・取り消し可。裏側は Edge Function `share`＝`supabase functions deploy share --no-verify-jwt`）、
      ZIP＝書き出し画面で実レンダーをブラウザ内でまとめて保存、完了メール＝ワーカーが Resend で送信（`RESEND_API_KEY` / `RESEND_FROM` / `APP_URL`）。自動チャージ UI は非表示。
- [ ] AIカット生成: `spec.cuts` を自動生成（現状は既定カットセットで代用）
- [x] 配信前チェック（書き出し画面）: AI利用表記（JIAA 2026-04）・C2PA の ON/OFF を `spec.compliance` に保存、媒体仕様を表示
- [x] ワーカー build: `spec.compliance` / `spec.delivery` → 開示テロップ焼き込み（`ad-prototype/src/Compliance.tsx`）・C2PA マニフェスト（c2patool があれば埋め込み、無ければ `.c2pa.json` サイドカー）・媒体別セーフゾーン／ラウドネス（`cm-pipeline/cm/delivery.py`）
- [x] 料金プラン: `plans` テーブル（002_plans_credits.sql）＝ `site/content/common.py` PLANS ＝ `spot-landing.html #pricing`（Free / Starter $99 / Team $399 / Business $1,199 / Enterprise）
- [x] 実案件ごとのコンポジション: 汎用 `SpotAd`（`ad-prototype/src/SpotAd.tsx`）＋ `cm/remotion_props.py`。spec → project.yaml → props で TSX 不要
- [x] c2patool 導入（brew）。埋め込み署名まで動作。本番用の署名証明書は **保留（プロダクト完成後に商用 CA から購入、2026-09-10 決定）**。それまではテスト証明書。切替は `C2PA_SIGN_CERT` / `C2PA_PRIVATE_KEY` の設定のみ
- [x] 撮影指示リスト: UI カットのスクショ／アプリアイコン／ロゴを `assets/<uid>/<project>/{ui/<cut>|brand}/` にアップロード →
      `spec.cuts[].assets` / `spec.brand` に配線。ワーカーが `assets/` にダウンロードして SpotAd の UI カットに合成

## 競合調査の反映（2026-09-10）

`../research/competitive-research-2026-09.md` の推奨アクションを、次のとおりプロダクトに落とした。

| 推奨 | 反映先 |
|---|---|
| ポジショニング「実UIを織り込む B2B SaaS/アプリ専用の AI CM スタジオ」 | `spot-landing.html` ヒーロー・SEO・フッター（EN/JA） |
| 5軸の比較表を営業資料化 | `spot-landing.html` `#compare`（カテゴリ比較・社名なし） |
| 空白帯の価格（1本 ¥3〜15万） | `spot-landing.html` `#pricing` の4プラン、JSON-LD offers |
| 「+120 teams」を降ろす | `spot-landing.html` ロゴ帯 → デザインパートナー募集＋実案件1件の事実 |
| 法務を武器に（AI開示・C2PA・肖像権） | 本アプリ 書き出し画面「配信前チェック」、`cm-pipeline` の `compliance` ブロック・quality-rules D3〜D8 |
| 媒体連携ロードマップ | `cm-pipeline/styles/platform-specs.yaml`（入稿仕様をデータ化）、`spec.delivery` |

