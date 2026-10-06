# LINE Design System → Spot 反映プラン

LINE Design System（公式ガイドライン, 98 PDF / 663ページ, 画像スペック）を通読し、Spot（ダークテーマの日本語 Web SPA・ブランドアクセント indigo `#4A67E3`・低ITリテラシー層向け）へ**原則・アナトミー・数値**を移植するためのアクションプラン。
LINE のブランドグリーンは Spot のブランドではない ── 抽出するのは **システム/原則/アナトミー**であり、緑そのものは移植しない。数値は Spot の indigo トークンにマップする。

- 元データ: `/Users/yosh/work/SPOT/LINE Design System/`（98 PDF）
- 対象: Spot `spot-app/index.html`（`styles/tokens.css`）／参照: `docs/design-system.md`
- 作成: 2026-09-22 / READ-ONLY（アプリコードは変更しない。本ファイルのみ WRITE）

---

## 目次
1. [Foundations（基盤の実数値）](#1-foundations)
2. [Components（コンポーネント別アナトミー）](#2-components)
3. [Reflection Plan（Spot への優先度付き反映）](#3-reflection-plan)
4. [Not applicable to Spot（記録のみ）](#4-not-applicable)
5. [98 PDF カバレッジ一覧](#5-coverage)

---
<a id="1-foundations"></a>
## 1. Foundations（基盤の実数値）

LINE Design System は 2 系統ある: **LDSG（LINE Design System for Global Family Service）** = トークン駆動・多言語（読み込んだ Foundation の多くはこちら）、**Messenger（LDS）** = OS システムフォント前提。両方を統合して記載する。LINE 本体はライト主体＋緑ブランドだが、Spot に効くのは**役割設計・スケール・アナトミー・数値**。

### 1.1 デザイントークンの命名思想（Overview）
`[Prefix "LDSG"] + [Visual Element] + [Category] + [Value]`。例 `ldsg-color-green-100`, `ldsg-typography-title-200`, `ldsg-radius-...`。
- **Value は 100 刻み**（100 が最小単位、必要時のみ 50 を追加。大きい数字ほど「強い/大きい」）。
- 8 つの Visual Element と接頭辞: `ldsg-color`(色) / `ldsg-font`(書体) / `ldsg-lineheight`(行高) / `ldsg-breakpoint` / `ldsg-spacing`(余白) / `ldsg-radius`(角丸) / `ldsg-border`(線幅) / `ldsg-shadow`(影)。
- LINE ブランド緑 = **#06C755** = `ldsg-color-primary-green`（＝Spot では `--accent #4A67E3` に相当）。
- **Spot への含意**: Spot の「意味→トークン→数値」の考え方は既に一致。LINE 流の **100 刻みの value スケール**は Spot の `--t-*`/`--s-*` にも部分適用できるが、Spot は px 直値で運用中なので採用は任意。

### 1.2 カラー — 役割・パレット構造（LINE Color Guide / Color Usage / Semantic / Contrast）

**Primary Palette（数値スケール, 明→暗）**: LINE は各色を **番号スケール**で持つ。
- **Gray**: White / Gray100・150・200・250・300・350・400・500・600・650・700・750・770・800・850・870・900 / Black。実数アンカー: **Gray900 = #111111**, **Gray800 = #2A2A2A**, **Gray650 = #616161**, **Gray400 = #878787**, White = #FFFFFF。
- **Blue**: 400/500/600/700。**Blue500 = ボタン背景・Tooltip 背景**の役割。**Blue700 = #2C53DE**（対白 6.31:1 / 対 Gray900 3.06:1）。リンク/ハッシュタグ = **Blue600**。プレースホルダのカーソル = Blue600。
- **Navy**: 400〜900。**Navy800 = 検索バー**, Navy850 = Android ヘッダ, Navy900 = iOS ナビバー。
- **Red**: Red400（iOS。通知バッジ = Red400）。
- **重要ルール**: パレット色は**透明度調整禁止**（例外は White / Black のみ、5% 刻みで可）。

**アクセシビリティ運用（パレット）**: 「**番号 500 以上**を文字に使う（対背景 3.0:1 以上）」。400 は重要度の低いテキストに限定。

**White / Black の不透明度運用**:
- **LINE White**: 文字・主要アイコンは **70%以上**、プレースホルダは **40%以上**、副次 UI（ボタン背景等）は **15%以上**。
- **LINE Black**: **10%以上**を dimmed(覆い)に。文字には使わない（disabled/placeholder を除く）。
- **Dimmed Effect** 3 段: 85% / 70% / 30%（背景画像の上に敷く覆い）。

**色による情報階層（Color Usage）** — Spot にそのまま効く:
| 役割 | LINE 割当 | Spot 対応トークン |
|---|---|---|
| Title / Primary text | Gray900(#111111) | `--ink` |
| Body / Secondary text | Gray600 | `--muted` |
| Caption / 三次 | Gray500 | `--faint`（装飾専用） |
| Divider | Gray150 | `--line` |
| Link / Hashtag | Blue600 | `--accent-ink`（darkでのリンク色） |
| 通知バッジ | Red400 | `--crit` |

**状態レイヤーの自動生成（Auto Code for Highlighted/Pressed）** — HSV の V を変換:
- V ≤ 32% → **元の V +45%**（暗い色は押下で明るく）
- V 33〜86% → **元の V −20%**
- V ≥ 87% → **元の V −35%**（明るい色は押下で暗く）
→ Spot 含意: `--accent-hover #5A76EC` は「明るくする」方向で LINE の暗色ルール（+45%相当）と整合。**ダーク面では pressed = 明るく**（LINE の V≤32% ルール）が正しい。Spot の `--pressed`（ink 10% 白オーバーレイ）はこの思想と一致。

**Disabled（Disabled Code）**: 「LINE White に **40% 透過**」／White 以外の色は「**Gray900 の 40%**」。disabled はまずボタンの**ラベル（文字）だけ**に効かせ、背景色まで変えるのは強調したい時のみ。LDSG の disabled グレー実数 = **#E4E4E4**（＝ライト用。Spot はダークなので `--surface-2/--faint` で代替）。

**Semantic Colors（Light/Dark 両対応の意味色システム）** — Spot はダーク一本だが**命名体系が有用**:
- 構造: `[Numeral(任意) + Assistive(任意) + Characteristic(任意) + Category(必須)]`。例 `primaryText`, `secondaryAccentText`, `tertiaryNeutralFill`, `quaternarySeparator`。
- **Numeral**（使用頻度順）: Primary → Secondary → Tertiary → Quaternary → **Quinary（第5＝上限推奨）** → Senary…。
- **Characteristic**: Accent(強調) / Placeholder(ヒント) / Additional / Prominent(目立つ) / Neutral(中立) / Inverse(反転)。
- **Category（必須）**: **Text / Link / Fill / Surface / Background / Separator / Disabled / Nonadaptable(light-dark固定) / Unique / Legacy**。
- 値の例: `primaryText` = Light #000000 / Dark #FFFFFF。`secondaryDisabled(40%)`。
- **Spot 含意**: Spot の面/字/線トークンは既にこの発想。**未整備の「アクセント面の上の文字色」規約**（design-system.md §10-F）は LINE 流に `on-` prefix（Category=Nonadaptable）で正準化できる。

**コントラスト基準（Color Contrast, WCAG マップ）**:
| | Must (WCAG A) | Should (WCAG AA) | Consider (WCAG AAA) |
|---|---|---|---|
| Small text | 3.0:1 | **4.5:1** | 7:1 |
| Large text | 3.0:1 | 3.0:1 | 4.5:1 |
- **Small text = 18.5px 未満のレギュラー**。**Large text = 18.5〜24px の bold、または 24px 超**。
- UI 要素と背景の比も **3.0:1 以上**必須。
- **Spot 含意**: Spot は既に本文 AA(4.5) 検証済み（design-system.md §7）。LINE の「18.5px 境界」を Spot の本文 14px（=small扱い→4.5必須）判定に採用でき、`--faint` を本文に使わない現行方針と完全一致。

### 1.3 タイポグラフィ（Typography / Typography２）

**LDSG トークン体系**: `[Lang]/[Type]/[Size]/[FontSize]/[Weight]`。例 `ldsg-en-title-xxl-200` = EN・Title・XXL・38px・Bold。
- **Type は 2 つ**: **Title**（見出し H1–H6・リスト見出し・サブ見出し。**行高小さめ**）／**Text**（本文・**ボタンラベル**・キャプション・オーバーレイ・バッジ。**行高＝高く可読性優先**）。
- **Size 記号**: XS / S / M / L / XL / XXL。
- **Weight は言語横断で 100/200/300 に正規化**（言語ごとにフォントの太さ表記が違うため）。
- **下限 12px（12pt 未満は非推奨）**。

**推奨スケール（Messenger, iOS 実数）** — Spot のスケール検証に有用:
| Style | Weight | Size(px) |
|---|---|---|
| Heading 1 | Heavy | 24 |
| Heading 2 | Bold | 17 |
| Heading 3 | Bold | 14 |
| Heading 4 | Regular | 13 |
| Title 1 | Bold | 23 |
| Title 2 | SemiBold/Bold | 19 |
| Title 3 | Medium/SemiBold | 16 |
| Title 4 | Medium/SemiBold | 15 |
| Title 5 | Medium/SemiBold | 14 |
| Body 1 | Regular | 16 |
| Body 2 | Regular | 14 |
| Body 3 | Regular | 13 |
| Body 4 | Regular | 12 |
- **書体**: iOS = SF Pro Text/Display（Light〜Heavy）／JP = Hiragino Sans（W3/W6/W7）／TC = PingFang／TH = Thonburi／KR = Apple SD Gothic Neo。OS システムフォント採用が原則。
- **多言語配慮**: JP・タイ語は EN より**行が長くなる**→折返し・省略に注意。
- **Spot 含意**: Spot の `--t-*`（32/26/20/16/15/14/13/12/11）は LINE の推奨レンジ内で健全。LINE は **12px を明確な下限**とする→Spot の `--t-label-sm 11px` は「最小・装飾のみ」を厳守（本文は 12px 以上）。「見出し=行高小さめ / 本文=行高大きめ」は Spot の行高設計指針として明文化価値あり。

### 1.4 アイコン（Iconography / Icon Guideline）

- **グリッド 24×24px**（既定、調整可）。
- **パディング 全辺 2px** → 実描画エリア **20×20px**。
- **Key Shape**（比率テンプレ）: Square / Circle / Vertical rectangle / Horizontal rectangle。
- **ストローク 既定 1.3pt**（推奨 **1.3 / 1.5 / 1.8pt**）。アウトラインをピクセルに合わせる。拡大時はストロークも比例拡大。
- **角丸 0〜2px**（コーナー個別可）。
- **角度 45°基準**（必要時 15°刻み）。
- **命名**: `[Category]-[Shape] / [name]` 例 `pictogram-regular/chat`。Category = Pictogram(UI) / Brand / ETC。Shape = **Regular(アウトライン)** / **Solid(塗り)**。名前は**名詞**（Close→Times）、同図の別型は `-alt`。
- **スタイル**: 簡潔・一貫・中立、**太めのストローク＋丸いコーナー**。
- **運用**: カスタムはサイズ変更のみ、メタファ/スタイル変更禁止。コンポーネント内のアイコンサイズ・ストロークは固定。
- **Spot 含意**: Spot のスプライト `.ic`（18px, currentColor, **stroke2**）は LINE の 24px グリッド/1.3–1.8pt ストロークと**思想一致**（線アイコン・currentColor）。Spot の stroke2 は 24px 換算で LINE 1.3–1.5pt 帯に近い。**追加時は「24グリッド・2px余白・名詞命名・Regular/Solid の2形」を明文ルール化**すると LINE 品質に寄る。`.ic.sm 14 / .ic 18 / .ic.lg 22` のサイズ規格も踏襲でよい。

### 1.5 レイアウト・グリッド（Layout / Layout２）

- **画面共通マージン 左右 16px**（デバイス幅 375 → コンテンツ幅 **343**）。カード内も**左右 16px**（カード幅 355 → 内容幅 323）。
- **カラムグリッド（375 基準）**:
| 列数 | カラム幅 | ガター | マージン |
|---|---|---|---|
| 2 col | 167 | **9** | 16 |
| 3 col | 109 | **8** | 16 |
| 4 col | 82 | **5** | 16 |
- **解像度変化**: ガターは維持、列数を増やし、カラム幅は同比率で拡大。
- **画像グリッド（モバイル, 参考）**: 全幅 375 / 16px マージン時 343。アスペクト比 **4:3・3:4・1:1**。
- **Spot 含意**: Spot は `.wrap max-width:1320px + padding 0 var(--s-6)(24px)` の Web 広幅。モバイル（≤1080px オフキャンバス）では **左右ガター 16px** を最低線として確認するとよい（LINE の 16px 規範）。Spot のグリッドは `.proj-grid minmax(255px,1fr)` 等の auto-fit で、LINE の固定カラムより Web 的に妥当。ガター（列間）は Spot 現行 `--s-*` で LINE の 8–9px より広めだが、密度重視の一覧では **8px ガター**を選択肢に。

### 1.6 デザイン原則（Design Principle / LINE Voice）

**6 原則**（LINE）:
1. **WE ≠ USERS** — 作り手＝ターゲットではない。実ユーザーの必要を調べる。
2. **Clear primary tasks** — 主タスクを直感的に。考え込まず使える設計。
3. Chat comes first —（LINE 固有）。
4. **Reliable design** — 信頼できる・全年齢に直感的なデザイン。
5. **A cohesive experience** — 画面をまたぐ**一貫した単一体験**。画面間の文脈と関係を考慮しシームレスに。
6. **Respect for legacy** — 既存を尊重、変更は段階導入。

**LINE Voice（UX ライティング）**:
- **CLEAR**: 一貫性より明快さ、専門語回避、短く。
- **CONVERSATIONAL**: 自然な言葉、「ユーザー」と呼ばない、能動態。
- **ボタンはユーザーの意図を述べる**（「OK」ではなく動作を書く）。
- **Spot 含意**: Spot の原則（1画面1主アクション・平易語・補足常設・成果物の言葉）は LINE 1/2/4/6 と**ほぼ同一思想**。特に「**主タスクを直感的に**」「**ボタンは意図を書く**」は Spot のトーン（design-system.md §8）と完全一致。LINE の「**画面間の cohesive 体験**」は Spot のビュー遷移（`focusView/setCrumb/_nav`）強化の裏付けになる。

---
<a id="2-components"></a>
## 2. Components（コンポーネント別アナトミー）

数値は LINE の redline 実測。**緑塗り（`ldsg-color-brand-primary` / #06C755）は全て Spot の `--accent #4A67E3` に読み替え**、破壊的赤・GNBバッジ赤は Spot の `--crit` に対応。px と pt はモバイルで 1:1 とみなす。共通: **Hover=不透明度70% / Pressed=不透明度50%**（LINE 全体の状態レイヤー規約）。disabled グレー実数 #E4E4E4（ライト用、Spot は `--surface-2`/`--faint` で代替）。

### 2.1 ボタン（Action / Box / Text / Icon / FAB / Segmented / Stepper）

**Action / Box Button（塗りボタン）**
- アナトミー: コンテナ + ラベル + アイコン(任意、ラベル先頭)。中央揃え。
- タイプ: **Contained**(塗り=primary, on-primary文字) / **Outlined**(枠+primary文字) / **Ghost/Text**(文字のみ)。破壊は赤 Solid。
- サイズ: XS/S/M/L/XL（px 注記なし）。**Full-Bleed** = 画面幅100%・**角丸なし**・最下部固定（ホームインジケータ端末用）。
- 状態: Enabled / Disabled(#E4E4E4, ラベルのみ) / Hover(明) / Pressed(明tint) / **Loading**(内部スピナー)。
- 角丸カスタム: **3 / 5 / 7 px から選択**。
- 配置規約: **横並びは主ボタンを右**、縦並びは**主を上**。1画面に primary は1つ（緑 or 赤）。必須入力が済むまで **disabled 維持**。購入済/DL済は disabled でも文字・アイコンで状態を示す。短いラベル(OK/Cancel)=横、長い/翻訳ラベル=縦。sticky ボタンは最下部固定（ダイアログ/シート以外で最前面）。
- → Spot: `.btn`/`.btn-primary`(白)/`.hn-btn`(青)/`.btn-ghost`/`.btn-tonal` の階層は LINE の Contained/Outlined/Ghost に対応済み。**Loading 状態**と**「主は右／縦なら上」規約**、**disabled はラベルのみ**が補える。角丸は Spot `--r-sm 10px`（LINE の 7px より丸め、Canva風で意図的）。

**Text Button**: 4タイプ = Primary / Destructive(赤) / Secondary Mono(**ダークでは白**) / Retreative Light(Cancel/Close)。ラベル↔アイコン gap **18pt**。1行1テキストボタン。Box+Text は**横に併置しない**（Text は下）。→ Spot `.linkbtn`。

**Icon Button**: サイズ **S=32 / L=52px**(コンテナ)。Contained/Outlined/Slot。**Hover 70% / Pressed 50%**。バッジ: Dot / Number(1–999、超過**999+**)。**Icon Button Group = 3〜5個**（6+ は Expanded）。等間隔・単色推奨。Messenger 版のアイコンコンテナ = **38pt**。→ Spot `.icon-btn`/`.btn.icon-only`。Spot はデスクトップ `--target 40px`。LINE の S32/L52 と近い。

**Floating Action Button（FAB）**: 直径 **54pt / アイコンエリア 38pt**（1サイズ）。緑(1階層) / 白(2階層の子)。**右下 16pt マージン**、常時最前面、ボトムナビの上。Expandable = 子 **3〜6個**（"+"→"×"、dimmer 表示）。Pill FAB = 完全角丸・自動幅固定高・"New Post" 等。→ **Spot に FAB は現状なし**。モバイルの「新規CM」主導線として検討価値（§3 参照）。

**Segmented Control**: サイズ **S=32 / M=36 / L=44px**。項目 **2〜4個**。Contained(選択=黒塗り白文字) / Padded(選択=白pill on グレー track)。**タブの"下"に置く**（上не可）、2つ併用不可、単独ならタブを使う。→ Spot: フィルタ切替 UI に相当（`.filter` 群）。

**Stepper**: サイズ **S=32 / M=46px**。minus/値/plus。最小値で minus disabled。**小数不可**（整数のみ）、広レンジはスライダー、小刻みは stepper。→ Spot: 数量入力（クレジットパック等 `.inline-input`）に適用可。

### 2.2 カード（Card）
- アナトミー: 画像エリア / テキスト(タイトル+本文) / インジケータ(任意、非タップ) / アクション(任意、右or下)。
- タイプ: Surface(画像+テキスト分離) / Full image(内側テキストはグラデ dim scrim で可読性確保)。
- アクション: **カード全体がタップ=詳細へ**。補助アクションはアイコン/トグル(ハート等、上固定)/テキスト(Share)。インジケータ(バッジN/価格/時間00:46/メディア種別)は四隅可、**タップ対象にしない**。
- 配置: 単体 / 縦コレクション(スクロール) / 横コレクション(スワイプ)。
- → Spot: `.proj`(動画カード)/`.plan-card`/`.pack-card`/`.u-card`。**「カード全体をタップ=詳細、補助アクションは分離」**が明確な指針。Full-image の**グラデ dim**はサムネ上テキストの可読性策として `.proj` に有効。

### 2.3 入力（Inputs / Text Input / Text Area / Search / Select / Pulldown）
共通 LDSG トークン:
- 値テキスト: **16px / 行高1.4**（システムフォント、変更不可）。
- ラベル: `text-m-200`(≈14–17px)/黒。ヘルプ/エラー: `text-s-100`/gray-500。カウンタ: gray-400。プレースホルダ: **gray-350**。必須 `*` = 赤、タイトル右。
- コンテナ3型: **Contained**(bg gray-150・枠なし) / **Outlined**(枠 border-100 + gray-300・bg なし) / **Underlined**(下線のみ)。**1画面1型**。
- 2入力横並び: **gap 12px**。単一入力の既定幅 = 画面幅 − 左右マージン。
- 状態: Enabled → **Focus=青枠/青カーソル** → Typing(値=黒 + 末尾×消去) → **Error=赤枠+赤ヘルプ** → Disabled(淡・不可)。**エラーはライブ表示**（送信後でなく）。入力に応じたキーボード（数値→テンキー）。パスワードは末尾に目トグル、既定 hide。
- **Text Area**: ヘルプ領域 **Min 62 / Max 207px**、本文は自動増→超過でスクロール。2行以上想定時に使用。
- **Search Bar**: アイコン/テキスト/リセット(×丸、入力時)/Cancel(フォーカス時)/音声・QR(任意)。フォーカスで下に候補リスト、履歴("Clear all")、オートコンプリート(一致文字ハイライト)、インスタント結果(タブ)。
- **Pulldown**: Text Input と同一 + chevron-down(黒)。
- **Pulldown Menu**: コンテナ **min-width 112px**、**画面端から≥8px / アンカーから2〜8px**。**≤6項目**（超過はボトムシート）。bg 白・枠 gray-150・divider は控えめ（毎項目/最終項目には引かない）。
- → Spot: `.fld`(プレーン) / `.field`(末尾アクション付き) / `.sel`。**Spot の focus=accent リング**は LINE の青枠と同思想。補える点: **必須`*`=赤右**、**ライブエラー(赤枠+赤ヘルプ+カウンタ色分け gray-400)**、**プレースホルダ専用色**（Spot は `--faint` 相当）、**コンテナ型を1画面1種に統一**、**文字カウンタ**（`0/500`）。値 16px は Spot `--t-title 16px`＝入力ズーム回避にも good（iOS で16px未満はズーム）。

### 2.4 選択コントロール（Checkbox / Checkmark / Radio / Switch）
- **Checkbox**: コントロール box **26pt** 角。状態 = Selected / Unselected / **Indeterminate(横棒、親子伝播)** × Enabled/Disabled/Hover/Pressed/**Error(赤)**。多選択に使用。既定は右側・リスト右端から **16pt**（画像上は上右 **8pt/8pt**）。Number 型(選択順を数字、最大3桁)。
- **Checkmark**: 単一選択の緑チェックのみ（確認ボタン不要、即時）。リスト右。確認フローには radio を使う。
- **Radio**: box **26pt** / 内側選択円 **12pt**。1グループ1選択、**常に既定選択あり**、無選択に戻れない。Error=赤リング。
- **Switch**: ラベル+説明+track+thumb。On=accent 塗り+thumb 右 / Off=グレー+左。即時反映。**リスト右端 16pt**、左置き不可。（track/thumb の px は未記載。）
- → Spot: `.switch-row`（チェックボックス+ラベル）。補える点: **Indeterminate 状態**、**Error 状態**、**「多選択=checkbox / 単一=checkmark / 確認=radio」の使い分け**、**右端16pt 配置規約**。Switch の「On=accent, 即時反映, 左置き禁止」も明文化価値。

### 2.5 チップ・タグ・バッジ（Chip / Chips / Tag / Badge）
- **Chip（LDSG）**: 左アイコン/ラベル/右アイコン/コンテナ。Contained/Outlined。状態 Selected/Unselected/Disabled/Hover/Pressed。**既定 border-radius = Pill**、**padding 固定**、幅=内容に自動。2個以上の選択肢がある時のみ使用。
- **Chips（Messenger）**: 用途 3種 = **Action**(実行) / **Filter**(多選択・再タップで解除) / **Choice**(単一選択・前を自動解除)。選択は "✓"、未選択 "+"。ラベルは**省略なし・改行なし**、左→右、収まらなければ次行（チップは分割しない）。
- **Tag（LDSG）**: アイコン/コンテナ/テキスト。Contained/Outlined/Ghost。**Pill=50%固定** or **Rectangle=角丸 0/3/5/7px**。1文字タグは Square(1:1)。padding 固定・幅可変・高さ固定。
- **Badge**: 3型 = Dot / Number / Icon。5サイズ。
  - **Dot 径**: S**5** / M**8** / L**10** / XL**14** / XXL**20** px。
  - **Number 高**: S**16** / M**18** / L**20** / XL**24** / XXL**36** px。
  - **Icon**: M18 / L20 / XL24 / XXL36。
  - 溢れ: **99+**（LDSG）/ **999+**（Messenger）。**色ルール: GNB/ボトムナビ=赤、その他=緑（=Spotではaccent）**。色は service primary か赤の濃淡推奨。
- → Spot: **`.badge` + variant** に正準化済み（design-system.md §3.4）。補える点: **Chip の Action/Filter/Choice の用途3分類**（Spot の `.filter[aria-pressed]` は Filter 型に相当）、**選択マーク ✓/+**、**Number バッジの 99+/999+ 溢れ表記**、**バッジ数値サイズの実数スケール**(16/18/20/24)。Spot の `.badge--danger` は「GNB=赤」の LINE 慣習と一致。

### 2.6 リスト・リストヘッダ（List / List Header）
- **List**: Row = 左エリア(Profile/Service/Image 1:1・4:3・16:9/Icon) + テキスト(タイトル+説明) + 右エリア(Switch/Checkbox/Radio/Icon/Text/Badge/Image)。状態 Normal/**Highlighted(New/追加)**/Pressed。**右側ボタンは≤2**（3+ は overflow か below-list）。アクション: 展開/選択(単=checkmark, 複=塗り丸)/並替(ドラッグ)/削除(スワイプ or 編集モード赤)/DL/追加/See more/**ロード時 Skeleton**。
- **List Header**: タイトル + 右ボタン(なし/Text/Icon/Dropdown)。ソート/フィルタは**タイトルに "▾"**、右に展開 chevron。"See more" は text か icon の一方に統一。
- → Spot: メンバー一覧・履歴・メディア一覧。補える点: **左エリアの画像アスペクト規格**、**右側≤2アクション**、**Highlighted(新規)行**、**ロード時 Skeleton**（Spot は `.skel` 実装済 ✓ ＝ LINE の shimmer と一致）。

### 2.7 ボトムシート（Bottom Sheet）
- 角丸 上 **14px 固定**、幅 **100%・左右マージンなし**、高さ Auto(0〜100%、status bar 除く)、超過でスクロール。
- ハンドルバー(任意) = Grab/Steer/Release の3段、離すと最寄りプリセット高にスナップ、ドラッグで全高へ。
- タイプ: **Modal(dimmer あり・操作をブロック)** / **Interactive(dimmer なし・背面操作可)**。
- ヘッダ: Normal/Close-Only(既定)/Tab-Only/Search-Only/None。ボタンエリア: 縦(既定)/横/Full-Bleed。**3ボタンは非推奨**。
- 画像サイズ: 16:9=375×210 / 4:3=375×281 / 1:1=375×375 / 3:4=375×500。
- キーボードでシートがせり上がる。**タブレット/PC では使わない**（drawer/pulldown を使う）。dim scrim = `opacity-black`。
- → **Spot に Bottom Sheet は現状なし**（モバイルは drawer とモーダル）。低ITリテラシー層のモバイルで「選択肢シート」は有効。§3 で P2 提案。

### 2.8 ナビゲーション（Bottom Nav / Top Nav / Side Drawer）
- **Bottom Navigation**: 幅100%・高さ Auto。項目 **3〜5個（最大5、超過はタブへ）**。選択=solid アイコン+黒(→accent)、非選択=gray-600、disabled=#E4E4E4。バッジ Dot/Number(999+)。**スクロールで消えない**、横スクロール不可、ラベルは短く(省略/2行禁止)。
- **Top Navigation**: 高さ **iOS 44 / Android 56 / Sub Window 50px**。左(戻る)/タイトル/右アイコン。タイトル `title-m-200`(EN/TH 17・JP/TC 16px)、幅 **max 136px**・高さ24、超過で省略。アイコン **24×24・stroke 1.5**。テキストボタン min40/max75px。端マージン **12px**・アイコン間 **16px**。スクロールで縮む flexible header 可。背景: ライト白 / **ダーク #111111**。
- **Side Drawer**: 幅 **既定280px(最大300 / 画面80%上限)**。dimmer `opacity-black-40`。divider gray-150。ヘッダ(Avatar+名前)/アクティブ域(icon solid + gray-150 コンテナ)/フッタ(social ghost icon)。バーガーで開、dimmer タップ/スワイプで閉。**3階層以上のネスト禁止**。Icon+Text と Text-only を同レベルで混在させない。
- **Navigation（意思決定表）**: Drawer=トップレベル・**4超は非推奨**。Bottom nav=**3〜5**・全画面一貫。Tab=任意階層・**2超**・タップ+スワイプ。
- → Spot: `.sidebar`(幅**248px**固定、≤1080でオフキャンバス drawer)/`#topbar`。**Spot の 248px は LINE drawer 既定 280px より狭いが妥当**。補える点: **topbar 高さの端末別規範(44/56)**（Spot `--topbar-h 60px` は妥当）、**drawer の dimmer 40%**、**3階層ネスト禁止**、**ナビ項目数 3〜5 / 4超はタブ移行**の意思決定表（Spot のサイドナビ項目数チェックに使える）。Spot の**ダークな topbar 背景**は LINE ダーク #111111 と同系。

### 2.9 タブ（Tab / Tabs / Expanded Tab List）
- **Tab**: Flexible(スクロール・項目無制限・下線=ラベル幅) / **Fixed(2〜4個・画面幅÷個数)**。項目間マージン M=24/S=12px。**下線太さ M=2 / S=1px**。padding S=8/M=12px。Fixed 側マージン 16 or 0px。状態: Normal 100%/Hover 70%/Pressed 50%、選択=太字+下線、**同時1つ**。バッジ(緑ドット)。**≥4項目 or 不均等長は Flexible**。テキスト折返し禁止（横スクロール）。**ボトムナビにタブを付けない**。
- **Tabs(別型)**: Text / Box(選択=黒塗り白文字, フィルタ用pill) / Icon。Fixed 2〜4列。List とタブの両方がスワイプ可なら List のスワイプ優先。
- **Expanded Tab List**: flexible tab 専用の展開一覧。ピル項目、左右 padding **20px**、項目間 gap **8px**、行間 **12px**、コンテナ左右マージン 16px、dim 域 min-height 78px。
- → Spot: メディア/コレクションのフィルタタブ。補える点: **下線 2px・状態不透明度(100/70/50)**、**Fixed 2〜4 / それ超は Flexible スクロール**、**Box タブ=フィルタ pill**(Spot の `.filter` と一致)。

### 2.10 オーバーレイ（Snackbar / Toast / Tooltip）
- **Snackbar**: 幅100%、左Item(任意)/タイトル(1行)/説明(2行)/右Item(Action Button 既定)。**下マージン既定16px**。**自動消滅 ~3秒（4〜10秒選択可）**。bg **`opacity-black-85`**、タイトル白、説明 white-40%、Action=accent。Top/Bottom 2位置。**snackbar=全域リンク+アクション可**。
- **Toast Overlay**: コンテナ/テキスト/アイコン。Icon Toast(check/loading/exclamation、正方形固定) / Text Toast(Center or Bottom、**Bottom 幅=画面−32**)。**自動消滅 ~4秒・ユーザーは消せない**。bg **`opacity-black-80`**、テキスト gray-100/`text-m-100`。Messenger 版: icon toast **123×46pt**、text max **305pt**、**フェード0.5秒**。**常に1つ**。**toast=アクションなし**、center or bottom。
- **Tooltip**: コンテナ/テキスト/矢印(任意)/×(任意)/ボタン(任意)。Large(幅可変・ボタン可) / Small(自動幅・固定高・1行・ボタン不可)。**テキスト最大3行**。**画面端≥8px / 対象要素から2〜8px**。padding 12/11pt、close 右14/上13pt。**1ページ1つ**、dim 画面上では避ける。状態 Default/Hover/Pressed。
- → Spot: `.toast`(下中央) / `window.toast(msg, ok, ms)`。**Spot の toast は LINE の Toast Overlay に相当**。補える点: **既定 ~3〜4秒・下16px マージン・bg 黒80〜85%**（Spot の toast タイミング/背景の基準に）、**「toast=アクションなし / snackbar=アクション可」の区別**、**常に1つ**。Tooltip は Spot 未実装 → 初回チュートリアル(memory: first-run tutorial)に有効。

### 2.11 確認・ポップアップ（Modal / Popup / Confirmation / Delete）
- **Popup(ダイアログ)**: **幅 288px 固定**、高さ Auto、**最大高 504px**、画面中央、左右マージン固定。4型(Text/Avatar/Image/Promotion)。画像 16:9=288×162 等。ボタン: 縦(Primary / Primary+Outlined / Primary+Ghost / 3ボタン) / 横(Primary / Ghost×2 / Contained×2)。タイトル `title-m/l-200`・説明 gray-500。iOS は scrim タップで閉じない。
- **Modal**: dismiss=×ボタン + プルダウン。全画面 or シート(0〜98%)。**× の位置**: ×のみ=右 / 進行タスク(Next/Save)=左 / 追加タスク(Edit)=右 / 深さあり=戻る左+×右。
- **Confirmation**: 建設的操作は原則確認なし（長待ち/不可逆/個人情報/認証は例外）。破壊的操作は原則確認（インラインスワイプ・些末操作は除く）。遷移/ナビ/閉じるでは確認しない。
- **Delete（重要度別3型）**: **Dialog Popup**(高重要度・中央・「復元不可」明記・Cancel/**Delete赤**) / **Action Sheet**(対象明示・下部) / **Toast**(低重要度・確認不要・フィードバックのみ)。破壊ラベル=赤。
- → Spot: `.modal-scrim`/`.modal-card`(コレクション作成/リネーム)。補える点: **ダイアログ幅 288px 基準・最大高 504px**、**× 位置規約**、**削除確認の重要度別3パターン**（Spot の「破壊的操作は確認」§1-6 を具体化）、**破壊ラベル=`--crit`**。

### 2.12 進捗・インジケータ（Progress / Spinner / Skeleton / Page Indicator / Page Controller）
- **Progress Indicator**: Linear(Determinate 0–100%/Indeterminate) / Circular(Indeterminate)。**Circular 径 XS20/S26/M40/L52・stroke 2.5/3/3/5px**。track gray-200、indicator=accent。状態 Before/In progress/Error。
- **Spinner**: 円形・時計回り・連続。**30×30 のみ提供**。中央配置(module/dimmed/dialog)。
- **Skeleton**: **shimmer 左上→右下**、bg **gray-150**、幅高可変。**progress indicator と併用しない**。
- **Page Indicator**: Dot(≤5=ページ数分, ≥6=間引き) / Number。**dot 径 S=5/L=7px**、active gray-800/inactive gray-300。外側16px/内側12px。Number 高 S=18/L=22px、bg opacity-black-40。
- **Page Controller(ページ送り)**: Prev/Next/番号/…。モバイル最大7・デスクトップ最大14。番号コンテナ **角丸5px**、選択=gray-900 塗り白太字。主にデスクトップ（モバイルは無限スクロール）。
- → Spot: `.skel`(実装済 ✓ shimmer)・`.spin`・`.toast .tsp`・メーター。補える点: **Circular progress の径/stroke 規格**（生成待ちの丸プログレス）、**Skeleton と spinner を併用しない**（Spot は skeleton 導入済＝正しい方向）、**Page Indicator**（ウィザードのステップ表示に流用可）。

### 2.13 その他（Avatar / Empty / Banner / Layout / Feedback）
- **Avatar**: 径 XXS**24**/XS**32**/S**42**/M**50**/L**60**/XL**72**/XXL**118**px。画像 or イニシャル(色+文字)。バッジ None/Number/Icon/Dot（XS・S は None のみ）。Outline True/False。Hover70/Pressed50%。→ Spot: サイドバー/メンバーのアバター。**径スケール(24/32/42/50/60/72)を規格化**すると散在を防げる。
- **Empty(空状態)**: 画像(任意, pictogram)/タイトル(任意)/説明/ボタン(**1推奨・最大2**)。中央配置。Large=全画面中央 / Small=モジュール中央。**煽り/CTA調の文言は避ける**。→ Spot: 空状態は「次の一歩」を出す方針(§1-3)と一致。**ボタン1つ・pictogram・中央**が具体規格。
- **Banner**: 背景/コンテンツ(タイトル/説明/ボタン)/画像(任意)/閉じる(任意)。プロモ/LAN/Smart。**13 の背景色**（各 Default+Pressed）。**トップナビ直下**、複数はページnetwork化、**1画面に複数積まない**、閉じる×は右上。→ Spot: お知らせ/プロモ帯に。**「1画面1バナー・×右上・注意を奪わない」**が指針。
- **Feedback（指針）**: 1操作に最低1つのフィードバック。Component/Motion/Transition/Haptic の4種。Component は自動消滅。→ Spot の「状態は色でも伝える」(§1-4) を補強。

---
<a id="3-reflection-plan"></a>
## 3. Reflection Plan（Spot への反映・優先度付き）

前提: Spot はダーク一本・indigo `--accent #4A67E3`・低ITリテラシー層向け Web SPA。LINE の**緑・ライト前提・ネイティブ chrome** は捨て、**役割設計・数値規格・状態・アナトミー・UXライティング**のみ移植する。既存トークン/クラス（`--accent`, `.hn-btn`, `.btn`, `.fld`, `.field`, `.badge`, `.toast`, `.modal-card`, `.skel`, `.u-meter`, `.filter`, `.sidebar` 等）を活かす前提。

**凡例**: P1=高価値・着手推奨 / P2=システム化 / P3=スケール・任意。効率=実装コスト（S小/M中/L大）。★=ダーク Web SPA で特に効くもの。

| # | 優先 | 効率 | 変更 | LINE 由来 → Spot 対象 |
|---|---|---|---|---|
| R1 ★ | **P1** | M | **フォームのエラー/必須/カウンタ整備**: 必須 `*`(赤・ラベル右)、**ライブ**インラインエラー（赤枠+赤ヘルプ、`--crit`）、プレースホルダ専用色、文字カウンタ `0/500`（gray-400相当=`--faint`）、コンテナ型は1画面1種 | Inputs/Text Input → `.fld`/`.field` |
| R2 ★ | **P1** | S | **ボタンの Loading 状態**（内部スピナー、`.spin` 流用）＋規約「主は右／縦積みは上」「disabled は文字のみ」 | Box/Action Button → `.btn`/`.btn-primary`/`.hn-btn` |
| R3 ★ | **P1** | S | **Toast の標準化**: 自動消滅 ~3–4秒、**常に1つ**、bg 黒80–85%相当、**toast=アクションなし / アクション要は別UI(snackbar)** の区別を明文化 | Toast Overlay/Snackbar → `.toast`/`window.toast()` |
| R4 | **P1** | S | **バッジ/チップの用途規約**: Number 溢れ **99+**、サイズ規格(16/18/20/24)、Chip を **Action/Filter/Choice** に分類、選択マーク ✓/+ | Badge/Chips → `.badge`/`.filter[aria-pressed]` |
| R5 ★ | **P1** | S | **削除確認の重要度別3型**: 高=Dialog（中央288px・「元に戻せません」明記・**Delete赤=`--crit`**）／低=Toast のみ | Delete/Confirmation → `.modal-card` |
| R6 | **P1** | S | **コントラスト運用の明文化**: 18.5px 境界＝Spot 本文14px は small→**4.5:1 必須**、`--faint` は本文不可（既存方針の裏付け） | Color Contrast → design-system.md §7 |
| R7 | **P1** | S | **アイコン統治ルール**: 24グリッド/2px余白/名詞命名/Regular・Solid の2形/ストローク一貫 | Iconography → SVG スプライト `.ic` |
| R8 ★ | **P2** | S | **意味色の「面上の文字色」正準化**: LINE の Category/Characteristic に倣い `on-*`（Nonadaptable）と `*-soft`+`*-ink` を規約化（§10-F を完了） | Semantic Colors → `--on-accent`/`--accent-ink`/`--accent-soft` |
| R9 | **P2** | S | **アバター径スケール規格**（24/32/42/50/60/72）でサイドバー/メンバーの散在を解消 | Avatar → `.sb-*`/`.member-row` |
| R10 | **P2** | S | **選択コントロールの状態拡張**: Checkbox に **Indeterminate/Error**、使い分け「多選=checkbox/単一=checkmark/確認=radio」、右端16px | Checkbox/Radio → `.switch-row` |
| R11 | **P2** | M | **タブ/フィルタの状態規格**: 下線2px、状態不透明度 100/70/50、Fixed 2–4・超過は横スクロール、Box タブ=フィルタpill | Tab/Tabs → `.filter` 群 |
| R12 | **P2** | S | **ナビ意思決定表の採用**: 項目 **3–5・4超はタブへ**、drawer dimmer 40%、**3階層ネスト禁止** | Navigation/Side Drawer → `.sidebar` |
| R13 | **P2** | M | **リスト規格**: 左メディアのアスペクト(1:1/4:3/16:9)、**右アクション≤2**、Highlighted(新規)行、ロード時 Skeleton（実装済 ✓） | List → メディア/メンバー一覧 |
| R14 | **P2** | S | **空状態の規格**: pictogram＋タイトル＋説明＋**ボタン1つ**・中央、煽り文言なし | Empty → 各 view の空状態 |
| R15 ★ | **P3** | L | **モバイル Bottom Sheet** 導入（角丸上14px・幅100%・ハンドルバー・Modal/Interactive）。低ITリテラシー層の「選ぶだけ」に好適 | Bottom Sheet → 新規（≤1080px） |
| R16 ★ | **P3** | M | **モバイル FAB**（直径54・右下16px・"新規CM"主導線）。Pill FAB=「新規CM」 | FAB → 新規（モバイル） |
| R17 | **P3** | M | **Tooltip / コーチマーク**（初回チュートリアル, memory: first-run tutorial）。画面端≥8px・対象から2–8px・最大3行・1画面1つ | Tooltip → 新規 |
| R18 | **P3** | S | **ダーク面の pressed=明るく**（LINE の V≤32%→+45%）を確認（Spot の `--pressed` 白オーバーレイは整合） | LINE Color Guide → `--pressed`/`--accent-hover` |
| R19 | **P3** | S | **Circular progress 規格**（径 XS20/S26/M40/L52・stroke 2.5–5px）を生成待ちに | Progress Indicator → 生成待ち UI |
| R20 | **P3** | S | **ウィザードの Page Indicator**（dot 5px/active・step 表示） | Page Indicator → `view-wizard` |
| R21 | **P3** | S | **グリッド・ガター**: 密な一覧は 8px ガター、モバイルは左右16px 最低線 | Layout → `.proj-grid`/`.wrap` |
| R22 | **P3** | L(任意) | **トークン value を100刻みスケール**に（`--t-*`/`--s-*` の別名）。運用コスト高につき任意 | Overview トークン思想 → `tokens.css` |

### ✅ P1 反映済み（2026-10-06）
R1〜R7 を `spot-app/index.html` と `docs/design-system.md` に反映した。
- R1: `fieldLive` / `fieldCounter` / `fieldSetError`（§3.7）— 設定系 `.fld` と台本欄にも検証・必須 `*`・カウンタ・プレースホルダ色。
- R2: `btnBusy()`（§3.8）— 保存・招待・パスワード変更・削除の直書き `disabled` を置換。`disabled`=薄く／`aria-busy`=薄くしない。
- R3: `toast` 既定 3.2 秒・常に 1 つ・アクションなし。行動が要るときは `snackbar()`。
- R4: `.badge--num` ＋ `fmtCount()`（99+）、選択チップの ✓ 前置、チップ 3 分類（§3.4）。
- R5: `openConfirm({irreversible:true})` で「元に戻せません」明記・肯定=右・モバイル幅 320。ワークスペース/アカウント/動画の削除に適用。
- R6/R7: §7 コントラスト運用規約、§3.9 アイコン統治ルール。

### ✅ P2 反映済み（2026-10-06）
- R8: `--warn-soft` / `--on-warn` / `--on-crit` / `--on-brand-red` を追加し §10-F 完了（`.badge--warn` と `.btn-danger` をトークン化）。
- R9: `--av-xs…--av-2xl` の径スケール。34/40px の散在を 32/42 に統一。
- R10: `.switch-row` の Indeterminate / Error / Disabled と使い分け規約。
- R11: `.filters` の横スクロール、無効状態 .5、Box タブ＝フィルタの規約。
- R12: `.sb-scrim` 40%、項目 3〜5・2 階層までを規約化。
- R13: `.proj.is-new`（24 時間以内）＋「新着」バッジ、右アクション ≤2 を規約化。
- R14: 空状態にボタン 1 つ（コレクション空に「メディアを開く」）。
### ✅ P3 反映済み（2026-10-06）
- R15: シート上角を `--r-sheet` 14px に統一（アカウントメニュー・コレクション移動）、**中重要度の確認をモバイルでは ActionSheet**（`.modal-card.as-sheet`）に。高重要度は中央ダイアログ。
- R16: FAB を `--fab` 54px に。400〜720px は Pill FAB（「新規CM」ラベル）。
- R17: Tooltip(Small)＝`data-tip`（title を自動移行）、Coachmark(Large)＝`showCoachmark()`（オンボーディング後のホームで主導線を指す・一度きり）。
- R18: `--pressed` の整合を確認（文書化）。
- R19: `.cprog`＋`cprogHtml()`（径 20/26/40/52）。生成の進捗に適用。
- R20: `.page-ind` をウィザードの「ステップ N / 4」に併記。
- R21: ガター規約を文書化。R22: 不採用（文書化）。
LINE Design System の反映は P1〜P3 で完了。

### 最優先7項目（P1）の補足
- **R1 フォーム**: Spot は入力の共有スタイルをトークン統一済み（§3.7）。欠けているのは**エラー/必須/カウンタの体系**。LINE は「focus=青枠 / error=赤枠+赤ヘルプ+カウンタ色分け / 必須*赤」を厳密規定。低ITリテラシー層には**送信前のライブ検証**が特に効く（LINE も「エラーは送信後でなくライブ」を明記）。値サイズは 16px 推奨（Spot `--t-title`）＝iOS の入力ズーム回避にもなる。
- **R2 ボタン Loading**: 生成・保存・購入など待ちが発生する主アクションに内部スピナー。既存 `.spin`/`.toast .tsp` を流用。あわせて「1画面1 primary（白と青を併置しない, §11）」は LINE の「1画面1緑/赤」と同一なので**現行規約が LINE 準拠であることを明記**。
- **R3 Toast**: Spot の `window.toast(msg, ok, ms)` に**既定 ms=3000–4000・同時1つ・下16px・bg 不透明黒**の規範を与える。LINE の「toast はアクションを持たない／アクションが要るなら snackbar」を Spot のフィードバック指針(§3.8)に追記。
- **R5 削除確認**: Spot の「破壊的操作は確認」(§1-6)を**重要度別に具体化**。高重要度（コレクション削除等）は中央ダイアログで「**元に戻せません**」を明記し Delete を `--crit`、低重要度（キャッシュ的操作）は Toast のみ。
- **R6/R7**: いずれもドキュメント／統治ルールで、実装コストほぼゼロ。既存の良い実装（コントラスト検証済・スプライト運用）を LINE 基準で裏付け・固定化する。

---
<a id="4-not-applicable"></a>
## 4. Not applicable to Spot（記録のみ）

LINE アプリ固有の chrome／ブランドイラスト／LINE プラットフォーム機能。開封のうえ Spot 非該当と確認（一部に転用可能な原則あり）。

- **Character Graphic** — LINE マスコットの作画規定（顔比率・7頭身）。転用なし。
- **Object Graphic** — LINE 用スポットイラスト集（二色線）。ブランド固有、転用なし。
- **Chats** — LINE メッセンジャーのチャット一覧/会話画面のケース。転用なし。
- **Home** — LINE Home タブ（トップ/ボトムナビ・友だち追加動線）。転用なし。
- **Flex Message** — チャット内リッチメッセージ。ブロック順 Header→Hero→Body→Footer の**カード構成階層**のみ一般原則として参考。
- **LIFF View** — LINE Front-end Framework の webview モーダル。転用なし。
- **LINE OpenChat** — 興味関心グループ機能のケース。転用なし。
- **LINE VOOM** — LINE のソーシャルフィード。転用なし。
- **LINE Voice** — （ビジュアルでなく）**UXライティング指針**。CLEAR/CONVERSATIONAL/ボタンは意図を書く＝Spot に**強く該当**（§1.6 に反映済）。
- **Keep** — 保存コンテンツのロッカー。検索+タブ+複数選択の一般パターンのみ。
- **Image Grid** / **Image Grid Mobile Only** — 画像グリッド。**アスペクト 4:3/3:4/1:1、全幅375/16pxマージン343** の数値は §1.5 に採録。
- **Footer Mobile Only** — フッタ（social icon M=30/L=36px、最大5–6個、**フッタ＝メタ情報専用**）。Web の Spot では site 側フッタに軽く参考。
- **Video Player** / **Video Player２** — 動画プレーヤー。状態機械（Before/AD/Playing/Seek/Ended/Error）は一般的だが Spot はプレビュー再生が主で該当薄。

---
<a id="5-coverage"></a>
## 5. 98 PDF カバレッジ一覧

全 98 ファイル・計663ページを閲覧。F=Foundation（本レポート筆者が全読）、C=Component（サブエージェントが全読）、N=Not applicable（開封確認）。

| # | ファイル | 種 | 一行メモ（要点/実数） |
|---|---|---|---|
| 1 | Action Button.pdf | C | Contained/Outlined/Ghost, XL–XS, disabled#E4E4E4, 角丸3/5/7, Full-Bleed |
| 2 | Avatar.pdf | C | 径 24/32/42/50/60/72/118px, hover70/pressed50, badge |
| 3 | Badge.pdf | C | Dot 5/8/10/14/20・Number高16/18/20/24/36px, 溢れ99+ |
| 4 | Badge2.pdf | C | N/Dot/Number, 999+, GNB=赤/他=緑 |
| 5 | Banner.pdf | C | プロモ/LAN/Smart, 13背景色, ×右上, 1画面1バナー |
| 6 | Bottom Navigation.pdf | C | 3–5項目, 選択solid, バッジ, スクロールで消えない |
| 7 | Bottom Navigation２.pdf | C | 幅100%/高Auto, Number999+バッジ, 最大5 |
| 8 | Bottom Sheet.pdf | C | 角丸上14px, 幅100%, Modal/Interactive, 画像375幅 |
| 9 | Bottom Sheet2.pdf | C | 角丸14固定, ハンドルバー3段スナップ |
| 10 | Box Button.pdf | C | Solid/Outline(緑/赤/灰), Loading, 主は右/縦は上 |
| 11 | Capsule Button.pdf | C | スクロール誘導pill, 高42pt, padding 26/7/16 |
| 12 | Card.pdf | C | Surface/Full-image, カード全体タップ=詳細, インジケータ非タップ |
| 13 | Character Graphic.pdf | N | LINEキャラ作画規定, 転用なし |
| 14 | Chats.pdf | N | LINEチャット画面ケース, 転用なし |
| 15 | Checkbox.pdf | C | Indeterminate/Error, 親子伝播, 多選択 |
| 16 | Checkbox２.pdf | C | box26pt, Number型(3桁), 配置右16pt/画像8pt |
| 17 | Checkmark.pdf | C | 単一選択の緑チェック, 即時, リスト右 |
| 18 | Chip.pdf | C | Contained/Outlined, 既定Pill, padding固定, 幅自動 |
| 19 | Chips.pdf | C | Action/Filter/Choice, 選択✓/未+, 改行なし |
| 20 | Color Contrast.pdf | F | Must3.0/Should4.5/Consider7:1, small<18.5px, WCAG A/AA/AAA |
| 21 | Color Usage.pdf | F | 階層色 Title黒/Body Gray600/Caption Gray500, Link Blue600 |
| 22 | Confirmation.pdf | C | 建設的=確認なし/破壊的=確認, 遷移では確認しない |
| 23 | Delete.pdf | C | Dialog/ActionSheet/Toast の重要度別3型, Delete赤 |
| 24 | Design Principle.pdf | F | 6原則(WE≠USERS/主タスク直感/信頼/一貫/legacy尊重) |
| 25 | Empty.pdf | C | pictogram+タイトル+説明+ボタン1(最大2), 中央, 煽らない |
| 26 | Feedback.pdf | C | 1操作1フィードバック, Component/Motion/Transition/Haptic |
| 27 | Flex Message.pdf | N | チャット内リッチメッセージ, Header→Hero→Body→Footerのみ参考 |
| 28 | Floating Action Button.pdf | C | Circle(Single/Expandable)+Pill, brand-primary塗り, radius-circle |
| 29 | Floating Action Button２.pdf | C | 径54pt/icon38pt, 緑/白, 右下16pt, 子3–6 |
| 30 | Footer Mobile Only.pdf | N | フッタ, social icon30/36px, フッタ=メタ専用 |
| 31 | Home.pdf | N | LINE Homeタブケース, 転用なし |
| 32 | Icon Button.pdf | C | S32/L52px, Contained/Outlined/Slot, group3–5, hover70/pressed50 |
| 33 | Icon Guideline.pdf | F | 24グリッド/2px余白, stroke1.3(1.3/1.5/1.8), 角丸0–2, 名詞命名 |
| 34 | Icon button２.pdf | C | Solid/Stroke, Single/Toggle, container38pt |
| 35 | Iconography.pdf | F | LAICON, category(Pictogram/Brand/ETC)+shape(Regular/Solid), 45°角度 |
| 36 | Image Grid Mobile Only.pdf | N | 全幅375/343, アスペクト4:3/3:4/1:1（§1.5採録） |
| 37 | Image Grid.pdf | N | 2/3col・Medium+Small等の列taxonomy, 既定3行 |
| 38 | Inputs.pdf | C | 旧Messenger入力(Large/Small/Password/Code), 概念/状態 |
| 39 | Keep.pdf | N | 保存ロッカー, 検索+タブ+複数選択のみ |
| 40 | LIFF View.pdf | N | LINE webviewモーダル, 転用なし |
| 41 | LINE Color Guide.pdf | F | Gray900#111111他, Blue500=btn/Blue700#2C53DE, 透明度規約, pressed HSV式 |
| 42 | LINE New Design.pdf | F | LDS適用ケース, "simple&light", Card/List/Profile/Banner/TopNav/Tabs |
| 43 | LINE OpenChat.pdf | N | OpenChat機能ケース, 転用なし |
| 44 | LINE Semantic Colors.pdf | F | 命名[Numeral+Assistive+Characteristic+Category], primaryText #000/#fff |
| 45 | LINE VOOM.pdf | N | ソーシャルフィード, 転用なし |
| 46 | LINE Voice.pdf | N | UXライティング(CLEAR/CONVERSATIONAL)＝Spot強く該当(§1.6) |
| 47 | Layout.pdf | F | 左右16px, 内容幅343, 2col167/g9・3col109/g8・4col82/g5 |
| 48 | Layout２.pdf | F | Layout と同一内容（重複） |
| 49 | List Header.pdf | C | タイトル+右ボタン(なし/Text/Icon/Dropdown), ソートは▾ |
| 50 | List.pdf | C | 左メディア(1:1/4:3/16:9)+右≤2, Highlighted新規, Skeleton |
| 51 | Modal.pdf | C | ×ボタン+プル, ×位置規約, 全画面/シート(0–98%) |
| 52 | Navigation.pdf | C | 意思決定表: drawer4超非推奨/bottom3–5/tab2超 |
| 53 | Object Graphic.pdf | N | LINEスポットイラスト, 転用なし |
| 54 | Overview.pdf | F | トークン命名 LDSG+Element+Category+Value(100刻み), 8要素, #06C755 |
| 55 | Page Controller.pdf | C | ページ送りPrev/Next/…, 角丸5px, 最大7/14, 主にデスクトップ |
| 56 | Page Indicator.pdf | C | dot 5/7px, active gray-800, 外16/内12px, Number高18/22 |
| 57 | Page Indicator２.pdf | C | 旧版, ドット≤10・省略時7, Number 8pt/22pt |
| 58 | Popup.pdf | C | **幅288px固定・最大高504px**, 4型, 縦/横ボタン |
| 59 | Popup２.pdf | C | 旧版, affirmative右/上・dismissive左/下, iOSはscrim閉じず |
| 60 | Profile.pdf | C | 径30/32/42/50/56/60/87/95pt, Single/Multiparty/Grouped |
| 61 | Progress Indicator.pdf | C | Circular径20/26/40/52・stroke2.5/3/3/5, track gray-200 |
| 62 | Progress Indicator２.pdf | C | 旧版, Linear/Circular, Before/In/Error/Complete |
| 63 | Pulldown Menu.pdf | C | min-width112px, 端≥8px/アンカー2–8px, ≤6項目 |
| 64 | Pulldown.pdf | C | Text Input同型+chevron-down, gap12px |
| 65 | Radio Button.pdf | C | 1グループ1選択・既定選択必須, Error赤 |
| 66 | Radio Button２.pdf | C | box26pt/内円12pt, 配置右16pt/画像8pt |
| 67 | Rainbow Color.pdf | F | 拡張パレット(Lime〜Navy, 各300–900+p), 装飾専用, LINE Indigoあり |
| 68 | Search Bar.pdf | C | アイコン/入力/リセット/Cancel, 履歴/オートコンプリート/インスタント |
| 69 | Segmented Control.pdf | C | S32/M36/L44, 2–4項目, タブの下に置く |
| 70 | Select.pdf | C | UX指針, 単一=radio/複数=check or 番号, 選択順表示 |
| 71 | Share.pdf | C | 共有フロー, half-modal, フィードバックはsnackbar/toast |
| 72 | Side Drawer.pdf | C | 幅既定280(最大300/80%), dimmer40%, 3階層禁止 |
| 73 | Skeleton.pdf | C | shimmer左上→右下, bg gray-150, progressと併用しない |
| 74 | Slider.pdf | C | thumb18/hover24, padding8/10, track#DFDFDF, ラベルr5/Bold13 |
| 75 | Slider２.pdf | C | 旧版, Continuous/Discrete, Drag/Tap, 縦可 |
| 76 | Snackbar.pdf | C | 幅100%, 下16px, 自動~3秒(4–10選択), bg黒85%, Action=accent |
| 77 | Snackbar２.pdf | C | 旧版, 下15pt/上43pt, blur背景, snackbar=全域リンク |
| 78 | Spinner.pdf | C | 30×30のみ, 時計回り連続, 中央配置 |
| 79 | Stepper.pdf | C | S32/M46, 最小でminus disabled, 小数不可 |
| 80 | Switch.pdf | C | On=accent即時, リスト右16pt, 左置き禁止 |
| 81 | Switch２.pdf | C | 旧版, 背景=On/dim=Off, 既定必須 |
| 82 | Tab.pdf | C | Flexible/Fixed(2–4), 下線M2/S1px, 状態100/70/50 |
| 83 | TabExpanded Tab List.pdf | C | flexible専用展開, padding20/gap8/行間12px |
| 84 | Tabs.pdf | C | Text/Box(黒塗り白=フィルタ)/Icon, Fixed2–4 |
| 85 | Tag.pdf | C | Pill50%/Rect0-3-5-7px, padding固定/幅可変/高固定 |
| 86 | Text Area.pdf | C | ヘルプMin62/Max207, 16px/1.4, カウンタ0/500 |
| 87 | Text Button.pdf | C | Primary/Destructive/Secondary(暗=白)/Retreative, gap18pt |
| 88 | Text Input.pdf | C | Contained/Outlined/Underlined, focus青枠, 必須*赤, ライブエラー |
| 89 | Toast Overlay.pdf | C | Icon/Text, Bottom幅=画面-32, 自動~4秒, bg黒80%, 常に1つ |
| 90 | Toast Overlay２.pdf | C | 旧版, icon123×46pt, text max305pt, フェード0.5秒 |
| 91 | Tooltip.pdf | C | Large/Small, 最大3行, 端≥8/対象2–8px |
| 92 | Tooltip２.pdf | C | 旧版, padding12/11pt, close14/13pt, 1ページ1つ |
| 93 | Top Navigation.pdf | C | 高iOS44/Android56/Sub50, title max136, icon24/stroke1.5, 端12/間16 |
| 94 | Top Navigation２.pdf | C | Emphasis/Regular/Search型, flexible header, ダーク#111111 |
| 95 | Typography.pdf | F | LDSGトークン[Lang/Type/Size/Fontsize/Weight], Title/Text, 下限12 |
| 96 | Typography２.pdf | F | 推奨スケール H1 24/Title1 23/Body1 16等, OSフォント, 多言語配慮 |
| 97 | Video Player.pdf | N | 動画プレーヤー状態機械, Spot該当薄 |
| 98 | Video Player２.pdf | N | 旧版プレーヤー, Fullscreen/Module, 該当薄 |

**カバレッジ**: **F=14**（Overview, Design Principle, LINE New Design, LINE Color Guide, Color Usage, LINE Semantic Colors, Rainbow Color, Color Contrast, Typography, Typography２, Iconography, Icon Guideline, Layout, Layout２）／**C=69**／**N=15**。合計 **98/98 = 100% 閲覧済**（Foundation・主要 Component は全ページ精読、N は開封確認）。
