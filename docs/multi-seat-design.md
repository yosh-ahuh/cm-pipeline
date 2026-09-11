# SPOT マルチシート（組織・招待・席数）設計 + アカウント共有の悪用対策

対象: spot-app（Supabase Postgres + RLS）。現状は全データが `owner = auth.uid()` 個人所有。
本書は「組織（Org）を単位にした複数人利用」への移行設計と、**同一アカウント共有（1ログインを複数人で使い回す）**の悪用対策をまとめる。

ステータス: **設計フェーズ（未実装）**。実装は Phase B 以降（本書末尾のフェーズ分割）。

---

## 0. 最重要の前提 —「本当に守るべきコスト」を先に定義する

SPOT で費用が出る資源は **動画生成（fal 実費）だけ**であり、それは **クレジット（credits）で従量計測**される。

したがって設計原則は：

> **クレジット残高を「組織」単位のプールにすれば、何人が同じログインを共有しても、生成できる総量＝支払った分を超えられない。**

つまり **アカウント共有で起きる実害は「暴走する生成コスト」ではなく、次の2つに限定される**：

1. **席課金の取りこぼし（レベニューリーク）** — 本来 5 席買うべきチームが 1 ログインを共有して席代を払わない。
2. **アトリビューションの喪失** — 誰が作った/消費したかの監査ログが消え、権限管理・不正調査・サポートが効かなくなる。

この整理が対策の強度を決める。**生成コストは（プール化で）構造的に守られている**ので、正規ユーザーを傷つける強硬なロックは不要。狙いは「**共有する意味を無くす構造 + 穏当な抑止 + 検知して席購入に誘導**」。

---

## 1. データモデル

### 1.1 新規テーブル

```
organizations
  id                uuid pk
  name              text
  plan              text  references plans(id)   -- 課金主体はここに移す
  credits           numeric                        -- 残高もここ（個人 profiles から移設）
  credits_reset_at  timestamptz
  owner_user_id     uuid  references auth.users    -- 契約者（billing 責任者）
  created_at        timestamptz

org_members
  org_id   uuid  references organizations
  user_id  uuid  references auth.users
  role     text  check (role in ('owner','admin','editor','viewer'))
  added_at timestamptz
  primary key (org_id, user_id)

org_invites
  id          uuid pk
  org_id      uuid  references organizations
  email       text                     -- 招待先（正規化して小文字）
  role        text
  token       text unique              -- 招待リンク用（推測不能）
  invited_by  uuid
  expires_at  timestamptz              -- 例: 7日
  accepted_at timestamptz              -- null = 未受諾

brands            -- brands 上限の実効化（現状は spec 内の裸データで未計数）
  id       uuid pk
  org_id   uuid references organizations
  name     text
  assets   jsonb        -- app_icon / logo / colors 等
```

### 1.2 既存テーブルの変更

- `profiles`：**identity と個人設定のみ**にする（display_name, 個人環境設定）。`credits` / `plan` / `credits_reset_at` は **organizations に移設**（個人からは剥がす）。
- `projects / generations / jobs / renders / credit_ledger`：`owner uuid` に加え **`org_id uuid`** を持たせ、所有判定を org に切り替える。`projects` に `brand_id` を追加（brands 上限の実効化）。
- Storage パス規約：`<owner_id>/…` → **`<org_id>/<project_id>/<file>`**。

### 1.3 ロール（確定: 3段）

IT リテラシーが高くない利用者層のため**3段に単純化**（admin/editor は分けない）。

| role | 生成（credits消費） | メンバー管理 | 課金 | 閲覧 | 席数 |
|---|---|---|---|---|---|
| owner | ✓ | ✓ | ✓ | ✓ | 1席 |
| **member** | ✓ | — | — | ✓ | 1席 |
| **viewer** | — | — | — | ✓ | **カウント外（完全無料・無制限）** |

- member = 制作担当（クレジットを消費して生成できる）。メンバー招待/課金は owner のみ。
- **viewer は完全無料・無制限**に追加可能 → 「見せたいだけ」で 1 ログインを渡す動機を消す（共有悪用対策の要）。

---

## 2. RLS 方針

所有判定を「本人」から「その org のメンバー」へ。

```sql
-- ヘルパ（SECURITY DEFINER で再帰RLSを避ける）
create function public.is_member(p_org uuid) returns boolean ...
  -- exists(select 1 from org_members where org_id=p_org and user_id=auth.uid())
create function public.member_role(p_org uuid) returns text ...

-- 例: projects
create policy "member reads projects" on projects
  for select using (is_member(org_id));
create policy "editor writes projects" on projects
  for all using (member_role(org_id) in ('owner','admin','editor'))
     with check (member_role(org_id) in ('owner','admin','editor'));
```

