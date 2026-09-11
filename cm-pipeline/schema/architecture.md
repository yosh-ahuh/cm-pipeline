# システムアーキテクチャ — コマドリ

実装に着手する前に確定させる土台。すべてのコードはこの設計に従う。

## 中心の洞察

パイプラインの本質は **「時間のかかる・課金される・リトライ可能な非同期AIジョブの連鎖」**。
1本のCMは 20〜40個のAI呼び出し（スチル・一貫性・動画化・音声・音楽・検品）を経て、
Remotionで合成される。この性質が全アーキテクチャを規定する:

- 生成は数分かかる → **リクエスト応答でなく非同期ジョブ**（キュー+ワーカー+進捗通知）
- 各呼び出しは課金される → **コスト計上とクレジット台帳が第一級の関心事**
- 生成は失敗・破綻しうる → **リトライ、`.done`冪等マーカー、検品ゲート**（実証済み）
- モデルは世代交代する → **プロバイダを抽象化**し、配役表を「設定」にする

## レイヤー構成

```
┌─────────────────────────────────────────────────────────┐
│  Client (Web UI = komadori)                              │
│  ウィザード / 台本 / ワークスペース / 書き出し            │
│  → project spec を送信、ジョブ進捗を購読、承認・選択      │
└───────────────┬─────────────────────────────────────────┘
                │ project.yaml (JSON) / SSE・WebSocketで進捗
┌───────────────▼─────────────────────────────────────────┐
│  API / Orchestrator                                      │
│  ・project を受理し検証（schema）                          │
│  ・カット表を展開してジョブDAGを生成                       │
│  ・クレジット残高チェック → ジョブ投入                     │
│  ・状態を集約して Client へ配信                            │
└───────────────┬─────────────────────────────────────────┘
                │ enqueue
┌───────────────▼─────────────────────────────────────────┐
│  Job Workers  （= cm CLI のロジックを再利用）              │
│  stills → review → animate → audio → build               │
│  各ステージ = 独立ジョブ（リトライ / .done / コスト記録）  │
└──────┬──────────────────────┬───────────────────┬────────┘
       │                      │                   │
┌──────▼───────┐   ┌──────────▼────────┐   ┌──────▼─────────┐
│ Model Adapter│   │ 検品 (Vision LLM) │   │ Render (Remotion)│
│ 層（下記）    │   │ quality-rules照合 │   │ 形式別mp4書き出し │
└──────┬───────┘   └───────────────────┘   └────────────────┘
       │ 抽象インターフェース
┌──────▼───────────────────────────────────────────────────┐
│  Providers: fal.ai (Imagen4 / nano-banana / Kling / Veo / │
│  MiniMax / Lyria / ElevenLabs) … 将来 別プロバイダ差替可   │
└──────────────────────────────────────────────────────────┘

  Storage: 入力素材 / 生成物（スチル・クリップ・音声）/ 書き出しmp4
           = オブジェクトストレージ + CDN。project状態 = DB(JSON)
```

## モデル抽象化層（#2の要）

fal依存を断ち切り、配役表を設定にするためのインターフェース。
今日の `gen_*.py` の呼び出しを、この抽象の背後に隠す。

```
interface ImageGen        { generate(prompt, size) -> Still }
interface ConsistencyEdit { edit(refImage, prompt) -> Still }        # nano-banana
interface Video           { animate(still, prompt, opts) -> Clip }   # Kling / Veo
interface TTS             { speak(text, voice, speed) -> Audio }
interface Music           { compose(mood, seconds) -> Audio }
interface SFX             { effect(desc) -> Audio }
interface VisionReview    { check(frame, checklist) -> Verdict[] }
```

- 各実装は fal のエンドポイントを1つラップするだけ（薄いアダプタ）。
- **配役表 `model-casting.yaml` が「どの実装を使うか」を決める設定**になる。
  例: `Video.animate` は cut.motion.model が veo なら VeoAdapter、kling なら KlingAdapter。
- モデル追加・差し替えは「アダプタ追加 + 配役表1行」で完結（コード改変なし）。

## データモデル（#3）

```
Org ── Users
 └─ Project ── Cuts ── Generations（version付き: still/clip/audio）
      │         └─ Assets（ユーザーアップロード素材）
      ├─ Renders（形式 × パターン の mp4）
      └─ project.yaml（JSON列 = 単一の真実。schema準拠）

CreditLedger  ── 各 Generation の実コストを記録 → 残高
Job           ── stage / status / cost / retries / .done
```

- **project.yaml が単一の真実**。DBのJSON列に持ち、UIの選択がこれを生成/更新。
- 生成物はオブジェクトストレージに `project/cut/version.ext` で保存（`.done`相当）。
- クレジット台帳は各モデル呼び出しの実コストを積む → UIの「クレジット残」に反映。

## 実装をブロックする決定事項（= 先に解くべきこと）

| # | 決定事項 | 既存資産からの出発点 |
|---|---|---|
| 1 | 非同期ジョブ基盤（キュー/ワーカー） | `gen_*.py` の逐次実行 → ワーカー化 |
| 2 | モデルアダプタのインターフェース | 各 `gen_*.py` の fal 呼び出しを1関数=1アダプタに |
| 3 | project.yaml ⇄ DB（JSON列）+ UIとの対応 | `projects/mirai-koji/project.yaml` が雛形 |
| 4 | コスト計上 → クレジット換算 | Veo $3-4/本、Kling $0.35、スチル数円 の実測値 |
| 5 | 検品ゲートの自動化 | `quality-rules.md` を Vision LLM プロンプト化 |
| 6 | レンダリング方式 | ローカル Remotion → Remotion Lambda / サーバ |

## 段階的実装の順序（既存資産を活かす）

```
Phase 1a: cm CLI = Job Workers のロジックを確立
  ・model-adapter 層を実装（fal を薄くラップ）
  ・cm stills / review / animate / audio / build を project.yaml 駆動に
  ・.done 冪等・コストログ・検品ゲートを内蔵
  → 2案件目を半日で回せる（Phase 1完了条件）

Phase 1b: Orchestrator で CLI を非同期ジョブ化
  ・キュー + ワーカー、進捗をSSEで配信
  ・project.yaml を DB(JSON)へ、クレジット台帳を追加

Phase 2: Web UI (komadori) を API に接続
  ・ウィザードの選択 → project.yaml 生成
  ・ワークスペースがジョブ進捗・生成物・原価をライブ表示
```

CLI（Phase 1a）が Web アプリのバックエンド・エンジンにそのまま昇格する一本道。
フロント（komadori.html）は既に見える形にあり、API を後から挿す。
