# ブランド取り込み（Brand Intake）設計

**ブランド＝動画を作る単位。動画を作る前に、AI がそのブランドを知っている必要がある。**
本書は、ブランド作成時に URL・SNS・資料からブランドを学習し、確認を経て「ブランドプロフィール」として保存し、以後の生成に効かせる機能の設計（2026-10-06 ユーザー合意）。

既存の [ブランドメモリ](brand-memory.md) は「過去に作った動画から学ぶ」設計で、履歴が 2 本たまるまで何も効かない（コールドスタート）。本機能はその**前段**として、初日からブランドの参照コーパスを用意する。ブランドメモリ Phase 2（ワーカーへの参照注入）は、本機能が作るプロフィールをそのまま消費する。

関連: [workspace-brand-model.md](workspace-brand-model.md)（用語）、[brand-memory.md](brand-memory.md)、[consistency-audit.md](consistency-audit.md)（正直さ方針）、[design-system.md](design-system.md) §7b（用語統一）。

---

## 1. 用語と位置づけ

| 用語 | 実体 | 備考 |
|---|---|---|
| アカウント | `organizations` | 請求・席の単位 |
| ブランド | `brands` | **動画を作る単位＝1 製品**。アカウント内に複数（023/024） |
| ブランドプロフィール | `brands.profile`（本機能で追加） | AI が学んだ「ブランドの理解」。ユーザー確認済みの構造化データ |
| 取り込み元 | `brand_sources`（本機能で追加） | URL・貼り付けテキスト・ファイル。再学習の履歴 |

画面上の呼び方は「ブランドを登録」「ブランドを学習」とし、「ワークスペース」は使わない（§7b）。

---

## 2. ユーザーフロー

### 2.1 入口
- **アカウント作成直後**: 最初のブランド作成＝「ブランドを登録」ステップ。はじめてガイドの 1 番目。
- **ブランドを追加**（2 つ目以降）: 同じステップ。
- **初回の動画作成**: プロフィール未確認のブランドで「新しく作る」を押したら、ウィザードの前に同ステップを挟む（スキップ可、後述）。
- **再学習**: ブランド設定画面の「もう一度学習する」。取り込み元の追加・差し替え。

### 2.2 画面 1「ブランドを登録」（入力）
- 必須は **Web ページの URL ひとつ**（サービス紹介・会社トップ・記事・プレスリリースのいずれか）。URL は**複数追加できる**リスト UI。
- 任意: SNS の投稿文の貼り付け（複数）、ファイル（**PDF / PPTX / 画像 PNG・JPG**、複数選択可）。いずれも「多いほど正確になる」と添えるだけで、止めない。
- URL が無い場合の逃げ道「URL がない・読み取れない」→ 3 問の手入力（何のサービスか／誰向けか／雰囲気）で最小プロフィールを作る。
- 主役ボタンは「読み込んで学習する」1 つ。所要の目安「約 1 分」を添える。
- 注意書き（1 行）: 「公開されている情報だけを読みます。あとから直せます。」

### 2.3 画面 2「読み込み中」
- 進捗を工程名で見せる: ページを読む → ロゴと色を探す → 文章を読む → まとめる。Realtime（`brand_sources.status`）で更新。
- 失敗時はその場で理由を平易に（「このページは読み取りを拒否しています」「ログインが必要なページです」）、代替（別の URL／3 問入力）を提示。

### 2.4 画面 3「こう理解しました」（確認＝必須）
学習結果を**ブランドカード**として表示し、各項目をその場で直せる。黙って適用しない。

| 区画 | 項目 | 表示 |
|---|---|---|
| 見た目 | ロゴ候補（最大 3）、主要色（2〜3 色のスウォッチ）、写真かイラストか | 候補から選ぶ／色はカラーピッカー |
| ひとこと | サービスのひとこと説明（40 字以内） | テキスト編集 |
| 誰に | 想定顧客（1〜2 行） | テキスト編集 |
| 伝えたいこと | 主要な価値・機能（3 つまで） | チップ、追加・削除 |
| 言葉 | 文体（ていねい／くだけた）、よく使う語と読み方、使わない表現 | セグメント／リスト編集 |
| 動画の初期設定 | 業種・ターゲット・トーン（ウィザード既定に直結） | 既存の選択肢と同じカード |
| 素材 | 公開サイトから拾った製品画面の候補 | 「素材として使う」チェック |

