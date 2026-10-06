# 案B モック → 実装の改修範囲（2026-10-06）

基準モック: キャンバス「SPOT ブランドを登録」（案B 本線ページ、13 画面＋モバイル 2 画面）。
対象コード: `spot-app/index.html`（単一ファイル・約 7,600 行）、`spot-app/supabase/migrations/`、`spot-app/worker/worker.py`、`cm-pipeline/`。
関連設計: [brand-intake.md](brand-intake.md)、[brand-memory.md](brand-memory.md)、[design-system.md](design-system.md)（§4 画面インベントリ・§7b 用語）。

**結論**: サイドバー・アカウント／ブランドモデル・台本画面・素材アップロード・書き出しはすでに実装があり、**作り直しではなく「順序の組み替え＋新規 3 画面＋バックエンド 2 本」**で足りる。新規要素は (1) ブランド取り込み、(2) 台本生成ステージ、(3) 目的／相手の複数選択。

---

## 1. 画面対応表

| # | モック画面 | 現行 view | 種別 | 主な変更 | 規模 |
|---|---|---|---|---|---|
| 0-1 | ブランドを登録（入力） | なし（`view-settings` 内 `#brandPanel` に名前・ロゴのみ） | **新規** | 新 view `view-brand-intake`。URL 複数・自由記述・ファイル複数（PDF/PPTX/画像）。すべて任意。未入力なら 3 問フォーム | M |
| 0-2 | こう理解しました（確認） | なし | **新規** | 新 view `view-brand-card`。項目ごとの確度・「直す」「追加」「項目を追加」・製品画面候補の選択。保存で `brands.profile.confirmed_at` | M |
| 1 | ホーム | `view-dash` | 改修 | ヒーロー＋使用状況カード → **「続きから」カード（次にやること・進捗）＋「目的から作る」複数選択＋自由入力＋最近のCM 一覧**。使用状況はサイドバー下部のメーターへ集約（既存） | M |
| 2 | 作成（7 ステップ） | `view-wizard`（4 ステップ） | 改修 | ステップ再編（§2）。業種ステップ廃止（ブランドから継承）。目的・相手を**複数選択＋自由入力**（`data-multi` 拡張＋チップ）。左の進捗列に CM 名と「名前を直す」 | M |
| 3a | 台本を確認（AI） | `view-script`（台本と絵コンテ） | 改修 | カードを「ナレーション／文字／必要な素材」の 3 行構成に。**素材パネルをこの画面から外す**（→ 4）。「言葉で直す」は既存の編集を流用。右に「この台本で必要な素材」 | S〜M |
| 3b | 台本を確認（持ち込み） | `view-script` の `#ownScript` | 改修 | 既存の貼り付け／TXT に **DOCX・PDF・動画音声**を追加。貼り付け後に**カット分割**（行頭「カット n:」優先、無ければ AI 分割）して 3a と同じカード表示へ。読み方辞書の適用表示 | M |
| 4 | 素材をアップ | `view-script` 右の `#shotList`（`renderShotList`） | 改修・移動 | 独立ステップ `view-assets` に移動。**台本が要求するカットだけ**表示（`cuts[].assets_required`）。ロゴは `brands.assets.logo` から自動。音楽参考に YouTube URL 欄。ブランドで拾った画面候補から選ぶ導線。不足中は「次へ」無効＋理由 | M |
| 5 | 初稿を確認（3 案） | `view-workspace`（制作画面） | 改修 | 3 案カード（再生・この案にする）＋言葉で直す＋確認ポイントを主役に。制作パイプライン・QC・原価は**折りたたみの補助情報**へ格下げ（削除はしない） | M |
| 6 | 完成・ダウンロード | `view-export` | 小改修 | 文言を平易化（配信前の設定 2 項目・次にやること）。機能は既存（ZIP・共有リンク・完了メール済） | S |
| M-1 | モバイル ホーム | `view-dash`（720px 以下） | 改修 | **ボトムナビ 4 項目**を追加（ホーム／作る／マイCM／ガイド）。サイドバーは 720px 以下で非表示 | S〜M |
| M-2 | モバイル 素材をアップ | — | 改修 | 下部固定の主ボタン（既存の `.wiz-nav` sticky を流用） | S |
| 参考 | 案A・案C | — | 対象外 | — | — |

---

## 2. 作成フローの再編

