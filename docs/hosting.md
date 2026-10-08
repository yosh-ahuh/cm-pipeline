# ホスティングと流入導線（ランディング → アプリ）

最終更新: 2026-10-08。ドメインは **仮**（`creativepunx.com` のサブドメイン）。本番ドメインが決まったら §5 の手順で差し替える。

## 1. 構成（決定事項）

同じプラットフォーム（Cloudflare Pages）に **2 プロジェクト**、ドメインは分ける。

| 役割 | URL（仮） | ソース | 検索 |
|---|---|---|---|
| ランディング / サイト | `https://spot.creativepunx.com/` | `site/dist/`（`python3 site/build.py` の出力）。1 ページ版は `spot-landing.html` | index |
| アプリ | `https://app.spot.creativepunx.com/` | `spot-app/`（静的 SPA + Supabase） | noindex |

同一オリジン（`/app` パス）にしない理由: 両方が `index.html` の SPA でルーティング/キャッシュ設定が衝突する、Supabase の Site URL / Redirect URL をアプリだけに向けたい、ランディングは計測タグ・OGP・SEO 重視でアプリは noindex と要件が逆。

## 2. Cloudflare Pages 設定

**プロジェクト A: site**（GitHub 連携、本番ブランチ `master`）
- Root directory: `/`（リポジトリ直下）
- Build command: `python3 site/build.py`
- Build output directory: `site/dist`
- Custom domain: `spot.creativepunx.com`
- ヘッダは `site/static/_headers`（ビルドで `dist/` にコピー）

**プロジェクト B: app**
- Root directory: `spot-app`
- Build command: `bash build.sh`（env から `config.js` を生成。`config.js` は .gitignore 済み）
- Build output directory: `/`
- Environment variables: `SUPABASE_URL`、`SUPABASE_ANON_KEY`（publishable / anon のみ）、任意で `SUPPORT_EMAIL`
- Custom domain: `app.spot.creativepunx.com`
- ヘッダは `spot-app/_headers`（`X-Robots-Tag: noindex`、`index.html` / `config.js` は no-cache）

DNS（creativepunx.com の Cloudflare ゾーン）: Pages のカスタムドメイン追加で CNAME が自動作成される。Resend の SPF/DKIM/DMARC（ルート側）には触れない。

## 3. Supabase 側（アプリのドメインが決まったら）

- Authentication → URL Configuration
  - Site URL: `https://app.spot.creativepunx.com/`
  - Redirect URLs: `https://app.spot.creativepunx.com/**`（開発の `http://localhost:5500/**` は残す）
  - ⚠ パスワード再設定・マジックリンク・OAuth の戻りはここに無いと弾かれる
- Google OAuth 同意画面の承認済みドメインに `supabase.co`（既定）。自社ドメインで出したい場合は Supabase Custom Domain（有料）
- ワーカー env `APP_URL=https://app.spot.creativepunx.com/`（完了メールのリンク先）

## 4. 流入導線と計測

ランディング / サイトの CTA はすべてアプリへ `utm_*` と `plan` を付けて送る（`site/content/common.py` の `app_link()`、`spot-landing.html` は直書き）。

| CTA | リンク |
|---|---|
| ヒーロー「無料ではじめる」 | `app/?utm_source=landing&utm_medium=cta&utm_campaign=hero` |
| 料金カード | `…&utm_campaign=pricing&plan=free|starter|team` |
| 最下部 | `…&utm_campaign=final` |
| デモ / 営業 | `mailto:hello@creativepunx.com`（予約ツールが決まったら差し替え） |

アプリ側（`spot-app/index.html` 認証ブロック）: URL の `utm_*` / `plan` / `ref` を `localStorage.spot_attr` に保存して URL から消す → メール登録では `signUp` の metadata に同梱（030 のトリガが `profiles.signup_attribution` へ）、OAuth 登録や別タブでのサインインではサインイン後に RPC `set_signup_attribution` で保存（本人のみ、未設定のときだけ）。

集計（SQL Editor）:
```sql
select signup_attribution->>'utm_source' as src, signup_attribution->>'utm_campaign' as camp,
       signup_attribution->>'plan' as plan, count(*)
from public.profiles where signup_attribution is not null group by 1,2,3 order by 4 desc;
```

サイト側の訪問計測（CTA クリック率）は未設定。Cloudflare Web Analytics（無料・Cookie なし）を Pages プロジェクト A で有効化するのが最小構成。

## 5. 本番ドメインへの差し替え手順

1. `site/content/common.py` の `DOMAIN` を変更 → `python3 site/build.py`
2. `spot-landing.html` の `spot.creativepunx.com` / `app.spot.creativepunx.com` / `hello@creativepunx.com` を置換
3. `spot-app/worker/.env.example`・`docs/hosting.md`・Pages のカスタムドメイン・Supabase URL Configuration（§3）
4. 旧 URL から 301（Pages の `_redirects` か Cloudflare Bulk Redirects）
5. Search Console / Bing に `sitemap-index.xml` を再登録（`site/README.md`）

## 6. 状態（2026-10-08）

- コード側（CTA リンク、utm 取り込み、030、`_headers`、`build.sh`）: 済
- Pages プロジェクト作成・DNS・Supabase URL 設定・030 の本番適用: **未**（ユーザー作業。030 は SQL Editor で実行）
