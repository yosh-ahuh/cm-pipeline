# モノレポ → 正本 `yosh-ahuh/spot` への移植一覧（2026-10-10）

対象: モノレポ `yosh-ahuh/cm-pipeline`（master）で 2026-10-06〜10-10 に入れたアプリ・ワーカー・パイプラインの変更。
正本 `yosh-ahuh/spot`（main、`/Users/yosh/work/spot-app`、`index.html`＋`js/{data,ui,i18n,auth}.js` に分割済み）へ**機能単位で再実装**する。
機械的なマージは不可（構造が違う）。移植と `railway up` は実装 (fork 2) が担当、UI/UX 側は本書の提供と移植後の end-to-end 立ち会い。

- コミット範囲: `ec90823..ed92194`（`spot-app/`・`cm-pipeline/`・直下 `Dockerfile` / `railway.toml` / `.railwayignore`）
- 変更量: 25 ファイル、+3,175 / −186
- 検証記録: `docs/implementation-scope-mockB.md` §5、メモリ `worker-live-run-2026-10`

---

## 0. ⚠ 先に直すべきこと: 本番 DB で正本側の権限設計を上書きしてしまった

モノレポ側の実環境通し（10/7）で「projects に INSERT できない」「spend_credits が permission denied」を GRANT 欠落と誤認し、
`028_grant_projects.sql` と `029_grant_credit_rpcs.sql` を本番に適用した。実際はこれらは正本側の **意図した制限** だった:

| 正本の migration | 意図 | モノレポが戻してしまった内容 |
|---|---|---|
| `028_column_privileges.sql` | projects の INSERT/UPDATE を **列単位**に限定（`name, product, spec, org_id, brand_id, collection_id`[, approved]） | `grant select, insert, update, delete on public.projects to authenticated`（テーブル単位に復活） |
| `026_server_generation.sql` | 生成開始を `start_generation(uuid, boolean)` RPC に一本化、`spend_credits` / `log_cost` の EXECUTE を authenticated から剥奪 | `grant execute on spend_credits / log_cost to authenticated`（クライアントから消費できる状態に戻った） |

**対応**: `spot-app/supabase/migrations/031_restore_column_privileges.sql`（モノレポ側に用意。内容は正本 026/028 の該当行の再適用）を本番で実行して元に戻す。
モノレポ版アプリが projects.insert で `status: 'draft'` を送っていたのが「permission denied」の真因（列権限に `status` が無い）。正本側アプリはこの列を送らないので問題ない。
モノレポ版アプリの `onGenerate`（クライアントから `spend_credits` → jobs insert）は正本の `start_generation` に置き換える（§4）。

---

## 1. コミット一覧（phase 順）

| phase | commit | 内容 |
|---|---|---|
| P1 | `919ea83` `b2c30ca` `cf9ccc0` | 7 ステップの制作フロー（流す場所／目的／届ける相手／伝えたいこと／台本を確認／素材をアップ／初稿を確認）、上部固定の横一列ステッパー、AI おすすめ構成は右パネル、CM 名入力 |
| P2 | `5362cb9` | ブランド取り込み UI（入力／読み込み中／確認カード）＋ `027_brand_intake.sql` |
| P4 | `7c39cdf` | 台本ステージ（`jobs.stage='script'`、`worker/script_gen.py`） |
| P3 | `5f52bd7` | ブランド取り込みワーカー（`worker/brand_ingest.py`） |
| P5 | `68db474` | ブランドの見た目・言葉を生成へ注入（`spec.brand`、`merge_brand`、`reference_stills`、`compose.still_prompt` の差し色） |
| 実環境通しの修正 | `361cf49` `f6e8109` `50bfa58` `77877b2` `7bcbe5f` `c00eccf` `da1ddc9` | robots UA、openConfirm、検品実装、写像修正、尺予算 27 秒、Resend UA、書き出し形式キー、依存失敗の連鎖、初稿の実動画、Veo クリップ長、色の彩度順、再開カード |
| UX 確定 | `6761597` | 届ける相手 3 つまで、持ち込み台本の規約・尺目安、モバイル「その他」メニュー |
| 品質 | `f29b48d` `dfc2bd2` | 実写の被写体・動き指示の制約、ナレーション（秒−1）×5 文字、Remotion の速度補完、**クリップ検品＋スチルへのフォールバック** |
| 常駐 | `048b92e` `2e7a763` | モノレポ用 Dockerfile / entrypoint / railway.toml / .railwayignore（正本は独自の Dockerfile があるので**移植不要**。§6） |
| 体裁 | `ed92194` | 「プロトタイプ」フッター撤去 |

