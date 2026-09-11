# cm-pipeline

AIコマーシャル動画制作パイプライン（Phase 1 / CLI）。

ミライ工事CM制作で確立した手作業ワークフローを、設定ファイル駆動の再利用可能な
パイプラインに昇華させたもの。`project.yaml` に案件を宣言すると、
スチル生成 → 検品 → 動画化 → 合成 → マルチフォーマット書き出しまでを実行する。

## 設計思想

1. **状態はファイルで持つ** — 生成物は `generated/`、承認フラグや原価は yaml に記録。
   途中で止まっても `.done` マーカーで再開でき、課金APIの二重実行を防ぐ。
2. **スタイル＝コードでなくデータ** — 画づくりの語彙・品質ルールは `styles/*.yaml`。
   業種・トーンの追加は「データ追加」で済む（プロンプトをコードに埋めない）。
3. **生成→検品→リテイクを1ループ** — 各生成物は視覚LLMの検品を通し、
   NGなら理由付きで自動リトライ。検品プロンプトには品質エンジンのチェックリストを注入。
4. **人はCDでなく判定者** — 選択肢の設計に専門知識を埋め込み、
   ユーザーは「良品の中からの好み選び」だけを行う（P1: CDができない人でも使える）。

## ディレクトリ構成

```
cm-pipeline/
  schema/
    project.schema.md    # project.yaml のスキーマ定義（このドキュメント群の中核）
  styles/
    documentary.yaml     # 「ドキュメンタリー調」の画づくり語彙（検証済み）
    grades.yaml          # カラーグレード定義（放送用クール 等）
    quality-rules.md     # 検品チェックリスト（AI感・破綻の潰し方）
    model-casting.yaml   # 工程別のモデル配役表
  projects/
    mirai-koji/
      project.yaml       # ミライ工事CM（1件目の実案件＝型の実例）
      assets/            # UIスクショ・ロゴ等の入力素材
      generated/         # 生成物（スチル・クリップ・音声）
      out/               # 最終書き出し（形式別）
```

## セットアップ

```
cd cm-pipeline
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/pip install -e .        # `cm` コマンドを venv に登録（任意）
```

以降は `cm <sub> <project>`（または `./.venv/bin/python -m cm <sub> <project>`）。

## コマンド（Phase 1a 実装済み）

```
cm validate <project>            # project.yaml の schema 準拠チェック
cm stills   <project>            # カット表 → スチル生成（Imagen 4 / Seedream / nano-banana）
cm review   <project> [--retake] # 視覚LLMで検品 → NG理由レポート（--retake でNGを再生成対象へ）
cm animate  <project>            # 承認スチル → 動画化（配役表に従い Kling / Veo 振り分け）
cm audio    <project>            # NA / BGM / サウンドロゴ 生成（発音辞書・声・トラック別mood）
cm build    <project>            # Remotion 合成 → 媒体×パターン別に納品（out/<platform>/、開示テロップ・C2PA・媒体仕様適用）
cm run      <project>            # stills→review→animate→audio→build を一気通し
cm cost     <project>            # 生成原価の集計（USD / ¥ / クレジット換算）
cm clean    <project>            # .done マーカーを削除して再生成可能に
```

**既定は DRY-RUN**（課金なし・原価は概算だけ台帳に計上・`generated/` に生成内容のプレビューを出力）。
実際に fal.ai で生成するときだけ `--live` を付ける（`../.fal_key` を読む。`--key` で上書き可）。
`.done` 冪等マーカーにより途中再開でき、課金APIの二重実行を防ぐ（`--force` で無視して再生成）。

```
cm run mirai-koji            # まず全工程をドライランで確認（無料）
cm stills mirai-koji --live  # 良ければステージ単位で実生成
cm cost  mirai-koji          # かかった原価を集計
```

Phase 1完了条件: 2案件目を `cm` コマンドで半日で回せること。
実装の地図は [schema/architecture.md](schema/architecture.md)（Phase 1a→1b→2 の一本道）。

## 汎用コンポジション SpotAd（2件目以降は TSX を書かない）

`cm build` の既定コンポジションは `SpotAd`（`ad-prototype/src/SpotAd.tsx`）。`cm/remotion_props.py` が
project.yaml のカット表を props に写像し、カバー 1f → スプラッシュ（A: リング / B: コンフェッティ / C: バブル）→
本編（live-action / ui / graphic / cta）→ ウォーターマーク・ナレーション・BGM をデータで組む。