| 新ステップ | 現行 | データ（`projects.spec`） | 備考 |
|---|---|---|---|
| 1 流す場所 ＝ 書き出し形式 | 配信先（既存） | `selections.media[]`、`output.formats[]`（既存） | ラベルに「＝書き出し形式」を明示 |
| 2 目的 | なし（ホームの入口のみ） | **新規** `selections.goals[]`（選択肢 ID＋自由入力文字列） | ホームの「目的から作る」で選んだ値を初期値に |
| 3 届ける相手 | ターゲット（単一） | `selections.target` → **`targets[]`** に変更（旧値は配列化して互換） | 筆頭の相手で冒頭 2 秒を決める |
| 4 伝えたいこと | 伝え方・トーン（既存） | `selections.angle`、`selections.tone`（既存） | 「訴求」は使わない（§7b） |
| 5 台本を確認 | 台本と絵コンテ | **新規** `script.cuts[]`（§3） | AI／持ち込みの切替は既存 `#scriptMode` |
| 6 素材をアップ | 台本画面内の素材パネル | `cuts[].assets`（既存）＋ `audio.reference{file\|youtube}`（新規） | 台本確定後にのみ到達 |
| 7 初稿を確認 | 制作画面 | `renders`（既存）、`projects.approved`（既存） | 3 案＝イントロ演出と音楽の差（既存の A/B/C） |
| — 業種 | 業種（削除） | `selections.industry` は **ブランドプロフィールから自動設定** | プロフィール未確認時のみ従来の選択肢を出す |
| — CM の名前 | 自動命名 `projectName()` | `meta.name` | 作成開始時に入力（既定: ブランド名＋目的＋日付）、進捗列で変更可 |

`__brandDefaults()`（ブランドメモリ Phase 1）は、履歴 2 本未満のとき `brands.profile.defaults` を使うように拡張する。

---

## 3. データ・バックエンド

### 3.1 スキーマ（新規マイグレーション 026）
- `brands.profile jsonb`（[brand-intake.md §3.1](brand-intake.md)。`custom[]` を含む）。確定時に `brands.assets.logo/colors` へ同期。
- `brand_sources` テーブル（同 §3.2）＋ RLS（org メンバー読取、owner/member 作成・削除）＋ Realtime 公開。
- `projects.spec` は JSONB のため列変更なし。`selections.targets[]`、`selections.goals[]`、`script.cuts[]`、`audio.reference` を追加（旧 `target` 文字列は読み取り側で配列化）。
- Storage: `assets/<org_id>/brand/<brand_id>/sources/…`（取り込み元ファイル）。既存の `<org_id>/<project>/…` 規約に合わせる。

### 3.2 ワーカー（`worker/worker.py`）
| 処理 | 種別 | 内容 |
|---|---|---|
| `brand_ingest` | **新規ループ** | `brand_sources.status='pending'` を拾い fetch → extract → summarize → `brands.profile` 更新。LLM 1〜2 回。詳細は brand-intake.md §4 |
| `script` ステージ | **新規ステージ** | `still` の前段。`selections`＋`brands.profile`（ひとこと・価値・文体・読み方・NG）から `script.cuts[]`（ナレーション・文字・秒数・必要素材）を生成。持ち込み台本は分割のみ（文章は変えない）。**現状、台本テキストはデモ固定（`SCUT`）で実生成が無い**ため、ここが最大の新規実装 |
| `audio` | 改修 | `audio.reference.youtube` は URL のメタ情報（タイトル・ジャンル推定）だけを参照に使い、音源は取得しない |
| `build` | 改修 | `brands.profile.visual.colors` をレンダーのスタイル入力に（ブランドメモリ Phase 2 の一部） |

ジョブ DAG: `script → (still → review → animate)×実写カット → audio → build`。`script` 完了までは素材ステップに進めない（UI 側で `jobs.stage='script'` の完了を待つ）。

### 3.3 UI ⇄ データの配線（index.html）
- `onWizardComplete`: `goals[]`／`targets[]`／`meta.name` の保存、`generateCuts` は役割列のみ（従来どおり）→ `script` ジョブ投入へ変更。
- `renderBoard`: `script.cuts[]` の narration/caption/assets_required を描画（現行の `boardFromCuts` を拡張）。
- `renderShotList` → `view-assets` へ移設。`assets_required` が空のカットは出さない。
- `applyBrandDefaults`: プロフィール既定値の優先順位（お手本 ＞ 履歴 ＞ プロフィール ＞ デモ既定）。

---

## 4. 既存機能の扱い

| 既存 | 扱い |
|---|---|
| ホームの「何の広告をつくりますか?」配信先選択 | 削除（作成ステップ 1 に一本化） |
| ウィザード「業種」 | 削除（ブランドから継承。未確認ブランドのみ表示） |
| 台本画面の素材パネル | ステップ 6 へ移動（コードは流用） |
| 制作画面のパイプライン・QC・原価パネル | 残すが折りたたみ既定・補助情報の見た目に |
| 「AIにおまかせ／台本を持ち込む」 | 残す（3a／3b の切替） |
| `projectName()` 自動命名 | 既定値生成に格下げ（入力欄を追加） |
| `#brandPanel`（ブランド名・ロゴ） | ブランドカード常設＋「もう一度学習する」「取り込み元を見る」を追加 |
| i18n 辞書 `D` | 新規文言をすべて JA ソース＋EN 訳で追加（既存規約） |