---

## 2. cm-pipeline 側（正本の Dockerfile は `yosh-ahuh/cm-pipeline` master を clone するので **自動的に取り込まれる**）

| ファイル | 変更 | 正本ワーカーからの呼び出しに必要なこと |
|---|---|---|
| `cm/adapters/review_llm.py` | `VisionReview.check()` を Claude（画像入力＋JSON schema）で実装。`check_clip(still, frames)` を追加（元スチル＋3 フレーム、6 項目）。`ANTHROPIC_API_KEY` 無しは通過。MIME は中身で判定 | ワーカー env に `ANTHROPIC_API_KEY`（任意 `SPOT_REVIEW_MODEL`） |
| `cm/project.py` | `_parse_checklist`: quality-rules.md の A 表＋日本考証＋D3/D4 のみ（開発メモの箇条書きを拾うバグ修正） | なし |
| `cm/pipeline.py` | `review_clip_one` / `retake_clip` / `reject_clip`、`_clip_duration`（Veo 4s/6s/8s、Kling 5/10）、`_motion_prompt` の既定に「手は動かさない・物が増えない」 | animate 後に `review_clip_one` → NG で `retake_clip`→再 animate → 再 NG で `reject_clip`（§3-5） |
| `cm/remotion_props.py` | クリップがカットより短いとき `rate` を 0.75〜1.0 に（`_fill_rate`、ffprobe） | なし |
| `cm/compose.py` | `still_prompt` に `brand.colors.primary` の差し色（実写のみ、`brand.color_hint=false` で無効） | `spec.brand` が project.yaml に写っていること（§3-3） |
| `cm/prices.py` | `vision-review-clip: 0.02` | なし |
| `cm/adapters/fal_video.py` | `VEO_NEGATIVE` に new objects / page turning / pasting / writing / extra hands | なし |

---

## 3. ワーカー側（`spot-app/worker/` → 正本 `worker/`）

### 3-1. 新規ファイル（そのまま持ち込める）
- `script_gen.py`（328 行）: 台本生成。`run(spec, profile, live) -> (patch, detail)`。Claude（`claude-opus-5-5`、`client.beta.messages.create(... betas=["server-side-fallback-2026-07-01"], fallbacks="default", output_config={"format":{"type":"json_schema",...}})`、TypeError で `client.messages.create` にフォールバック）。キー無し／失敗時はテンプレート台本。
  - 秒数配分: 合計 30（YouTube のみ）／27（Reels・Shorts・SNS タイムラインを含む）／15（Reels のみ）。実写カットは 8 秒上限（超過は UI/CTA へ）。
  - 出力 cut: `narration`, `narration_tts`（読み方適用）, `caption`（≤18 字）, `subject`（≤40 字、動きの少ない場面）, `motion_en`（英語 ≤12 語）, `secs`, `assets_required`（ui / logo / none）, `narration_id`。`script = {source:'ai'|'user'|'template', model, pronunciation, voice, warnings}`。
  - 持ち込み台本（`spec.script.source==='user'`）は文章を変えず分割だけ。
- `brand_ingest.py`（498 行）: `tick_brands(sb, only_brand, live)`。`brand_sources.status='pending'` を brand ごとに処理: URL（robots.txt を**自前 UA で**取得、4xx＝許可、15 秒・2 MB）／text／file（PDF=pypdf、PPTX=zip XML、画像）→ `extract_*` → Claude で profile（キー無しはヒューリスティック、confidence low）→ `merge_profile`（`confirmed_at` 済みの項目は上書きしない）→ `brands.profile` 更新 → sources を `done`。ロゴ候補は `<org>/brand/<brand>/logo.<ext>` に保存。
- `requirements.txt`: `anthropic>=1.11`, `pypdf>=6`, `pyyaml`。