- 項目ごとに **確信度**（高／要確認）。「要確認」は黄色で目立たせ、上部に「要確認が N 件あります」。
- 各項目は「直す」で編集、リスト項目（色・相手・伝えたいこと・読み方・NG 表現）は「追加」で増やせる。足りない観点は「項目を追加」で**ユーザー定義の項目**（例: 競合との違い、キャッチコピー、料金の言い方）を足せる → `profile.custom[]` に `{label, value}` で保存し、生成時は台本の制約として渡す。
- 主役ボタン「この内容で保存」1 つ。副は「もう一度読み込む」「あとで直す」。
- 保存後は `brands.profile.confirmed_at` を立てる。未確認のまま離脱した場合はカード自体は保存するが「未確認」扱い（ウィザードの既定には使わない）。

### 2.5 保存後の効き方
- **ウィザード既定**: 業種・ターゲット・トーンがプロフィールから入る（ブランドメモリ Phase 1 の `__brandDefaults` は、履歴 2 本未満ならプロフィール値を使う）。
- **制作フローの順序（2026-10-06 変更）**: 1 流す場所（＝書き出し形式をここで確定） → 2 目的 → 3 届ける相手 → 4 伝えたいこと → 5 **台本を確認** → 6 **素材をアップ（台本で決まったカット分だけ）** → 7 初稿を確認（3 案）。業種はプロフィールから引き継ぐので聞かない。目的・届ける相手は 8 択＋自由入力。CM の名前は作成開始時につける。
- **素材アップ**: 台本の各カットが要求する素材だけを求める。ロゴは「ブランドから自動」、製品画面はプロフィールの候補から選べる。音楽の参考は MP3 のほか **YouTube リンク**も受ける（雰囲気の参照のみ、音源は使わない）。
- **生成**: ワーカーがプロフィールを参照（ブランドメモリ Phase 2）。色・ロゴはレンダーのスタイル入力、ひとこと／価値／文体は台本生成の few-shot と制約、読み方は発音辞書、NG 表現はチェック項目。

---

## 3. データ

### 3.1 `brands.profile`（JSONB、本機能で追加）

```json
{
  "version": 1,
  "confirmed_at": "2026-10-06T09:00:00Z",
  "summary": { "one_liner": "現場写真を撮るだけで工事台帳ができるアプリ", "audience": "建設会社の現場監督", "values": ["持ち帰りゼロ", "台帳が自動", "その場で PDF"] },
  "visual": { "logo": "brand-assets/<id>/logo.png", "colors": ["#D7000F", "#1C1B1F", "#FFFFFF"], "imagery": "photo", "font_family": "sans" },
  "voice": { "register": "polite", "terms": [{ "text": "ミライ工事", "reading": "ミライこうじ" }], "avoid": ["業界最安"] },
  "defaults": { "industry": "SaaS・アプリ", "target": "現場担当", "tone": "ドキュメンタリー" },
  "screens": [{ "url": "https://…/shot1.png", "caption": "一覧画面", "use": true }],
  "custom": [{ "label": "競合との違い", "value": "紙の台帳からの移行が 1 日で終わる" }],
  "confidence": { "summary.one_liner": "high", "visual.colors": "low" },
  "learned_from": ["<brand_sources.id>", "…"]
}
```

- `brands.assets`（ロゴ等の既存キット）はそのまま。プロフィール確定時に `assets.logo` / `assets.colors` を同期する（既存の生成経路を壊さない）。
- 各項目には `confidence` を持ち、UI の「要確認」表示に使う。

### 3.2 `brand_sources`（新テーブル）

```sql
create table if not exists public.brand_sources (
  id          uuid primary key default gen_random_uuid(),
  brand_id    uuid not null references public.brands(id) on delete cascade,
  org_id      uuid not null references public.organizations(id) on delete cascade,
  kind        text not null,                 -- url / text / file（file は PDF/PPTX/PNG/JPG）
  url         text,                          -- kind=url
  text        text,                          -- kind=text（貼り付け）
  storage_path text,                         -- kind=file（assets バケット: <org_id>/brand/<brand_id>/…）
  status      text not null default 'pending',  -- pending/running/done/failed
  step        text,                          -- fetch/extract/summarize（進捗表示用）
  error       text,                          -- 平易な失敗理由
  extracted   jsonb not null default '{}'::jsonb, -- 本文要約・og 情報・色候補・画像候補（原文は保存しない）
  created_by  uuid references auth.users(id),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create index if not exists brand_sources_brand_idx on public.brand_sources(brand_id);
create index if not exists brand_sources_status_idx on public.brand_sources(status);
-- RLS: org メンバー＝読取、owner/member＝作成・削除（viewer 不可）。Realtime 公開。
```