---

## 5. 段階計画

| フェーズ | 内容 | 依存 | 規模 |
|---|---|---|---|
| **P1 フロー再編（UI のみ）** ✅ 2026-10-06 `feat/p1-flow` | ステップ 7 化、目的／相手の複数選択＋自由入力、CM 名、素材ステップの独立（`view-assets`・必須素材のゲート・音楽参考 MP3/YouTube）、台本カード 3 行化＋持ち込み台本のカット分割、初稿確認の主役化、ホーム（続きから／目的から作る）、モバイルのボトムナビ | なし | L |
| **P2 ブランド取り込み（UI＋DB）** ✅ 2026-10-06 `feat/p1-flow` | `027_brand_intake.sql`（brands.profile・brand_sources・RLS・Realtime、⏳ 適用待ち）、入力／読み込み中／確認の 3 画面、3 問フォールバック、ホームの CTA、「新しく作る」初回ゲート（スキップ可）、設定のブランドカード、ウィザード既定値の profile フォールバック。ワーカー未接続時は 3 問と手入力だけで保存できる | P1 と独立 | M |
| **P3 ワーカー: brand_ingest** ✅ 2026-10-06 `feat/p1-flow` | `worker/brand_ingest.py`: URL（robots.txt 尊重・15 秒・2 MB）／自由記述／PDF（pypdf）／PPTX／画像を取り込み、Claude でプロフィール（スキーマ出力）。キー無し・失敗時はヒューリスティック（確度 low）。色・ロゴ候補・画面候補を補充、ロゴ候補は Storage へ保存。確認済み項目は上書きしない。`worker.py --watch` の同じループで処理（`--brand <id>` で単体実行） | P2、`--live` 環境 | M |
| **P4 ワーカー: script ステージ** ✅ 2026-10-06 `feat/p1-flow` | `worker/script_gen.py`: Claude（Anthropic SDK・`claude-opus-5-5`・JSON schema 出力）で台本、キー無し／失敗時はテンプレート台本。持ち込みは文章を変えず分割。秒数配分・文字・必要な素材・読み方辞書（TTS 用）。`jobs.stage='script'` をウィザード完了時に投入（クレジット消費なし）、生成 DAG は script 完了に依存。アプリは Realtime で台本画面を更新、60 秒で「素材へ進める」案内 | P1、P3（プロフィール参照） | L |
| **P5 生成への注入** ✅ 2026-10-06 `feat/p1-flow` | アプリは案件作成時に `spec.brand`（名前・ロゴ・色・ひとこと・読み方・見た目・言葉づかい・NG）を書き、ワーカーは最新の `brands.assets/profile` で補完（`merge_brand`）。色は Remotion の primary/accent/dark、ロゴ・アイコンは Storage から取得、読み方は配信レポートへ。実写スチルにはブランドカラーを差し色として控えめに指示（`compose.still_prompt`）。お手本案件（approved）の生成スチルを `brand.references` として同梱（人物一貫性・スタイル参照の土台） | P3、P4 | M |

P1 と P2 は並行可能。ユーザーが体感できる順は P1 → P2 → P4 → P3 → P5。

---

## 6. リスク・未決

- **台本生成の品質**: 現行は固定デモ。LLM の呼び先（fal か別 API）とプロンプト設計、生成失敗時の既定台本（現 `ANGLE_STRUCT`）へのフォールバックを決める。
- ✅ **複数ターゲット時の構成**（2026-10-07）: 届ける相手は **3 つまで**（4 つ目はトーストで拒否、自由入力も合算）。冒頭は最初に選んだ相手に合わせる。
- ✅ **持ち込み台本の分割**（2026-10-07）: 貼付欄の説明に「カット1:」「#1」規約と空行分割（最大 8）を明記。入力中に尺の目安（日本語 5 文字/秒・英語 15 文字/秒）を表示し、32 秒超は警告（止めない。反映時にも注意トースト）。
- ✅ **モバイルのボトムナビとサイドバー**（2026-10-07）: ボトムナビ 4 番目を「その他」にし、アカウントメニューの上部にモバイル限定の「メニュー」群（メディア・コレクション・チーム・請求）を表示。ガイド（ヘルプ）も同メニュー内。
- ✅ **DB 適用**: 024〜029 適用済み（2026-10-07）。022（メンバー一覧のメール・アイコン）のみ未適用。
- **クレジット**: 形式数は消費に影響しない（確認済み）。`script` ステージの LLM 費用はクレジット外（運営コスト）とする想定。