### 3-2. `worker.py` の変更点（正本 worker.py に相当箇所を入れる）
1. `JOB_USD["script"]=0.02`。`tick()` の先頭で `brand_ingest.tick_brands(sb, only_brand, live)`。CLI `--brand <id>`。
2. **script ステージ**: `run_script_stage(sb, project_id, live)` が `projects.spec` と `brands.profile` を読み、`script_gen.run` の結果で `spec.cuts` / `spec.script` を更新。**`LiveRunner`（project.yaml 生成）は script の後、最初の生成ジョブで遅延生成**（`ensure_runner`）。project の `done` 判定は「script 以外のジョブが 1 つ以上あり全部 done/skipped」。
3. `spec_to_project`: cuts の `narration`/`narration_tts` → `script.narration[{id,text,display}]`、`caption` → telop（UI カットは caption のみ、telop は明示時だけ）、`secs*30` → `dur`、`subject` → `still.subject`、`motion_en` → `motion.prompt`（＋「手は動かさない」定型）、CTA の `button` は caption 優先・`search` はブランド名、`script.userScript` は落とす。
4. `merge_brand(sb, spec, brand_id)`: 生成直前に `brands.assets`（logo/app_icon/colors）と `brands.profile`（summary.one_liner → tagline、voice.terms → pronunciation、visual/voice）で `spec.brand` を補完。`reference_stills(sb, brand_id, exclude_project, limit=3)`: `projects.approved=true` の同ブランド案件の `generations(kind='still')` を `brand.references` に同梱（`localize_assets` でダウンロード）。
5. **検品フロー**（LiveRunner.run）:
   - `review`: `review_one(retake=True)` → NG なら `still_one` → `review_one(retake=False)` → 2 回目も NG は**止めず**に `<cid>.review.json` を `pass=true, needs_check=true` にして進める。作り直したスチルは Storage に再アップロード。
   - `animate`: `animate_one` → `review_clip_one` → NG なら `retake_clip`＋再 `animate_one`＋再 `review_clip_one` → 2 回目も NG なら `reject_clip`（Remotion はスチルの Ken Burns に自動フォールバック）。結果は `self.notes` → `jobs.detail`（`clip_fallback` / `needs_check`）。
   - `audio`: ledger から音声ファイルごとの model/usd を引いて generations に記録。
6. **依存失敗の連鎖**: `process_project` の各 tick で、deps に failed を含む pending ジョブを `failed`（detail `blocked: <dep> failed`）に倒す。連鎖は同 tick 内で伝播。見出しログはジョブが動くときだけ。
7. 完了メール: Resend への `User-Agent` 付与（Python 既定 UA は Cloudflare 1010 で 403）。
8. `.env.example`: `ANTHROPIC_API_KEY`, `SPOT_SCRIPT_MODEL`, `SPOT_REVIEW_MODEL`。

### 3-3. ジョブ DAG と正本 `start_generation` の統合（要設計判断）
モノレポ版はクライアントが「案件作成直後に `jobs(stage='script', cut=null, deps=[])` を insert」し、生成時は「全生成ジョブの deps に `'script'` を先頭追加（script が done でなければ）」していた。
正本は `start_generation` RPC がサーバで jobs を作るので、**RPC 側で script ジョブを先頭に作り、他ジョブの deps に `script` を入れる**のが筋。案件作成時（台本画面に入る時点）に script ジョブだけ先に作るには、
(a) `start_script(p_project)` のような小さな RPC を追加する（クレジット消費なし、1 案件 1 回）か、(b) `start_generation` に `p_stage='script'` を足す。UI は Realtime で `jobs`（stage='script'）を購読し、done で `projects.spec.cuts` を読み直す。

### 3-4. ジョブ `detail` の形
- 失敗: `{"error": "..."}`、依存失敗: `{"error": "blocked: review:cut1 failed (...)", "blocked_by": ["review:cut1"]}`
- 完了時の注記: `{"needs_check": {"stage":"still","ng":[...]}}` / `{"clip_fallback": {"cut":"cut2","ng":[...],"reasons":[...]}}`

