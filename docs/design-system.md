# Spot デザインシステム / UI・UX ガイド

`spot-app/index.html`（Supabase 製 SPA）のUIを対象にした、**現状の棚卸し＋共通ルール＋改善ロードマップ**。
デザイナー・実装者が同じ基準で判断できるようにするための「単一の参照点」。

- 対象: `spot-app/index.html`（アプリ本体）。マーケサイト `site/build.py` は**別トークン体系**（§12）。
- 最終更新: 2026-09-21 / 由来: 実コードの棚卸し（`:root` トークン、コンポーネントCSS、11ビュー）。
- 凡例: ✅=現状OK / ⚠️=不整合・要改善 / 🐛=バグ。改善は §10 に優先度つきで集約。

---

## 1. デザイン原則

対象ユーザーは **ITリテラシーが高くない広告担当者**（`memory: spot-app-audience-low-it-literacy`）。「選ぶだけで広告動画」が価値。したがって:

1. **1画面＝1つの主アクション。** 主ボタンは画面に1つ。支援情報は視覚的に格下げする。
2. **平易な言葉。** 専門語（処方箋/検品/訴求/スポット等）を避け、成果物の言葉（CM・本・クレジット）で話す。
3. **迷わせない。** 入力・選択の隣に必ず補足（何を・どう）を置く。空状態は「次の一歩」を提示。
4. **状態は色でも伝える。** 数字だけでなく残量・成否をメーター色/バッジで冗長化。
5. **ダーク一本化。** ライトテーマは廃止（`color-scheme:dark` の単一パレット）。
6. **可逆・安全。** 破壊的操作は確認を挟む。権限（viewer/member/owner）で導線を出し分け。

---

## 2. 基盤トークン（Foundations）

すべて `index.html` の `<style> :root` にインライン定義。**色・寸法はハードコードせずトークンを使う。**

### 2.1 カラー

**面（tonal surfaces）** — 数字が上がるほど前面/明るい。
| トークン | 値 | 用途 |
|---|---|---|
| `--ground` | `#131318` | ページ地 |
| `--surface-low` | `#191920` | サイドバー・レール・くぼみ |
| `--surface` | `#1E1E26` | カード・パネル |
| `--surface-2` | `#25252F` | 入力欄・入れ子のくぼみ |
| `--surface-3` | `#2C2C37` | カード上のホバー |

**文字（on-surface）**
| `--ink` `#F1EDE4` 主要 | `--muted` `#A8A49A` 補助 | `--faint` `#8A867C` 三次 | `--outline` `#5A5866` 装飾線 |
|---|---|---|---|

**罫線**: `--line` `#2C2C37`（既定ヘアライン） / `--line-strong` `#3E3E4B`（明確な境界）

**ブランド／意味色**
| 役割 | トークン | 値 | メモ |
|---|---|---|---|
| プライマリ | `--accent` (+`-hover` `-ink` `-soft`) | `#4A67E3` | ブランド青。ink=文字用, soft=容器 |
| 補助 | `--cool` (+`-soft`) | `#4CC2B0` | ティール |
| 成功 | `--good` (+`-soft`) | `#6DB98C` | 潤沢・合格・完了 |
| 注意 | `--warn` | `#E4B14C` | 残少 |
| 危険 | `--crit` (+`-soft`) | `#E07A64` | 枯渇・失敗・削除 |
| 強調赤 | `--brand-red` | `#D7000F` | 実写カット等の限定用途 |

**状態レイヤー（M3）**: `--hover`（ink 6%）/ `--pressed`（ink 10%）
**影**: `--shadow-1`（カード）/ `--shadow`（浮上）/ `--shadow-lift`（ドラッグ・ホバー浮上）

> ⚠️ **`--on-accent` 以外の「色の上の文字色」規約が未整備。** バッジ等でアクセント面に文字を載せる時の色を規約化すべき（§10-F）。

### 2.2 タイポグラフィ

