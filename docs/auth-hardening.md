# 認証ハードニング手順（設計書 §6 のコンソール/Edge依存4項目）

マルチシート悪用対策のうち、**コードだけで完結しない**4項目の適用手順。
対応コードは実装済み（`008_auth_hardening.sql` ＋ `index.html` のクライアント配線）。
ここに書いてある**あなたの操作**（SQL適用・ダッシュボード設定）で有効化される。

前提: `006_orgs.sql` → `007_anti_abuse.sql` 適用済み。次に **`008_auth_hardening.sql` を SQL Editor で Run**。

---

## ① 新デバイス強制OTP  ← コード済み・要「有効化」

**仕組み**: 未知の端末からログインすると、Supabase 標準の**メールOTP**（6桁コード）で本人確認し、確認できた端末を `trusted_devices` に記録する。外部メール業者は不要（サインアップ確認メールと同じ経路）。

**有効化の手順（3つ）**
1. `008_auth_hardening.sql` を適用（`trusted_devices` / `is_device_trusted` / `trust_device`）。
2. Supabase ダッシュボードで **メールOTPを有効化＋テンプレートにコードを入れる**:
   - Authentication → Providers → **Email**：`Enable Email OTP`（またはOTP/Magic Link）をON。
   - Authentication → **Email Templates → Magic Link (OTP)**：本文に **`{{ .Token }}`**（6桁コード）が含まれていること。無ければ追記。
3. `config.js` に**フラグを追加**して有効化（既定はOFF＝ロックアウト事故防止）:
   ```js
   window.SPOT_CONFIG = {
     url: '...', anonKey: '...',
     deviceOtp: true,          // ← これで新デバイスOTPが有効に
   };
   ```

**挙動**: `deviceOtp:true` かつ未信頼端末のとき、ログイン後に確認画面（`#deviceGate`）が出てコード入力→検証→`trust_device` で信頼登録。`false` や 008 未適用時は**何も起きない（フェイルオープン）**。

**注意（強度）**: 現状はパスワードで認証済みのセッションに UI ゲートを重ねる**抑止（deterrent）**方式。devtools でオーバーレイを外せば裏のセッションは有効なので、これは「共有の心理的ハードル」であって完全な強制ではない。

### 厳格モード（D8）— 堅牢にやるなら「クライアント上書き」ではなく MFA
未信頼端末に確実にセッションを与えない強制は、クライアント JS では脆くなる（signOut→OTP再ログインの綱渡りになり、状態が壊れやすい）。**堅牢な標準機能＝Supabase MFA（TOTP）**を使うのが正解:
1. Authentication → **Multi-Factor Authentication** を有効化。
2. アプリに MFA エンロール/チャレンジ UI を足す（`sb.auth.mfa.enroll()` / `challenge()` / `verify()`）。ログイン後 `sb.auth.mfa.getAuthenticatorAssuranceLevel()` が `aal1` なら未検証 → チャレンジ必須にする。
3. これで**認証器（TOTP）を持つ本人以外はセッションを完成できない**＝共有ログインを事実上不可能にできる。

＝ 新デバイスOTP（`deviceOtp`）は**軽量な抑止**、MFA(TOTP)は**厳格な強制**。運用フェーズに応じて選ぶ。まずは opt-in の `deviceOtp` で様子見 → 悪用が実際に出たら MFA を必須化、が無駄がない。

---

## ② 同時セッション上限=2 の強制失効  ← コード済み・SQL適用で有効

**仕組み**: ログイン直後にクライアントが `enforce_session_cap(2)` を呼び、自分の `auth.sessions` を**最新2件（最終アクティビティ順）に間引く**（3台目以降＝最古を失効＝Netflix型）。

**有効化**: `008_auth_hardening.sql` を適用するだけ（クライアントは配線済み）。

**権限の注意**: `enforce_session_cap` は `auth.sessions` を DELETE する SECURITY DEFINER 関数。
- 適用時にエラーが出なければ、SQL Editor 実行者（postgres）に権限があり動く。
- もし `permission denied for table sessions` 等が出る環境なら、**Edge Function 版**に切替:
  1. `supabase/functions/session-cap/index.ts` を作成し、`service_role` で `auth.sessions` を間引く（下記スニペット）。
  2. クライアントの `enforceSessionCap()` を、RPC から `sb.functions.invoke('session-cap')` に差し替え。

  ```ts
  // supabase/functions/session-cap/index.ts（Edge Function 版・権限エラー時のみ）
  import { createClient } from 'jsr:@supabase/supabase-js@2'
  Deno.serve(async (req) => {
    const auth = req.headers.get('Authorization') ?? ''
    const admin = createClient(Deno.env.get('SUPABASE_URL')!, Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!)
    const { data: { user } } = await admin.auth.getUser(auth.replace('Bearer ', ''))
    if (!user) return new Response('unauthorized', { status: 401 })
    const { data: s } = await admin.from('sessions').schema('auth')
      .select('id').eq('user_id', user.id).order('updated_at', { ascending: false })
    const kill = (s ?? []).slice(2).map(r => r.id)
    if (kill.length) await admin.from('sessions').schema('auth').delete().in('id', kill)
    return Response.json({ revoked: kill.length })
  })
  ```
  デプロイ: `supabase functions deploy session-cap`（あなたの環境で。CLI ログイン必要）。

---

## ③ Refresh Token Rotation + Reuse Detection  ← 純ダッシュボード

共有された refresh token が2端末で使われると reuse 検知で失効し、共有側に自然な摩擦を与える。

**手順**: Authentication → **Sessions / Security**（プロジェクトにより名称差）で
- **Refresh Token Rotation**: ON
- **Reuse Detection / Reuse Interval**: ON（間隔は既定でよい）
- 併せて **JWT expiry** を短め（例 3600s）に。

コード変更不要。supabase-js は自動でローテーションに追従する。

---

## ④ SAML SSO / ドメイン参加  ← ドメイン参加はコード済み / SSOはEnterprise

- **ドメイン自動参加**（簡易SSO・実装済み）: `007` の `set_org_domain(org, 'company.com')` を実行すると、以後 `@company.com` の**新規サインアップが自動で member 参加**（席が空いている場合）。オーナーが設定画面や SQL から設定。
  ```sql
  select set_org_domain('<組織のUUID>', 'company.com');
  ```
- **本格SAML SSO**: Supabase の **Enterprise 機能**。Authentication → SSO で IdP（Okta/Azure AD 等）を登録。プラン/契約が必要で、このリポジトリのコードだけでは有効化できない。必要になった段階で Supabase に相談。

---

## 適用順まとめ
1. SQL Editor: `008_auth_hardening.sql` を Run（①②の土台）。
2. ダッシュボード: ②はこれだけで有効。①は Email OTP 有効化＋テンプレに `{{ .Token }}`、③はセッション設定 ON。
3. `config.js` に `deviceOtp: true`（①を使う場合）。
4. ④のドメイン参加は `set_org_domain` を実行。SAML は必要時に Enterprise 設定。
