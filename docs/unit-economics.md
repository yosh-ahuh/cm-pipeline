# ユニットエコノミクス整理（生成コスト vs プラン価格）

プランのスポット数・価格戦略の土台。**実コスト構造**と**採算**を整理する。数値はコード由来の概算＋実データで調整。

## 1. 1CMの原価構造
- ジョブ単価（`JOB_USD` / worker）：still $0.05 / review $0.01 / **animate（Veo動画）$3.50** / audio $0.28 / build $0。
- **パターンA/B/C × 3フォーマット（＝9ファイル）は Remotion の再コンポジット（build＝$0）**。**Veoアニメは1回だけ**（音楽/色/テロップだけ差し替え）。
- **1CMのコスト ≒（実写カット数 × $3.56）＋ audio $0.28**。
  - 実写3カット → **約 $11（¥1,650）**／実写5カット（現デモ）→ **約 $18（¥2,700）**。
- ⇒ **原価の支配項は「実写(Veo)カット数」**。ここが採算の最大変数。

## 2. クレジット/課金モデル（現状）
- `credit_costs`：generate=1 / rerender_pattern=0.25 / regenerate_shot=0.1。
- `spend_credits` は**生成時に1クレジット**消費（`onGenerate`）。1クレジット＝1CM＝9ファイル。
- extra_spot_usd（追加1本の単価）：free/starter/team $19 / business $15 / enterprise $12。
- **実コストは per-job で記録**（`log_cost`／worker が実 usd を jobs/generations に計上）＝**実データで per-CM/編集コストを算出可能**。

## 3. ⚠ 矛盾・リスク
- **編集の「無制限」矛盾**：UIは「この案件・修正は無制限」。だが `credit_costs` は編集に課金（regenerate_shot=0.1＝再Veo）。**カット作り直し(regenerate_shot)は再アニメ＝$3.56/回**。無制限にすると**編集がコストのブラックホール**。
- **Enterprise「無制限スポット＋無制限編集」＝上限なきCOGS**。fair-use上限/カスタム契約が必須。
- **Freeは1本でも原価¥1,650〜2,700/ユーザー/月**の獲得コスト。

## 4. 採算（粗利＝価格 − スポット数×原価）
実写3カット＝¥1,650/CM で試算：
| プラン | 価格/月 | スポット | COGS(¥1,650/本) | 粗利 | 粗利率 |
|---|---|---|---|---|---|
| Starter | ¥14,800 | 6 | ¥9,900 | ¥4,900 | ~33% |
| Team | ¥59,800 | 25 | ¥41,250 | ¥18,550 | ~31% |
| Business | ¥178,000 | 80 | ¥132,000 | ¥46,000 | ~26% |

実写5カット＝¥2,700/CM だと：Starter粗利 ¥-1,400（**赤字**）／Team ¥-8,000（**赤字**）／Business ¥-38,000（**赤字**）。
⇒ **実写カット数が3→5になるだけで黒字↔赤字が反転**。インフラ/サポート/決済手数料はこの上に乗る。

## 5. スポット戦略（Yoshの懸念＝Team25本は3ブランドに窮屈）
- **スポットは原価の直接ドライバ**。**ブランド単位で配ると 3ブランド×25＝75本＝COGS3倍**で確実に赤字。→ **スポットはアカウント全体の共有プールに据える（＝原価キャップ）**のが正解。窮屈さは「原価上限」の裏返し。
- 「もっと本数を」と「粗利確保」は両立しない。動かせるレバーは3つ：
  1. **1CMの原価を下げる**：実写(Veo)カットを減らす／コード描画(UI・図版=$0)比率を上げる／より安い動画モデル。← **最優先・最も効く**。
  2. **価格を上げる**。
  3. **追加スポット（top-up）を主導線に**：基本プールは薄め＋足りなければ都度購入（extra_spot は既存）。
- 目安式：`スポット数 ≒ 価格 ×(1−目標粗利率) ÷ 原価/CM`。例）Team ¥59,800・目標粗利50%・¥1,650/CM → **約18本**（現25本は粗利31%想定）。

## 6. 提案（意思決定用）
- **A. 編集課金の是正**：軽い編集（パターン差し替え/色/テロップ＝再コンポジットのみ＝ほぼ$0）は無制限でOK。**カット作り直し（再Veo）は credit_costs 通り課金**（0.1クレジット）。UIの「無制限」を「軽い修正は無制限／作り直しはクレジット」に正直化。
- **B. 原価/CMを下げる設計**：実写カット数の既定を抑える・コード描画比率UP・動画モデルの単価見直し。**採算の主戦場はここ**。
- **C. スポットはアカウント共有プール維持**＋top-up主導線。ブランド単位配布はしない。
- **D. Enterprise は無制限にfair-use上限**（カスタム契約）。
- **E. 実データで確定**：`log_cost` の実 usd から「実写カット数分布・実 per-CM原価・編集頻度」を集計し、スポット数と価格を確定。**まず現行 jobs/generations の usd を集計するクエリ/ダッシュボードを用意**。

## 6b. 決定（2026-09-22）と含意
- **目標粗利率＝近100%**。**品質（実写カット数・モデル）は落とさない**＝**原価は固定**。**編集は「軽い修正は無制限／作り直し(再Veo)はクレジット」**でOK。
- ⇒ 原価を下げられない以上、**近100%粗利は「価格＝価値基準」への転換でしか達成できない**。1CMの実効単価を**原価の数倍〜10倍**に。

