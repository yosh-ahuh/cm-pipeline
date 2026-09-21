# メールの言語切替（日本語 / 英語）

Spot の認証メール（パスワード再設定・認証番号・登録確認）を、**ユーザーの言語に合わせて日本語/英語で出し分ける**ための設定です。

## 仕組み

- アプリは、ユーザーの表示言語を `user_metadata.lang`（`"ja"` または `"en"`）に保存します。
  - 新規登録時：`signUp` の `options.data.lang`
  - ログイン中：`onAppReady` と表示言語ドロップダウンの変更時に `updateUser({ data: { lang } })`
  - 表示言語の既定は**デバイスの言語設定**（日本語なら `ja`、それ以外は `en`）。
- Supabase のメールテンプレートは Go テンプレートで、`{{ index .Data "lang" }}` を参照して本文を出し分けます（メタデータが空のユーザーでも描画で落ちない安全な書き方）。
  - `lang` が未設定の旧ユーザー等は **英語にフォールバック**します。

## ロゴのホスティング（メールに画像を出すため・最初に1回）

メールはローカルの `assets/` を参照できず、Gmail/Outlook 等は base64 埋め込み画像もブロックするため、ロゴは**公開URL**が必要です。Supabase Storage の公開バケットを使います。

1. Supabase → **Storage** → **New bucket** → 名前 `brand`、**Public bucket を ON** → Create。
2. その `brand` バケットに `spot-app/assets/spot-mark.png` をアップロード（ファイル名は `spot-mark.png` のまま）。
3. 公開URLは次になります（テンプレートにこのURLを直書き済み）:
   `https://mmnpfxrodsurxpeyaaaf.supabase.co/storage/v1/object/public/brand/spot-mark.png`
   - バケット名やファイル名を変えた場合は、各テンプレートの `<img src="...">` を合わせて修正してください。
   - ブラウザでこのURLを開いてロゴが表示されれば準備OKです。

## 設定手順（Supabase ダッシュボード）

Authentication → **Emails** → **Templates** で、各テンプレートに以下を貼り付けます（ブランド版：ロゴ＋インディゴ #4A67E3）。

| テンプレート | 貼り付けるファイル | 使われる場面 |
|---|---|---|
| Reset Password | [`reset-password.html`](./reset-password.html) | `resetPasswordForEmail`（パスワードを忘れた） |
| Magic Link | [`magic-link.html`](./magic-link.html) | `signInWithOtp`（認証番号ログイン）。`{{ .Token }}` が番号 |
| Confirm signup | [`confirm-signup.html`](./confirm-signup.html) | 新規登録の確認メール |

### 件名（Subject）も言語切替
各テンプレートの **Subject 欄**（本文HTMLとは別管理）にも同じ条件分岐を入れて、本文と言語を揃える（既定は英語のままなので要変更）:

| テンプレート | Subject 欄に入れる値 |
|---|---|
| Magic Link | `{{ if eq (index .Data "lang") "ja" }}Spot 認証番号{{ else }}Your Spot verification code{{ end }}` |
| Reset Password | `{{ if eq (index .Data "lang") "ja" }}Spot パスワードの再設定{{ else }}Reset your Spot password{{ end }}` |
| Confirm signup | `{{ if eq (index .Data "lang") "ja" }}Spot メールアドレスの確認{{ else }}Confirm your Spot email{{ end }}` |

### 配信（SMTP）
- 組み込みメールはレート制限あり・本番不可。**カスタムSMTP＝Resend** を使用。
  Supabase → Authentication → Emails → SMTP Settings: Host `smtp.resend.com` / Port `465` / Username `resend` / Password `ResendのAPIキー` / Sender `no-reply@creativepunx.com` / Name `Spot`。
- 送信ドメイン `creativepunx.com` を Resend で認証済み（DKIM `resend._domainkey`、CNAME `rsend`/`send`、DMARC `_dmarc`）。SPF/DKIM/DMARC 全PASS。
- ロゴは Storage 公開バケット `brand/spot-mark.png`。**迷惑メール内では Gmail が画像を読み込まない**ため、受信トレイ＋画像表示で確認する。
- 新規ドメインは初期に迷惑メール判定されやすい（レピュテーション）。「迷惑メールではない」操作＋通常運用で改善。

### 補足
- **認証番号の桁数**：Authentication → Providers → Email → **Email OTP Length** で設定（例: 8桁）。テンプレート側は `{{ .Token }}` のままでOK。
- **リダイレクトURL**：Authentication → **URL Configuration** → Redirect URLs に、アプリのURL（dev の `http://localhost:5500/**` と本番オリジン）を許可登録。これが無いと再設定リンクが弾かれます。
- テンプレートは最小限のインラインCSSのみ。ブランドに合わせてロゴや色を足す場合も、`{{ if eq (index .Data "lang") "ja" }} … {{ else }} … {{ end }}` の分岐は残してください。
- 既存ユーザーは一度ログイン（または言語を切替）すると `lang` が保存され、以後のメールが言語に追従します。
