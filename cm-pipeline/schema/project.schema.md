# project.yaml スキーマ定義

CM1本を宣言的に定義するスキーマ。ミライ工事案件から抽出した「型」。
CLI各コマンドはこの yaml を読んで動作する。

---

## トップレベル構造

```yaml
meta:        # 案件メタ情報
output:      # 書き出し仕様（尺・fps・形式）
brand:       # ブランドキット（色・ロゴ・発音辞書）
style:       # 画づくりトーン・グレードの参照
script:      # ナレーション行とテロップ
cuts:        # カット表（順序付き・タイムラインの実体）
audio:       # BGM・サウンドロゴ・効果音
compliance:  # 開示・認証・法務（省略時は全て ON）
delivery:    # 配信先。styles/platform-specs.yaml の入稿仕様を build に適用
```

---

## `meta`

```yaml
meta:
  name: mirai-koji            # プロジェクトID（ディレクトリ名と一致）
  client: 株式会社ミライ工事
  product: ミライ工事写真       # 工事写真台帳アプリ
  goal: 認知獲得・アプリDL促進   # このCMの目的
```

## `output`

```yaml
output:
  fps: 30
  duration_frames: 961        # カバー1f + スプラッシュ2s + 本編30s
  formats:                    # 書き出す全形式。各々でクロップ/レイアウトが自動対応
    - {id: wide,     w: 1920, h: 1080}   # 16:9 YouTube/サイト
    - {id: vertical, w: 1080, h: 1920}   # 9:16 リール/ショート
    - {id: square,   w: 1080, h: 1080}   # 1:1 タイムライン投稿
  variants:                   # イントロ違いのA/B/Cパターン
    - {id: A, splash: ring-marimba}
    - {id: B, splash: confetti-ukulele}
    - {id: C, splash: bubble-electro}
```

## `brand`

```yaml
brand:
  colors:
    primary: '#D7000F'        # ブランドレッド
    accent:  '#FFC933'
  logo:      assets/logo/m_logo.svg
  app_icon:  assets/logo/app_icon.png
  watermark: {text: ミライ工事, position: top-left}   # 全画面固定ロゴ
  pronunciation:              # TTSの読み制御（商品名のイントネーション対策）
    ミライ工事写真: "ミライコウジシャシン"   # カタカナ表記で正しいアクセント
    # 文中に埋めると平板化するため、台本側で「。」区切りにするのも併用
```

## `style`

```yaml
style:
  tone: documentary           # styles/documentary.yaml を参照
  grade: broadcast-cool       # styles/grades.yaml を参照
  realism_fx:                 # 実在感の仕上げ（全実写カット共通）
    grain: 0.07               # 動的フィルムグレイン不透明度
    handheld_drift: true      # 手持ち風マイクロドリフト
    ambience_bed: 0.20        # 環境音ベッドの音量
  living_world: contextual    # 背景の生命。ただし「停車中の車内」等は文脈でOFF
```

## `script`

ナレーションとテロップ。`cut` から index で参照する。

```yaml
script:
  narration:                  # LoyalKnight音声・カタカナ発音・無音トリム
    - {id: na1, text: "現場写真の整理、まだ会社に持ち帰ってますか?"}
    - {id: na2, text: "取り込んで、仕分けて、貼り付けて。毎日、何時間かかっていますか?"}
    - {id: na3, text: "ミライ工事写真、スマホで撮るだけで、工事台帳が自動でできあがる。"}
    - {id: na4, text: "現場を出る前に、PDFまで完成。"}
    - {id: na5, text: "お客様への提出も、その場で完了。持ち帰りゼロへ。"}
    - {id: na6, text: "ミライ工事写真、今すぐ無料でダウンロード。"}
  voice: {model: minimax-speech-02-hd, voice_id: Japanese_LoyalKnight, speed: 1.18}
```

## `cuts`（中核）

タイムラインの実体。各カットは `type` で挙動が決まる。