- **viewer は select のみ**、editor 以上が insert/update/delete。
- `organizations.credits/plan` はクライアント直更新不可（既存 `protect_profile_fields` と同型のトリガで保護）。消費は RPC 経由（`spend_credits` を org 対応に改修）。
- Storage の RLS も `<org_id>/…` で member 判定に変更。

---

## 3. 席数（seats）の実効化

- 招待受諾は **SECURITY DEFINER の `accept_invite(token)` RPC** で行い、**その中で `count(org_members where role in ('owner','member')) < plans.seats`（0=無制限）を原子的にチェック**。UI 側チェックだけにしない（回避される）。
- 席超過時は「席を追加購入 / プラン変更」導線を返す。
- **viewer はカウント外（完全無料・無制限）**。owner/member のみが席を消費する。

---

## 4. アカウント共有（同一ログイン使い回し）の悪用対策 ★本題

「席を買わずに 1 アカウントを全員で共有」への多層防御。**§0 の通り生成コストは守られている**前提で、**穏当さ優先**で設計する。

### 層A: 構造で「共有する意味」を無くす（最優先・恒久対策）

1. **クレジットは org プール**：共有しても生成総量は増えない（＝計算資源の悪用は原理的に不可）。
2. **無料 viewer 席**：閲覧・確認目的の共有動機を消す。
3. **席の価値を“協業機能”に置く**：個人ドラフト、役割分担、**監査ログ（誰が何を生成したか）**、同時編集の安全性。これらは共有ログインでは得られない（共有すると誰の操作か分からず、事故・上書き・責任不在になる）。
4. **上位プランはドメインキャプチャ / SSO**：`@company.com` で入れば自分のメールで自動参加 → そもそも共有ログインにする理由が消える（Business+ 向け）。

### 層B: 検知（1ログイン＝複数人 のシグナル）

`login_events` テーブル（または Supabase の `auth.audit_log_entries` を集計）に記録し、org 単位でスコアリング：

- `user_id, ip, coarse_geo(市/国), asn, device_fp(UA+client_id), ts`

**信頼できる陽性シグナル**：
- **同時刻に地理的に離れた複数アクティブセッション**（例: 東京と福岡で同時にアクティブ）。← 最も確度が高い
- **ローリング30日での多デバイス数**が席数に対して過大。
- **24/7 稼働で人間的なアイドルが無い**（交代運用の兆候）。
- **新規デバイス出現の高頻度**。

**誤検知を避けるための注意（重要）**：
- **同一オフィスの NAT は全員が“1 IP”に見える** → これは共有を**隠す**方向。だから「同一都市内の IP 分散」ではなく「**離れた地理での同時アクティブ**」を主シグナルにする。
- 1人が「ノートPC＋スマホ＋自宅＋オフィス＋VPN」を使うのは正常 → **単発の impossible-travel では判定しない**。**持続的・同時・多地理**のみをフラグ。
- VPN / 出張の存在を前提に、閾値は**席数に応じた妥当なデバイス/地理バジェット**にする。

出力は「**org を要確認フラグに立てる**」まで。単一シグナルで自動制裁しない。

### 層C: 抑止・強制（段階的・誤検知に優しい順）

1. **ソフト（既定）**：アプリ内バナー＋owner へメール通知
   「今週 SPOT が N か所/N デバイスで利用されました。プランには X 席が含まれます。**メンバーを招待すると各自のログインで安全に使えます**」← 罰でなく**席購入へのコンバージョン**。
2. **新デバイス検証（確定: 全プラン）**：未知デバイスからの**初回ログイン時にメール OTP のステップアップ**。カジュアルなパスワード共有を確実に抑止（共有相手はメール受信箱を持っていないと入れない）。標準的なセキュリティでもあるため Free 含む全プランで有効化。毎回ではなく「新規デバイス初回のみ」なので正規ユーザーの摩擦は最小。
3. **同時セッション上限（確定: 2）**：1ユーザー当たり**同時アクティブ2セッション**（PC＋スマホは許容）、3台目以降は**最古を失効**＝Netflix 型。
4. **ハード（稀・高スコア時のみ）**：ステップアップ必須化 or 新規デバイス拒否。**データ削除や即時BANはしない**。必ず人手レビューと「これは本人です」の申告経路を用意。