- 素材は `ad-prototype/public/projects/<name>/` に自動 staging（`generated/<cut>.mp4`、`<cut>.still.png`、`audio/*.mp3`、`assets/**`）。
  `src: mirai/cut01_veo.mp4` のように public 配下の既存パスはそのまま参照できる。
- 動画未生成のカットはスチル（Ken Burns）→ それも無ければ「生成待ち」プレースホルダで描く。UI カットはスクショが無ければ
  明示的なスケルトン（偽 UI は描かない）。
- 尺は `cut.dur`（未指定は均等割り）。`output.splash_frames` でスプラッシュ長を変更。
- 1件目の `mirai-koji` は `render: {composition: MiraiCM}` で手作り版を維持。2件目の型検証は `projects/demo-saas`
  （`cm build demo-saas` で 9 ファイル。既存クリップを `src` で参照）。

## 配信仕様と法務（build の出口）

`cm build` は `project.yaml` の `delivery.platforms` と `compliance` を読み、`styles/platform-specs.yaml` の
入稿仕様を適用して媒体別に納品する（競合調査 `../research/competitive-research-2026-09.md` の「法務を武器に」「全媒体一括納品」）。

- **composition の切替**: Root.tsx の規約 `{base}{-B|-C}{-V|-SQ}` で形式ごとに正しいサイズのコンポジションを選ぶ（`render.composition_pattern` で上書き可）。
- **props**: `compliance.disclosure`（AI 利用開示テロップ・末尾 2 秒）、`compliance.safeZone`（リール 上14%/下35% 等。Telop / Watermark が避ける）、`captions`。
  Remotion 側は `ad-prototype/src/Compliance.tsx`（`DisclosureCaption` / `SafeZoneGuides` / `useSafeInsets`）。
- **後処理**: ffmpeg でラウドネス正規化（−14 LUFS）、サイネージは無音化、尺・容量の上限チェック（警告）。
- **C2PA**: 使用モデル（`.done` マーカー集計）・編集履歴（ledger）・ブランド素材・数値訴求の根拠をマニフェスト化。
  `c2patool`（`brew install c2patool`）で mp4 に埋め込み署名。未導入なら `<file>.c2pa.json` サイドカーのみ。
  署名鍵は環境変数 `C2PA_SIGN_CERT` / `C2PA_PRIVATE_KEY`（PEM パス、任意で `C2PA_ALG` / `C2PA_TA_URL`）。
  未設定時は c2patool 内蔵のテスト証明書で署名される（検証は通るが発行者が "C2PA Test Signing Cert" になる＝本番不可）。
  本番用の証明書は CA 発行のコード署名証明書か、Content Credentials 対応の署名サービスを用意すること。
- **出力**: `out/<platform>/<name>_<variant>_<platform>.mp4` と `out/delivery.json`（全ファイルの仕様・警告・props）。

```yaml
compliance: {ai_disclosure: true, disclosure_lang: ja, content_credentials: true, likeness_check: true, real_ui_only: true}
delivery:   {platforms: [youtube, reels_shorts, timeline]}   # 省略時は output.formats から推定
```

## Orchestrator（Phase 1b 実装済み）

Phase 1a のステージ・ロジックを、非同期ジョブDAG＋ワーカープールで回す層（`cm/orchestrator/`）。
カット表を `still→review→animate` の直列チェーンに展開し、`audio`／`build` を加えて DAG 化。
依存が揃ったジョブから**並列実行**し、進捗を SSE で配信、状態を JSON で永続化する。
CLI と同じ `cm.pipeline` の per-cut 関数を呼ぶため、ロジックの二重管理は無い。

```
cm orchestrate <project> [--workers N]   # DAGをインプロセスで実行（進捗を標準出力へ）
cm serve [--host --port]                 # HTTP/SSE サーバを起動
cm submit <project> [--live --workers N] # 起動中サーバへ投入（POST /projects）
```

HTTP API（Web UI = komadori の接続先。Phase 2）:

```
POST /projects            {project, live?, workers?}   → DAGを起動（202・非同期）
GET  /projects/<name>          ジョブ状態スナップショット（by_status・原価）
GET  /projects/<name>/events   SSEで進捗を購読（run.start / job / run.end）
GET  /projects/<name>/cost     生成原価（USD/¥/クレジット）
GET  /health
```

```
cm serve --port 8799 &
cm submit mirai-koji --port 8799
curl -N http://127.0.0.1:8799/projects/mirai-koji/events   # 進捗をライブ購読
```

次（Phase 2）: komadori のウィザード選択 → project.yaml 生成 → `POST /projects`、
ワークスペースが `/events` を購読してジョブ進捗・生成物・原価をライブ表示。