### 3-5. 実測値（10/7 の通し）
- 台本 $0.02、スチル $0.05/枚、スチル検品 $0.05/回、クリップ検品 $0.02/回、Veo 3.1 6 秒 $3.5/本（8 秒は未計測）、音声 $0.14、合計 ≒ $7.5 / 本（4 カット・実写 2）。
- Remotion はローカルで 9 本 ≒ 1 時間。コンテナでの実測は未。

---

## 4. アプリ側（モノレポ `index.html` → 正本 `index.html`＋`js/*.js`）

### 4-1. データ契約（`projects.spec`）
```
meta:       { name, goal }                         # name = CM 名（UI 入力、既定はブランド名＋筆頭目的＋日付）
selections: { media[], goals[], targets[], target(=targets[0]), industry, angle, tone }
output:     { formats[] }
delivery:   { platforms[] }
compliance: { ai_disclosure, content_credentials, likeness_check, real_ui_only }
brand:      { name, logo, app_icon, colors{primary,accent,dark,palette[]}, tagline, pronunciation{}, imagery, register, avoid[] }   # brandSnapshot()（primary は彩度優先）
cuts[]:     { id, role, type(live-action|ui|cta|graphic), secs, narration, narration_tts, narration_id, caption, subject, motion_en, assets_required, assets[] }
script:     { source('ai'|'user'|'template'), model, userScript, pronunciation, voice, warnings }
audio:      { reference: { youtube | file } }
```
`brands.profile`: `{ summary{one_liner,audience,values[]}, visual{logo,colors[],imagery,logo_candidates[]}, voice{register,terms[{text,reading}],avoid[]}, defaults{industry,target,tone}, screens[], custom[{label,value}], confidence{}, learned_from[], learned_at, model, confirmed_at }`
`brand_sources`: `{ brand_id, org_id, kind(url|text|file), url, text, storage_path, file_name, status(pending|running|done|failed), step(fetch|extract|extracted|summarize|done), error, extracted }`

### 4-2. 画面・挙動（移植する機能の要点）
1. **7 ステップのフロー**: 共通 `FLOW_STEPS` と上部固定 `.flow-bar`（ウィザード／台本／素材／初稿の 4 画面で共有、`flowJump(i)`）。ウィザードは 4 ステップ（流す場所＝書き出し形式／目的／届ける相手／伝えたいこと＋業種サブセクション）。目的・相手は複数選択＋自由入力チップ。**届ける相手は 3 つまで**（4 つ目はトースト）。CM 名入力。
2. **ブランド取り込み**（`view-brand-intake` / `view-brand-card`）: URL 複数・自由記述・ファイル複数（PDF/PPTX/画像、Storage に保存）・3 問フォールバック。開始で `brand_sources` を pending に、Realtime で進捗、90 秒で「答えだけで進む」。確認カードは全項目編集可、保存で `profile.confirmed_at`。ホームの CTA、「新しく作る」初回ゲート（`spot-intake-skip:<brandId>` でスキップ記憶）、設定のブランドカード、ウィザード既定値の profile フォールバック。
3. **台本画面**: 状態バナー（pending/running/slow(60 秒)/failed/done）。Realtime で script ジョブを監視し done で `spec.cuts` を再読込。持ち込み台本: 「カット1:」「#1」規約と空行分割（最大 8）、入力中の尺目安（日本語 5 文字/秒・英語 15 文字/秒、32 秒超は警告）、反映で `script.source='user'`。
4. **素材画面**（`view-assets`）: 台本の `assets_required` から必要素材だけを列挙（UI スクショ＝必須、ロゴ／アイコン＝任意）、音楽参考（MP3 or YouTube URL）。必須が揃うまでゲート。アップロード先 `<org>/<project>/ui/<cut>/<ts>_<name>` を `cuts[].assets` に記録。「初稿をつくる」は確認ダイアログ（1 クレジット）→ 生成開始（正本では `start_generation`）。
5. **初稿画面**: 完成レンダー（A・横）があれば `<video>` で実再生。ジョブ失敗の理由（`detail.error`）表示。
6. **書き出し画面**: `renders.format` は配信先名（youtube / reels_shorts / timeline）なので形式キー（wide / vertical / square）に正規化して紐づけ（これが無いと 9 本あっても「プレビュー」表示のまま）。
7. **ホーム**: 「続きから」カード（台本未着＝Step 5、素材アップ済み＝Step 6 で素材画面へ、生成中＝Step 6、完成＝Step 7）、「目的から作る」。
8. **モバイル**: ボトムナビ（ホーム／作る／マイCM／その他）。「その他」でアカウントメニューを開き、モバイル限定群（メディア・コレクション・チーム・請求）を表示。
9. **その他**: `openConfirm` を window に公開（正本は `b700d00` で対応済み）、「プロトタイプ」フッター撤去、ブランド色は彩度優先、i18n 辞書に新規文言（JA→EN）。