### 層D: Supabase 固有のレバー

- **Refresh token rotation + reuse detection を ON**：共有された refresh token が 2 デバイスで使われると reuse 検知で失効 → 共有側に自然な摩擦。
- **JWT 短寿命 + ローテーション**。
- Single-session-per-user は PC＋スマホの正規利用を壊すので**非推奨**、上限 N 方式を採用。
- ログインは `auth.audit_log_entries` に残るので、これを集計元にできる（自前 `login_events` は補完）。

---

## 5. 個人 → 組織への移行手順（既存ユーザーを壊さない）

1. 既存ユーザーごとに **個人 org を1つ生成**（name=表示名, owner=本人, plan/credits を profiles から移設）、`org_members` に owner で1行。
2. `projects/generations/jobs/renders/credit_ledger` に `org_id` 列を追加し、各行を所有者の個人 org で**バックフィル**。
3. RLS を `owner=auth.uid()` から `is_member(org_id)` に**切替**。
4. `spend_credits/log_cost/add_credits/set_plan/reset_monthly_credits` を **org 対象**に改修。
5. 動作確認後、`profiles.credits/plan` を**後日** drop（当面は残して二重管理を避けるためリード元を org に一本化）。

全ステップ冪等 SQL＋段階適用。ロールバック可能な順序にする。

---

## 6. フェーズ分割（実装状況 2026-09-11）

- **Phase A ✅ 完了**：本設計書。数値・ロール・悪用対策方針の確定。
- **Phase B ✅ 実装完了**：
  - B-1 DB: `006_orgs.sql`（organizations/org_members/org_invites/brands、org_id付与、RLS切替、accept_invite席数チェック、クレジットorgプール化、個人org自動移行）。ローカルPG14で全ロジック実証＋冪等確認。
  - B-2 UI: `spot-app/index.html`（org文脈 loadOrg、クレジット/プラン読取をorgへ、設定画面のチーム・メンバーパネル＝一覧/招待リンク/削除、`?invite=` 受諾フロー、Stripeを組織課金に変更）。移行前フォールバック経路をブラウザ検証済み。
  - ⏳ 残: ユーザーが `006_orgs.sql` を実DBに適用 → org有効時UIをブラウザ検証。
- **Phase C 🟡 コード部分完了 / 一部コンソール依存**：`007_anti_abuse.sql`（`login_events`＋`record_login`＝新デバイス判定＋`login_device_count`）、クライアントのログイン記録＋**共有ソフト誘導トースト**。★新デバイス“強制”OTP は Supabase Auth 設定 or Edge Function 側。
- **Phase D 🟡 コード部分完了 / 一部コンソール依存**：`007` にドメイン自動参加（`set_org_domain`＋`handle_new_user`）と **brands上限の実効化**（`create_brand`）。★同時セッション強制失効＝service_role Admin API、★SAML SSO＝Supabase Enterprise 設定。

### §6拡張 ✅ 実装完了（コード）／要ダッシュボード有効化 — 手順: `docs/auth-hardening.md`
`008_auth_hardening.sql`（ローカルPG14で実証・冪等）＋ index.html 配線で、4項目のうち3項目をEdge不要で実装:
1. **新デバイスOTP**：`trusted_devices` + Supabase標準メールOTP（`signInWithOtp`/`verifyOtp`）+ `#deviceGate`。config `deviceOtp:true` で有効（既定OFF=ロックアウト防止）。要: Email OTP有効化＋テンプレ `{{ .Token }}`。
2. **同時セッション上限=2**：`enforce_session_cap(2)` が自分の `auth.sessions` を最新2件に間引く（ログイン後に呼ぶ、配線済み）。実証済み。auth.sessions のDELETE権限が無ければEdge版に切替（doc にスニペット）。
3. **refresh token rotation + reuse detection**：純ダッシュボード（Auth設定 ON）。
4. **SAML SSO**：Enterprise設定。※ドメイン自動参加（`set_org_domain`, 007）で簡易SSOは実装済み。

---

## 7. 確定事項（2026-09-11 決定）

- **ロール = 3段（owner / member / viewer）**。admin/editor は分けない。
- **viewer 席 = 完全無料・無制限**（席数にカウントしない）。
- **同時セッション上限 = 2**（PC＋スマホ許容、3台目以降は最古を失効）。
- **新デバイス OTP = 全プラン**（新規デバイス初回のみメール OTP）。
- **Enterprise の席・ブランド無制限 = 技術上限なし（0=無制限）、契約/運用で管理**。