- `jobs` は `project_id not null` で動画ジョブ専用のため流用しない。`brand_sources.status` 自体をキューにし、ワーカーが `pending` を拾う。
- 原文（HTML・PDF 全文）は保存しない。`extracted` には要約・構造化結果・画像 URL のみ。

---

## 4. 処理パイプライン（ワーカー側）

`worker.py` に `brand_ingest` ループを追加（`--watch` で `jobs` と同じ周期）。

1. **fetch**: URL を取得（タイムアウト 15 秒、robots.txt を尊重、リダイレクト 3 回まで、HTML 2 MB 上限）。ログイン必須・403・JS 専用描画は「読み取れない」として平易な理由を `error` に。
2. **extract**:
   - テキスト: title / meta description / og:* / h1〜h3 / 本文（readability 抽出）。
   - ロゴ候補: `<link rel=icon>`、og:image、`header` 内の `img`／`svg`。
   - 色候補: CSS の背景・ボタン・リンク色の出現頻度上位、ロゴ画像の主要色。
   - 画面候補: 本文中の `img`（幅 600px 以上、`alt`/周辺見出しを caption に）。
   - ファイル: PDF/PPTX はテキスト抽出＋画像抽出、画像は OCR なし（caption 用に周辺テキストのみ）。
3. **summarize**: 抽出結果を LLM に渡し §3.1 のスキーマへ構造化（JSON モード）。項目ごとに確信度を出させる。文体判定は本文の敬体率で補助。
4. **merge**: 既存プロフィール（確認済み）がある場合、ユーザーが直した項目は上書きしない（`confirmed_at` 以降の手修正を優先）。
5. 完了で `brand_sources.status='done'`、`brands.profile` を更新（`confirmed_at` は立てない。UI の確認で立つ）。

コスト目安: 1 回の取り込みで LLM 呼び出し 1〜2 回（数千トークン）。クレジット消費なし。

---

## 5. 制約・上限・法務

- 取り込み元: ブランドあたり URL 10 件・貼り付け 10 件・ファイル 10 件（画像含む、合計 50 MB）。Free は URL 3 件・ファイル 3 件。再学習は 1 日 5 回まで。
- 対象は**ユーザー自身のブランドの公開情報**。他社サイト（記事・レビュー）は要約のみ保存し本文は持たない。robots.txt の拒否は従う。
- SNS: X / Instagram / TikTok の API・規約上、自動取得はしない。投稿文の貼り付けとスクリーンショットで受ける。連携は将来。
- プロフィールはアカウント内で共有（ブランド単位のアクセス範囲 024 に従う）。削除はブランド削除に連動。
- 正直さ: 学習結果を自動適用しない。確信度を表示する。「AI が読み取った内容です。間違っていることがあります」を確認画面に常時表示。

---

## 6. 画面仕様（案B モックとの対応）

- 「ブランドを登録」「こう理解しました」は案B の制作フローの前段。モック: `SPOT レイアウト案` キャンバス「案B 本線」ページ 3 段目（`BrandIntake` / `BrandCard`）。
- はじめてガイドの 1 番目を「ブランドを登録」に差し替え、以降「流す場所 → … → 素材をアップ → 初稿を確認」。
- ブランド設定画面にブランドカードを常設し、「もう一度学習する」「取り込み元を見る」を置く。

---

## 7. 段階計画

| 段階 | 内容 | 依存 |
|---|---|---|
| A | スキーマ（`brands.profile`、`brand_sources`、RLS、Realtime）＋アプリ側 3 画面（入力／読み込み中／確認）。ワーカー未接続時は 3 問入力のみで保存できる | なし |
| B | ワーカー `brand_ingest`（URL・貼り付け）。ロゴ・色・要約・既定値 | A、ワーカー `--live` 環境 |
| C | ファイル取り込み（PDF/PPTX）、製品画面候補の収集 | B |
| D | 生成への注入＝ブランドメモリ Phase 2（色・ロゴ・few-shot・発音・NG） | B |
| E | 再学習と手修正の優先マージ、ブランド設定画面の常設カード | A〜D |

## 8. 未決事項

- LLM の呼び先（fal 経由か別 API か）とコストの計上先。
- 製品画面候補を素材として使う際の画質基準（幅・解像度）と、ログイン必須アプリの画面は結局ユーザーが撮る前提で良いか。
- 複数ブランド時、アカウント共通の「会社情報」（社名・請求先）とブランドプロフィールの重複をどう見せるか。
