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

### 2.4 角丸・影
`--r-xs`6 / `--r-sm`8 / `--r-md`12 / `--r-lg`16 / `--r-xl`24 / `--r-full`999。別名 `--radius`=r-lg(16), `--radius-sm`=r-sm(8)。
**基準**: ボタン/入力=`--r-sm`〜`--r-md`、カード=`--r-md`〜`--r-lg`、ピル=`--r-full`。
> ⚠️ 入力で `9px`/`10px` の非トークン値が混在（§10-D）。

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

### 3.4 バッジ・ピル・チップ ⚠️（乱立・§10-F）
現状は用途ごとに個別実装で**6種以上**が併存:
`.badge-cur`(accent-soft) / `.member-row .badge`(枠線muted, `.owner`でaccent) / `.col-badge`(accent-soft) / `.pk-tag`(accent-soft, `.pop`はaccent) / `.sb-badge`(surface-3) / `.proj-status`(暗ガラス) / `.filter[aria-pressed]`(ink反転) / `.chip`(選択チップ)。
→ **neutral / accent / success / warn / danger のバリアント制**に統合する（§10-F）。

### 3.5 メーター ⚠️（3種・§10-A）
| 実装 | 高さ | 色 | 使用 |
|---|---|---|---|
| `.u-meter` | 6px | `--accent-ink` | ダッシュボード使用状況 |
| `.sb-credits .u-meter` | 5px | `--accent` | サイドバー残クレジット |
| `.u-meter.big` | 10px | `--good`（残量で warn/crit に変化） | 請求ヒーロー |
→ **1つのメーターコンポーネント＋残量による色分けオプション**に統合する。

### 3.6 カード
- **`.proj`**: 動画カード（サムネ＋名前＋メタ＋フッタ。hoverで浮上）。`.proj-grid` は `minmax(255px,1fr)`。
- **`.u-card`**: 使用状況の数値カード（大数字＋メーター＋補足）。
- **`.plan-card`**: プランカード（価格＋✓特徴リスト＋アクション。`.popular`でaccent枠＋人気バッジ、`.current`で淡色化）。`.plan-grid` は `minmax(210px,1fr)`。
- **`.pack-card`**: クレジットパック（数量・価格・目安。選択で`.sel`）。`.pack-grid` は `minmax(150px,1fr)`。
- **`.bill-hero`**: 請求の現在プラン（上部accentバー＋大見出し＋太メーター＋含有チップ）。

### 3.7 フォーム ⚠️
- **`.fld`**: `label(--t-label,muted)` + `input`（h42, `radius:9px`, `bg:--surface-2`, focusで accent リング）。
- **`.sel`**: セレクト（h38, `radius:10px`, **`bg:var(--card)` 🐛未定義**）。
- **`.switch-row`**: チェックボックス＋ラベル（自動チャージ等）。
> 🐛 `--card` は `:root` に**未定義**。`.sel` と `.member-row` の背景が無効化される（§10-E）。
> ⚠️ コントロール高さが btn44 / input42 / sel38 / filter34 とバラバラ（§10-D）。

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

- ✅ アイコンボタンに `aria-label`、パンくず `aria-current`、ビュー切替でフォーカス移動、`role=button/dialog/menu` の付与。
- ⚠️ 追加すべき: `prefers-reduced-motion` 対応、フォーカスリングの一貫性、色だけに依存しない状態表現の徹底、コントラスト検証（muted/faint on surface）。

---

## 8. ライティング指針

- **成果物の言葉で。** クレジット（＝CM◯本）で統一。「スポット」は使わない。
- 主ボタンは動詞から（「クレジットを追加」「プランを変更」）。「OK/送信」ではなく何が起きるかを書く。
- エラーは「何が起きたか＋次にどうするか」。空状態は誘い（「まだ〜ありません」で終えない）。
- 数字には単位と補足（「残り 42 本」「＝CM◯本」）。

---

## 9. 現状の課題（Audit サマリ）

