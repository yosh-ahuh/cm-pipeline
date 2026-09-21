# メールの言語切替（日本語 / 英語）

Spot の認証メール（パスワード再設定・認証番号・登録確認）を、**ユーザーの言語に合わせて日本語/英語で出し分ける**ための設定です。

## 仕組み

- アプリは、ユーザーの表示言語を `user_metadata.lang`（`"ja"` または `"en"`）に保存します。
  - 新規登録時：`signUp` の `options.data.lang`
  - ログイン中：`onAppReady` と表示言語ドロップダウンの変更時に `updateUser({ data: { lang } })`
  - 表示言語の既定は**デバイスの言語設定**（日本語なら `ja`、それ以外は `en`）。
- Supabase のメールテンプレートは Go テンプレートで、`{{ .Data.lang }}` を参照して本文を出し分けます。
  - `lang` が未設定の旧ユーザー等は **英語にフォールバック**します。

## 設定手順（Supabase ダッシュボード）

Authentication → **Emails** → **Templates** で、各テンプレートに以下を貼り付けます。

| テンプレート | 貼り付けるファイル | 使われる場面 |
|---|---|---|
| Reset Password | [`reset-password.html`](./reset-password.html) | `resetPasswordForEmail`（パスワードを忘れた） |
| Magic Link | [`magic-link.html`](./magic-link.html) | `signInWithOtp`（認証番号ログイン）。`{{ .Token }}` が番号 |
| Confirm signup | [`confirm-signup.html`](./confirm-signup.html) | 新規登録の確認メール |

### 補足
- **認証番号の桁数**：Authentication → Providers → Email → **Email OTP Length** で設定（例: 8桁）。テンプレート側は `{{ .Token }}` のままでOK。
- **リダイレクトURL**：Authentication → **URL Configuration** → Redirect URLs に、アプリのURL（dev の `http://localhost:5500/**` と本番オリジン）を許可登録。これが無いと再設定リンクが弾かれます。
- テンプレートは最小限のインラインCSSのみ。ブランドに合わせてロゴや色を足す場合も、`{{ if eq .Data.lang "ja" }} … {{ else }} … {{ end }}` の分岐は残してください。
- 既存ユーザーは一度ログイン（または言語を切替）すると `lang` が保存され、以後のメールが言語に追従します。