### ⚠ 現状は「原価基準」＝実質ゼロ粗利
- プランの実効 ¥/CM：Starter ¥2,467・Team ¥2,392・Business ¥2,225。**原価 ¥1,650〜2,700 とほぼ同額**。
- 追加スポット：$12-19（¥1,800-2,850）＝**これも原価並み**。→ **今の値付けは全面的に粗利ほぼゼロ**。

### 価値基準リプライシング（近100%粗利）
- **アンカー＝代理店の代替（1本¥300k+）**。¥15,000〜30,000/CM でも**代理店比90%超の割引**かつ**粗利85〜95%**（原価¥1,650〜2,700）。
- 目安：`粗利90% → 実効¥/CM ＝ 原価 ÷ 0.1 ＝ ¥16,500〜27,000`。
- **含意：本数は絞られる**（近100%粗利×固定原価×現行価格では、含める本数はごく少数）。＝**プレミアム路線**（少数の高価値CM）。「たくさん作る」路線とは両立しない。

### サンプル・リプライシング（粗利~85%・原価¥2,500/CM 想定・要調整）
| プラン | 月額 | 含むCM/月 | 実効¥/CM | 追加CM単価 | ブランド | 席 |
|---|---|---|---|---|---|---|
| Free | ¥0 | 1（お試し） | — | — | 1 | 1 |
| Starter | ¥16,500 | 1 | ¥16,500(≈85%) | ¥16,500 | 1 | 2 |
| Team | ¥59,800 | 4 | ¥14,950(≈83%) | ¥16,500 | 3 | 5 |
| Business | ¥178,000 | 12 | ¥14,833(≈83%) | ¥16,500 | 10 | ∞ |
| Enterprise | 個別 | 個別 | 個別 | 個別 | ∞ | ∞ |
> 数字は例。**目標粗利率と原価/CMの実測**で確定。追加CM（top-up）を**価値価格**にするのが粗利の要（現$12-19→¥16,500級へ）。

### 編集課金（決定を反映）
- **軽い修正（パターン差し替え/色/テロップ＝再コンポジット＝ほぼ$0）＝無制限・無料**。
- **カット作り直し（再Veo＝$3.56）＝クレジット消費**（`credit_costs.regenerate_shot=0.1` を実際に `spend_credits`）。UIの「修正は無制限」を「軽い修正は無制限／作り直しはクレジット」に正直化。
- ＝編集でも原価分はクレジットで回収＝粗利を守る。

## 7. 要ユーザー判断
1. **目標粗利率**（例50%/60%）＝スポット数と価格の基準。
2. **編集課金**：Aの「軽い修正無制限／作り直しは課金」で良いか。
3. **原価低減の方針**（実写カット既定を下げる／モデル見直し）に踏み込むか。
4. **Enterprise の fair-use 上限**の考え方。

関連: [[brand-plan-limits-proposal]], [[consistency-audit-2026-09]]（生成の本番稼働・課金導線）。

## 8. 実コスト集計クエリ（後で実行する）
> Supabase MCP 直アクセスは保留中（下記TODO）。当面は SQL Editor で Run するか、legacy PAT 設定後に Claude が実行。$1≈¥150 換算。

### A. データ有無
```sql
select
  (select count(*) from public.projects) as projects,
  (select count(*) from public.jobs where usd > 0) as job_cost_rows,
  (select count(*) from public.credit_ledger where usd > 0) as ledger_cost_rows,
  round((select coalesce(sum(usd),0) from public.jobs)::numeric,2) as jobs_usd_total;
```
### B. 1CMあたり原価（最重要）
```sql
with pp as (select project_id, sum(usd) usd, count(*) filter (where stage='animate') live_cuts
            from public.jobs group by project_id)
select count(*) cms, round(avg(usd)::numeric,2) avg_usd,
       round((percentile_cont(0.5) within group (order by usd))::numeric,2) median_usd,
       round(avg(usd)*150) avg_jpy, round(avg(live_cuts)::numeric,1) avg_live_cuts
from pp;
```
### C. ステージ別内訳
```sql
select stage, count(*) n, round(sum(usd)::numeric,2) usd,
       round((100*sum(usd)/nullif((select sum(usd) from public.jobs),0))::numeric,1) pct
from public.jobs group by stage order by usd desc;
```
### D. 実写(Veo)カット数の分布
```sql
with pc as (select project_id, count(*) filter (where stage='animate') live_cuts
            from public.jobs group by project_id)
select live_cuts, count(*) cms from pc group by live_cuts order by live_cuts;
```

## 9. TODO：Supabase 直アクセス（Claude が実行できるように）
- 現状：MCP server 追加済みだが、発行された**粒度別トークンが Unauthorized で拒否**（Management API / MCP 双方）。原因＝Database権限未付与 or 粒度別トークン非対応。
- 直し方：Supabase の token 生成画面「**Create legacy token**」でフルアクセスPATを作成 →
  `claude mcp remove supabase` → `claude mcp add supabase -e SUPABASE_ACCESS_TOKEN=<sbp_...> -- npx -y @supabase/mcp-server-supabase@latest --project-ref=mmnpfxrodsurxpeyaaaf`
- 有効後：Claude が上記A〜Dを実行して**実額でプラン表を確定**、以降のマイグレーションも直接適用可能（セッション再読込不要＝ワンショットMCPで叩ける）。