| ID | 種別 | 課題 | 影響 |
|---|---|---|---|
| A | ⚠️ | メーターが3実装（高さ5/6/10px・色バラバラ） | 一貫性・保守性 |
| B | ⚠️ | バッジ/ピルが6種以上の個別実装 | 一貫性・学習性 |
| C | ⚠️ | 主役ボタンが3系統（白/青/青大） | 主アクションが不明瞭 |
| D | ⚠️ | コントロール高さ(44/42/38/34)・角丸(8/9/10/12/16)がバラつき、非トークン値混在 | 精度・保守性 |
| E | 🐛 | `--card` 未定義トークンを `.sel`/`.member-row` が使用 | 背景が抜ける表示バグ |
| F | ⚠️ | アクセント面の文字色規約が未整備 | 可読性・アクセシビリティ |
| G | ⚠️ | mono に未読込の 600/700 weight | 合成ボールドの滲み |
| H | ⚠️ | アプリとサイトでトークン別体系（`--accent` vs `--blue` 等） | ブランド不一致 |
| I | ⚠️ | `.panel-h .count` が常に `--good` 色 | 成功以外の数値に不適切 |

---

## 10. 改善提案ロードマップ（優先度つき）

### P0 — バグ・即時（低コスト）
- **E**: `--card` を `:root` に定義（`--card: var(--surface)` 目安）か、使用箇所を `--surface`/`--surface-2` に置換。
- **G**: mono の 600/700 使用を 500 に寄せる、または Google Fonts の DM Mono に 500 上限で統一。
- **I**: `.panel-h .count` を中立色（`--muted`）に変更し、成功時のみ `--good` を明示クラスで付与。

### P1 — 統合（一貫性の核）
- **A メーター統合**: `.meter`（土台）＋ `.meter--sm/--md/--lg`（高さ）＋ 残量で `--good/--warn/--crit` を切替える単一実装に。ダッシュ/サイドバー/請求/クレジットで共用。
- **B バッジ統合**: `.badge` ＋ `--neutral/--accent/--success/--warn/--danger` バリアント（色＝面soft＋文字ink）。既存の badge-cur/col-badge/pk-tag/sb-badge/member badge を置換。
- **C ボタン階層の確定**: 「1画面1主アクション」に合わせ**主＝1系統に決定**（推奨: ダーク地で最も視認性の高い `--btn-primary`=白 を主、`--accent` は限定強調、`.hn-btn` は主へ吸収）。`.btn` 既定の `flex:1` を見直し（伸びるのは意図した所だけ）。

### P2 — システム化
- **D コントロール規格**: 高さトークン（例 `--control-h: 40px` / `-sm 34` / `-lg 44`）と角丸トークンを定義し、btn/input/sel/filter を統一。非トークン値（9/10px）を撤廃。
- **F 文字色規約**: 「面soft＋同系ink文字」「面solid＋on-色文字」の2パターンを明文化（バッジ・チップ・ボタン横断）。
- **A11y**: `prefers-reduced-motion`、フォーカスリング共通化、コントラスト検証。

### P3 — スケール
- **H ブランド統一**: アプリ⇄サイトのトークンを共通ソース化（少なくとも brand blue・surface 系の値を一致）。将来的に共有CSS or ビルド時生成。
- ドキュメントの**ライブ・スタイルガイド化**（実スウォッチ/実コンポーネントを並べたページ）。

---

## 11. 実装・命名規約

- 色・寸法・角丸・余白・モーションは**必ずトークン参照**（ハードコード禁止）。新パターンはまずトークンを増やす。
- クラス命名はブロック接頭辞（`bh-*`=bill hero, `sb-*`=sidebar, `proj-*`=video card, `qc-*`=quality check…）。
- 追加コンポーネントは本ドキュメントの該当節に1行追記。
- i18n: 静的JAは辞書へ、動的は `window.L()`。
- アイコンはスプライトへ追加。外部アイコンフォント不使用。

---

## 12. マーケサイトとの関係（別体系・注意）

`site/build.py` は**独立したトークン**を持つ（例: `--blue:#6180F5`, `--ground:#0E0F14`, surface 値もアプリと異なる）。アプリ `--accent:#4A67E3` とはブランド青がずれている。
- ダーク一本化は両者済みだが、**トークン体系は共有していない**。
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