```yaml
cuts:
  # --- 実写カット（AI生成：スチル→動画化） ---
  - id: cut01
    type: live-action
    from: 0            # 本編内フレーム（スプラッシュ後基準）
    dur: 125
    still:                          # スチル生成
      model: imagen4
      prompt_ref: styles.documentary.van-interior   # 語彙はスタイルから合成
      subject: "疲れた40代の現場監督が停車中の車内でため息"
      props: ["助手席の書類の山", "コンパクトデジカメ"]
    consistency: {ref: cut01, model: nano-banana}   # 主演の顔・服を固定
    motion:                         # 動画化
      model: veo3.1                 # 配役表に従う（明部・動き＝Veo）
      resolution: 1080p
      prompt: "停車・窓外は完全静止。目を閉じ→ため息→伏し目で書類を見る"
      gaze: downcast                # カメラ目線禁止
    crop: {anchor_x: 55, portrait_native: cut01_v}  # 縦/正方形は専用素材
    telop: ["写真整理は、会社に帰ってから…?"]
    narration: na1

  # --- UIカット（コード描画：Remotion） ---
  - id: cut3b
    type: ui
    from: 410
    dur: 110
    ui: auto-ledger                 # 台帳が自動作成される演出
    assets: {camera: ui2_camera, ledger_empty: ui2_list_empty, ledger_full: ui2_list_filled}
    animation: photo-fly-to-ledger  # 写真が飛んで行がポップイン
    sfx: [shutter, pop, pop, pop]
    telop: ["スマホで撮るだけ。台帳が自動作成"]

  # --- グラフィックカット（数字演出等） ---
  - id: cut2b
    type: graphic
    from: 255
    dur: 65
    graphic: stat-countup           # 「月40時間」カウントアップ
    value: {label: "その作業に、月", number: 40, unit: "時間。", note: "※自社調べ"}
    background: papers-falling       # 舞う書類の実写背景

  # --- CTAカット ---
  - id: cta
    type: cta
    from: 795
    dur: 105
    badges: ["累計50万DL突破", "プロジェクト300万件突破"]
    button: "今すぐ 無料ダウンロード"
    store: [app-store, google-play]
    narration: na6
```

### `cut.type` 一覧

| type | 生成方法 | 用途 |
|---|---|---|
| `live-action` | AI（スチル→動画化） | 人物・実写シーン |
| `ui` | コード描画（Remotion） | アプリ画面のデモ。文字が崩れない |
| `graphic` | コード描画 | 数字演出・図版・タイトル |
| `splash` | コード描画 | サウンドロゴ用のブランド演出 |
| `cta` | コード描画 | 検索窓・実績バッジ・ボタン |
| `cover` | コード描画 | 0フレーム目のポスター画像 |

## `audio`

```yaml
audio:
  sound_logo: {model: elevenlabs-sfx-v2, ref: styles.sound-logo.two-part}
  brand_call: {text: "ミライコウジ!", voice: minimax, sync_to: sound_logo_beat2}
  bgm:                              # 悩み→転調→解決の2トラック
    - {id: problem,  model: lyria2, mood: melancholic-piano, span: [0, splash_end]}
    - {id: solution, model: lyria2, mood: uplifting-corporate, span: [splash_end, end]}
  sfx_trim: waveform-silence        # 生成SEは頭の無音を波形解析でトリム
```

## `compliance`

競合調査（research/competitive-research-2026-09.md）の結論「法務を武器にする」を型にしたもの。
海外の AI 広告 SaaS が持たず、国内の制作サービス型が「人の目」で担保しているものを、データとして宣言する。
**省略時は全て ON**（安全側デフォルト）。spot-app の `projects.spec.compliance` と同形。

```yaml
compliance:
  ai_disclosure: true         # 末尾にAI利用表記を焼き込む（JIAA 自主開示ガイドライン 2026-04 準拠）
  disclosure_lang: ja         # ja / en / both。文言は styles/platform-specs.yaml の disclosure
  content_credentials: true   # C2PA コンテンツ認証情報を書き出しに付与（生成モデル・編集履歴・ブランド素材）
  likeness_check: true        # 実在人物との類似を review 段階で検査（quality-rules D3）
  real_ui_only: true          # type: ui のカットは提供スクショ / コード描画のみ。生成UIを禁止（景表法）
  claims_evidence:            # 数値訴求の根拠。build がテロップ注記（※）を自動付与する
    - {claim: "月40時間", source: "自社調べ", note: "※自社調べ"}
```

## `delivery`

```yaml
delivery:
  platforms: [youtube, reels_shorts, timeline]   # styles/platform-specs.yaml のキー
  # build は platform → format を引き、セーフゾーン・字幕焼き込み・ラウドネス・尺上限を適用する。
  # 同じ企画を全媒体の入稿仕様で一括納品するのが SPOT の差別化（媒体内蔵ツールは単一媒体）。
```

---

## 設計上の要点（ミライ工事案件からの学び）

- **cut は「意味」で宣言し、実装はパイプラインが選ぶ** — `motion.model` の Kling/Veo 振り分けは
  配役表（暗部＝Kling / 明部・動き＝Veo）のデフォルトに従い、上書きも可能。
- **crop.portrait_native** — スマートクロップで重要要素が外れるカットだけ、縦ネイティブ素材を指定。
  9割はアンカー基準のクロップで賄う。
- **検品は cut 単位** — 各 live-action cut のスチルを quality-rules.md のチェックリストで検査し、
  NG（手の指・小道具の形状・光のフレア等）はスチル段階でリトライ（動画化前に潰す）。
- **状態管理** — 生成物は `generated/<cut_id>.<ext>` + `.done` マーカー。再開時にスキップ。