### 4-3. 正本側で既に別実装になっているもの（移植時に合わせる）
- 生成開始: `start_generation` RPC（クライアントの `spend_credits` は使わない）。
- `openConfirm` 公開済み（`b700d00`）。
- 列権限（028）: projects.insert に `status` を含めない。

---

## 5. DB（本番 mmnpfxrodsurxpeyaaaf は両系列の migration が混在）

| 系列 | 番号 | 状態 |
|---|---|---|
| モノレポ | `023_brands_multi` `024_brand_members` `025_share_notify` `026_owner_check_hotfix` `027_brand_intake` | 適用済み（brands 複数・ブランド範囲・共有リンク・**brand_sources**） |
| モノレポ | `028_grant_projects` `029_grant_credit_rpcs` | 適用済み → **031 で戻す（§0）** |
| モノレポ | `030_signup_attribution` | 適用済み（utm） |
| 正本 | `023_project_poster` … `030_server_compliance` | 適用済み（実装側） |

正本リポジトリに取り込む際、モノレポの `027_brand_intake.sql` は番号が衝突するので `031`〜に振り直す（内容: `brands.profile jsonb`、`brand_sources` テーブル＋`touch_updated_at`/`fill_brand_source_org` トリガ、RLS は `is_member/can_write/brand_visible`、Realtime publication 追加、`grant select, insert, update, delete on brand_sources to authenticated` ← 列権限方針に合わせて列単位に絞ってよい）。本番には適用済みなので再実行は冪等であること。

---

## 6. 常駐（Railway）
- 正本の Dockerfile は `python:3.12-slim`＋ffmpeg＋cm-pipeline clone。**Remotion（Node＋Chrome Headless Shell）と日本語フォントが無い**ので build ステージがコンテナで動かない可能性が高い。モノレポ版 Dockerfile（`node:20-bookworm-slim`、`npx remotion browser ensure`、`fonts-noto-cjk`、`ad-prototype` 同梱）を参考に、正本側で ad-prototype をどう持つか決める（clone or サブモジュール）。
- `WORKER_MODE=live` 変数はこちらが追加したもの。正本 entrypoint が `WORKER_LIVE=1` を見るなら不要。
- ワーカーは 1 台だけ（ローカル同時起動不可）。

---

## 7. 移植後の end-to-end 確認（UI/UX 側が立ち会う）
1. ブランド取り込み: URL 1 件＋自由記述 → `brand_sources` が pending→running(step)→done、`brands.profile` に summary/visual/voice、カード保存で `confirmed_at`。
2. 案件作成 → script ジョブ → `spec.cuts[].narration/caption/assets_required/secs/subject/motion_en` が入り、台本画面が Realtime で更新。
3. 素材 1 枚 → 生成開始（`start_generation`）→ still → review（NG なら作り直し）→ animate（8s）→ clip review（NG なら作り直し／フォールバック）→ audio → build → renders 9 本 → `projects.status='done'` → 完了メール。
4. 書き出し画面で「書き出し完了・9 本」、DL リンクの署名 URL が mp4 を返す。
5. 失敗系: review を強制 NG にして animate/build が `blocked:` で failed になること。