**書体**（Google Fonts）
- `--font-display` = Bricolage Grotesque（500/700/**800**）… 見出し・数字の主役
- `--font-jp` = Zen Kaku Gothic New（400/500/700/900）… 本文（日本語）
- `--font-mono` = DM Mono（400/500）… 数値・コード

**スケール**
| トークン | px | 用途 |
|---|---|---|
| `--t-display` | 32 | ヒーロー/ウィザード見出し |
| `--t-headline` | 26 | ページタイトル (`.title-h1`) |
| `--t-title-lg` | 20 | 設問 |
| `--t-title` | 16 | カード見出し・パネル見出し |
| `--t-body-lg` | 15 | 強めの本文 |
| `--t-body` | 14 | 本文 |
| `--t-body-sm` | 13 | 小本文・ボタン |
| `--t-label` | 12 | ラベル |
| `--t-label-sm` | 11 | 最小（下限） |

> ⚠️ mono に `font-weight:600/700` を当てている箇所があるが **DM Mono は 400/500 のみ読込** → 合成ボールドで滲む（§10-G）。

### 2.3 スペーシング（4pt グリッド）
`--s-1`4 / `--s-2`8 / `--s-3`12 / `--s-4`16 / `--s-5`20 / `--s-6`24 / `--s-8`32 / `--s-10`40
**基準**: パネル間=`--s-6`、パネル内=`--s-4`、密なリスト行間=`--s-2`。

### 2.4 角丸・影・コントロール高さ
`--r-xs`6 / `--r-sm`8 / `--r-md`12 / `--r-lg`16 / `--r-xl`24 / `--r-full`999。別名 `--radius`=r-lg(16), `--radius-sm`=r-sm(8)。
**基準**: ボタン/入力=`--r-sm`、カード=`--r-md`〜`--r-lg`、ピル=`--r-full`。
**コントロール高さ**（P2で追加）: `--control-h`40（入力/セレクト）/ `--control-h-sm`34（フィルタ）/ `--control-h-lg`44（ボタン）。

### 2.5 モーション
`--ease-standard` `cubic-bezier(.2,0,0,1)` / `--ease-emphasized` `cubic-bezier(.05,.7,.1,1)`
`--dur-fast`120ms / `--dur`200ms / `--dur-slow`320ms
**基準**: 色/背景=`--dur-fast`、移動/開閉=`--dur`、ビュー遷移=`--dur-slow`+emphasized。`prefers-reduced-motion` 対応を今後追加（§10）。

---

## 3. コンポーネント

### 3.1 レイアウト
- **`.wrap`**: `max-width:1320px; margin:auto; padding:0 --s-6`。全ビューの外枠。
- **`.context`**: ページ見出しブロック（`.title-h1` + `.title-sub`）。上下 `--s-8/--s-5`。
- **`.panel`**: `bg:--surface; 1px --line; radius:--radius; shadow-1`。パネル見出し `.panel-h`（font-display）。
  - `.panel-h .count`（右寄せ・mono）／`.panel-h .rt`（faint・"Realtime"等の副題）。

### 3.2 ナビゲーション
- **`.sidebar`**（`body.signed-in` で表示、幅248px固定、`padding-left:248px`）。折りたたみ=`.sb-collapsed`（66px）。≤1080px はオフキャンバス drawer。
  - 構成: ブランド → ワークスペースカード(`.sb-wscard`：切替＋残クレジット) → ナビ(`.sb-nav`) → 下部アカウント(`.sb-acct`)。
  - ナビ項目: **ホーム / メディア / コレクション** ｜（区切り）**プランと請求 / チーム・メンバー / クレジットを追加**（`data-owner-only`）｜ プロフィール・設定。
- **`#topbar`**: 工程中（`body.in-project`）のみ表示のスリムバー。モバイルではメニューボタン用に常時。

### 3.3 ボタン ⚠️（要整理・§10-C）
| クラス | 見た目 | 現状の使われ方 |
|---|---|---|
| `.btn`（基底） | min-h44, radius r-sm, weight700, **`flex:1`** | 既定で伸びる点に注意 |
| `.btn-primary` | **白（`bg:--ink`）** on dark | 請求「クレジットを追加」等 |
| `.btn-accent` | **青（`bg:--accent`）** | 一部CTA |
| `.hn-btn` | **青・大きめ** | サインイン/オンボーディング/空状態 |
| `.btn-ghost` | 枠線(`--line-strong`) | 副アクション |
| `.btn-tonal` | `--surface-2` | 中間アクション |
| `.btn.icon-only` / `.icon-btn` | 正方形アイコン | ツールバー |
| `.linkbtn` | テキストリンク | 弱いアクション |

> ⚠️ **「主役ボタン」が白(`.btn-primary`)・青(`.btn-accent`)・青大(`.hn-btn`)の3系統**あり基準が曖昧。§10-C で1系統に確定する。

### 3.4 バッジ・ピル・チップ ✅（P1-Bで正準化）
**正準コンポーネント**: `.badge` ＋ `.badge--accent / --neutral / --success / --warn / --danger`（面soft＋同系ink文字, `--r-full`, `--t-label-sm`）。**新規は必ずこれを使う。**
移行済み: `.member-row .badge`（枠線→variant）。
未移行（幾何は近いが独自クラスのまま・positioning都合）: `.badge-cur` / `.col-badge` / `.pk-tag` / `.sb-badge` / `.proj-status` / `.filter[aria-pressed]`。→ 見た目はaccent系で概ね揃っているが、順次 `.badge--*` へ寄せる。

### 3.5 メーター ✅（P1-Aで統合）
**単一コンポーネント** `.u-meter`（既定6px）＋ `.u-meter.sm`(5px) / `.u-meter.big`(10px)。塗り=`--accent`・形状=`--r-full`・地=`--surface-3` に統一。
残量で色を変える場合は塗り `<i>` の `background` を呼び出し側で `--good/--warn/--crit` に上書き（請求ヒーローが実施）。ダッシュボード/サイドバー/請求で共用。

### 3.6 カード
- **`.proj`**: 動画カード（サムネ＋名前＋メタ＋フッタ。hoverで浮上）。`.proj-grid` は `minmax(255px,1fr)`。
- **`.u-card`**: 使用状況の数値カード（大数字＋メーター＋補足）。
- **`.plan-card`**: プランカード（価格＋✓特徴リスト＋アクション。`.popular`でaccent枠＋人気バッジ、`.current`で淡色化）。`.plan-grid` は `minmax(210px,1fr)`。
- **`.pack-card`**: クレジットパック（数量・価格・目安。選択で`.sel`）。`.pack-grid` は `minmax(150px,1fr)`。
- **`.bill-hero`**: 請求の現在プラン（上部accentバー＋大見出し＋太メーター＋含有チップ）。

### 3.7 フォーム
- **`.fld`**: `label(--t-label,muted)` + `input`（`--control-h`40, `--r-sm`, `bg:--surface-2/線 line-strong`, focusで accent リング）。※ P0/P2で `--card`未定義・9px角丸・高さを是正済み。
- **`.sel`**: セレクト（`--control-h`40, `--r-sm`, `bg:--surface-2`）。
- **`.switch-row`**: チェックボックス＋ラベル（自動チャージ等）。`.inline-input`（数値＋単位）。
- **`.field`**: **末尾アクション付き入力**（送信ボタン・パスワードの目トグル等）。`.fld` とは別用途の意図的パターン。
> ✅ **入力の共有スタイルはトークン統一済み**（border=line-strong / radius=r-sm / bg=surface-2 / focus=accent-soft リング / 高さ=`--control-h`）。`.fld`=プレーン、`.field`=末尾アクション付き の2パターン。認証(`.auth-form .field`)のみ h48 の意図的な大サイズ（スコープ限定）。

### 3.8 フィードバック
- **`.toast`**（`#toasts`、下中央、成功/失敗/スピナー）。`window.toast(msg, ok, ms)`。
- **`.modal-scrim`/`.modal-card`**（コレクション作成/リネーム等）。
- **`.move-menu`**（ポップオーバー：コレクション移動）。

### 3.9 アイコン
SVGスプライト（`<symbol id="i-*">`）を `<svg class="ic"><use href="#i-..."/>` で参照。`.ic`（18px, currentColor, stroke2）、`.ic.sm`(14) `.ic.lg`(22)。
現有: `home menu panel back forward arrow-left arrow-right check alert plus edit download share send play eye eye-off camera film folder card user users settings logout chevron-down`。
> 追加時はこのスプライトに追記（外部アイコンフォントは使わない）。

---

## 4. 画面インベントリ（11ビュー）

| view | 画面 | 目的 | 主アクション | 主な構成 |
|---|---|---|---|---|
| `view-dash` | ホーム | 概況と入口 | 新規CM | 使用状況カード＋制作物グリッド |
| `view-wizard` | 新規CM | 選択で仕様化 | 次へ | 質問ステップ |
| `view-script` | 台本・絵コンテ | 素材確認 | 進む | ショットリスト |
| `view-workspace` | ワークスペース | 進捗と仕上がり | 書き出し | プレビュー＋制作パイプライン＋QC＋クレジット |
| `view-export` | 書き出し | 納品形式選択 | ZIP/共有 | 形式カード |
| `view-media` | メディア | 全動画一覧 | （絞り込み） | フィルタ＋グリッド |
| `view-collections` | コレクション | フォルダ整理 | 新規/移動 | 一覧＋詳細 |
| `view-team` | チーム・メンバー | 招待・席管理 | 招待リンク | 席数＋メンバー一覧 |
| `view-billing` | プランと請求 | プラン・支払い | プラン変更 | ヒーロー＋プラン比較＋履歴＋料金目安 |
| `view-credits` | クレジットを追加 | 購入・自動チャージ | 購入/保存 | 残高＋パック＋自動チャージ＋明細 |
| `view-settings` | プロフィール・設定 | 表示名・言語 | 保存 | プロフィール＋言語 |

**ビュー切替**: `hideAll()` → 対象を表示 → `focusView()`（AT用フォーカス移動）→ `setCrumb()`（パンくず）→ `_nav()`（topbar出し分け＋サイドバー現在地）。

---

## 5. ナビゲーション・IA・権限

- **ロール**: `viewer`（閲覧のみ・無料・席外）/ `member`（制作可）/ `owner`（招待・課金・全操作）。
- **権限ゲート**:
  - `body.readonly-role`（viewer）で制作/書き出し/課金系UIを非表示（制作パイプライン・QC・クレジット・生成 等）。
  - `data-owner-only`（請求/チーム/クレジット）＋ `window.__isOwner()` ガードで課金導線をオーナー限定。
  - `data-write-only` は member以上（コレクション作成/移動 等）。
- **クレジットは org プール**。共有アカウントでも支払い分を超えて生成できない設計（`memory: multi-seat-design`）。

---

## 6. 国際化（i18n）

- ソースは**日本語**。`var D = {...}`（JA→EN辞書）＋ MutationObserver でテキストノードを走査置換。
- 動的文字列は `window.L(en, ja)`（`LANG` グローバルが現在言語）。切替は `.lang [data-lang]`。
- **新しい静的JA文字列は必ず辞書 `D` にエントリ追加**（無いと英語時にJAのまま残る）。`data-t` 属性で明示も可。

---

## 7. アクセシビリティ（現状と指針）

- ✅ アイコンボタンに `aria-label`、パンくず `aria-current`、ビュー切替でフォーカス移動、`role=button/dialog/menu`。
- ✅ **フォーカスリング**: グローバル `:focus-visible { outline: 2px solid var(--accent-ink); outline-offset:2px }`（`:focus{outline:none}` でマウス時は抑制）。
- ✅ **`prefers-reduced-motion: reduce`**: 全 `animation/transition` を無効化。ただし**読み込みスピナー（`.spin`/`.toast .tsp`）は回転を維持**（必須フィードバック）。
- ✅ **コントラスト検証（2026-09-21）**: 暗い面（ground〜surface-3）上で `ink/muted/accent-ink/good/warn/crit` はすべて WCAG AA(4.5+)。**`--faint` のみ surface-2/3 で 4.2/3.8（本文AA未満）** → 三次・装飾テキスト専用とし、**本文には使わない**（本文は `--muted` 以上）。
- ✅ **アクセント塗りの上の文字は `--on-accent`（白, 4.8 AA）のみ**。`accent-ink`/`muted`/意味色を `--accent` 塗りに載せない（2.6以下で不合格）。バッジは `--accent-soft`(暗) 地なので `accent-ink` でAA。
- ⏳ 今後: 色だけに依存しない状態表現の最終点検（メーター等はテキスト併記済み）。

---

## 8. ライティング指針

- **成果物の言葉で。** クレジット（＝CM◯本）で統一。「スポット」は使わない。
- 主ボタンは動詞から（「クレジットを追加」「プランを変更」）。「OK/送信」ではなく何が起きるかを書く。
- エラーは「何が起きたか＋次にどうするか」。空状態は誘い（「まだ〜ありません」で終えない）。
- 数字には単位と補足（「残り 42 本」「＝CM◯本」）。

---

## 9. 現状の課題（Audit サマリ）

| ID | 状態 | 課題 | 対応 |
|---|---|---|---|
| A | ✅済 | メーター3実装 | 単一 `.u-meter`+`.sm/.big` に統合（P1） |
| B | ✅済 | バッジ6種以上 | 正準 `.badge`+variant 新設・member移行（P1）／残りは順次移行 |
| C | 📝文書化 | 主役ボタン3系統（白/青/青大） | 全体変更は回帰リスク大 → §11で使い分けを規約化。コード統合は保留 |
| D | ✅済 | コントロール高さ・角丸バラつき | `--control-h*` トークン化、非トークン角丸撤廃（P2） |
| E | ✅済 | `--card` 未定義 | 撤廃し `--surface`/`--surface-2` に（P0） |
| F | ✅済 | アクセント面の文字色規約 | 「面soft＋同系ink」を `.badge` で標準化・§11に明記（P1） |
| G | ✅済 | mono の 600/700 未読込 | 500 に統一（P0） |
| H | ✅済 | アプリ⇄サイトの brand blue 不一致 | サイトの青をアプリ `--accent #4A67E3` に統一（P3, `site/build.py`）。面/字の値は別のまま |
| I | ✅済 | `.panel-h .count` 常時 good色 | 中立(muted)化＋`.count.ok`で成功時のみgood（P0） |
| J | ✅済 | `.fld`/`.field` の実態整理 | 冗長ではなく別用途（プレーン／末尾アクション付き）。共有スタイルをトークン統一（高さ=`--control-h`）。認証のh48は意図的スコープ |

---

## 10. 改善提案ロードマップ（進捗）

### ✅ P0 — バグ・即時（完了）
E `--card`撤廃 ／ G mono 500統一 ／ I `.count`中立化＋`.ok`。

### ✅ P1 — 統合（完了：A・B。C は文書化）
- ✅ **A メーター統合**: `.u-meter`+`.sm/.big`、塗りaccent・残量色は上書き。
- ✅ **B バッジ統合**: `.badge`+`--accent/neutral/success/warn/danger`。member移行済み、他は順次。
- 📝 **C ボタン階層**: `.btn-primary`(白)=**アプリ内の主アクション**、`.hn-btn`/`.btn-accent`(青)=**ヒーロー/認証/オンボーディングの主アクション**、`.btn-ghost`=副、`.btn-tonal`=中間、と§11で規約化。`.btn{flex:1}` 既定は回帰リスクのため据え置き（`.cta-row`前提）。

### ✅ P2 — システム化（完了：D。F は規約化）
- ✅ **D コントロール規格**: `--control-h*` 導入、btn/input/sel/filter を統一、非トークン角丸撤廃。
- ✅ **F 文字色規約**: §11に明文化（面soft＋同系ink / 面solid＋on-色）。
- ⏳ **A11y**: `prefers-reduced-motion`・フォーカスリング共通化・コントラスト検証は未了（次段）。

### P3 — スケール（一部完了）
- ✅ **H ブランド統一**: サイトの brand blue をアプリ `--accent #4A67E3` に統一（`site/build.py` の `--blue/--blue-ink/--blue-soft` ＋ OG画像 ACCENT）。※ 面/文字/ground 等の値は依然別体系（完全統一は将来）。
- ✅ **A11y**: `:focus-visible`・`prefers-reduced-motion` は既実装を確認、スピナー維持を追加。コントラスト検証済み（faintは本文不可・on-accentは白のみ、を§7/§11に明記）。
- ✅ **J**: `.fld`(プレーン)/`.field`(末尾アクション付き)は別用途と確認、共有入力スタイルをトークン統一（高さ=`--control-h`）。
- ⏳ **ライブ・スタイルガイド**: 実スウォッチ/コンポーネントページ（別途ビルド）。
- ⏳ **面/字トークンの完全共通化**（アプリ⇄サイト）: brand blue 以外の値。
- ⏳ **C の物理統合**（白/青ボタンの実コード統一）: 現状は§11規約で運用。

> 残: ライブ・スタイルガイド ・ 面/字トークン完全共通化 ・（任意）Cの物理統合。コア（P0–P2＋H・A11y・J）は完了。

---

## 11. 実装・命名規約

- 色・寸法・角丸・余白・モーションは**必ずトークン参照**（ハードコード禁止）。新パターンはまずトークンを増やす。
- クラス命名はブロック接頭辞（`bh-*`=bill hero, `sb-*`=sidebar, `proj-*`=video card, `qc-*`=quality check…）。
- 追加コンポーネントは本ドキュメントの該当節に1行追記。
- i18n: 静的JAは辞書へ、動的は `window.L()`。
- アイコンはスプライトへ追加。外部アイコンフォント不使用。

### ボタンの使い分け（C）
| 種類 | クラス | 使う場面 |
|---|---|---|
| 主（アプリ内） | `.btn-primary`（白） | パネル/画面内の主アクション（例:「クレジットを追加」）。**1画面1つ** |
| 主（ヒーロー/導入） | `.hn-btn`・`.btn-accent`（青） | 認証・オンボーディング・空状態の主アクション |
| 副 | `.btn-ghost`（枠線） | キャンセル・戻る・第2アクション |
| 中間 | `.btn-tonal` | 弱い塗りが欲しい時 |
| アイコン | `.btn.icon-only`・`.icon-btn` | ツールバー |
| テキスト | `.linkbtn` | 最も弱い操作 |
> 白と青の主ボタンを**同一画面に併置しない**（主役は1つ）。

### 色の上の文字色規約（F）
- **面soft ＋ 同系ink 文字**（例: `--accent-soft` 地に `--accent-ink`）… バッジ・容器・淡い強調。
- **面solid ＋ on-色 文字**（例: `--accent` 地に `--on-accent`）… 塗りボタン等。
- 生の黒/グレーやコントラスト不足の同系色を面上に載せない。バッジは `.badge--*` に集約済み。

---

## 12. マーケサイトとの関係（別体系・注意）

`site/build.py` は**独立したトークン**を持つ（`--ground:#0E0F14`, surface 値もアプリと異なる）。
- ✅ **brand blue はアプリに統一済み**（`--blue:#4A67E3` = アプリ `--accent`）。
- ⚠️ ただし面/文字/ground など**その他の値は依然別体系**。ダーク一本化は両者済み。
- 「claude.ai ウィジェット用 CDS トークン（`--surface-1` 等）」とも**別物**。混同注意。
- 改善は §10-H（P3）。

---

### 付録: よく使うトークン早見
```
面   : --ground / --surface-low / --surface / --surface-2 / --surface-3
文字 : --ink / --muted / --faint / --outline
線   : --line / --line-strong
意味 : --accent(+hover/ink/soft) / --good(+soft) / --warn / --crit(+soft) / --cool
影   : --shadow-1 / --shadow / --shadow-lift
字   : --font-display / --font-jp / --font-mono ; --t-display..--t-label-sm(11)
角丸 : --r-xs6/--r-sm8/--r-md12/--r-lg16/--r-xl24/--r-full ; --radius(16)
余白 : --s-1..--s-10 (4/8/12/16/20/24/32/40)
動き : --ease-standard/--ease-emphasized ; --dur-fast120/--dur200/--dur-slow320
```
