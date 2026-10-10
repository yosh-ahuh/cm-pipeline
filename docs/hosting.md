# ホスティングと流入導線（ランディング → アプリ）

最終更新: 2026-10-08。ドメインは **仮**（`creativepunx.com` のサブドメイン）。本番ドメインが決まったら §5 の手順で差し替える。

## 1. 現状（2026-10-08 時点の事実）

> **2026-10-10 決定（同日に更新）: 正本はこのモノレポ https://github.com/yosh-ahuh/cm-pipeline.git（master、作業ツリー `/Users/yosh/work/SPOT`）。** 一時的に yosh-ahuh/spot（main）を正本とする判断が出たが、spot 側に 10/6〜10/10 のアプリ・ワーカー変更（7 ステップ制作フロー、ブランド取り込み、台本ステージ、検品、027〜029）が無いため撤回。yosh-ahuh/spot は旧リポとして凍結し、アプリ・ワーカー・サイト・LP・docs はすべてここで管理する。Railway のワーカーはこのモノレポから `railway up`（実装セッションに一元化）。差分の記録は docs/port-to-spot-2026-10.md。

| 役割 | 状態 |
|---|---|
| アプリ `spot-app/` | **Vercel にデプロイ済み**。チーム `creative-punx`、プロジェクト `spot`、本番 URL `https://spot-smoky-six.vercel.app`（2026-09-25 作成、最終デプロイ 2026-10-01）。ローカルの `spot-app` で `vercel --prod` を実行＝ローカルの `config.js` ごとアップロード。**Vercel Authentication が有効で、Vercel にログインした人しか開けない**（外部は 302） |
| ランディング（1 ページ `spot-landing.html`） | **Vercel にデプロイ済み**（2026-10-08）。プロジェクト `spot-landing`、URL `https://spot-landing-seven.vercel.app`。`bash site/deploy_landing.sh` で更新。アプリ同様 Vercel Authentication で非公開、`X-Robots-Tag: noindex` 付き |
| 生成サイト `site/dist/`（多ページ） | **Vercel にデプロイ済み**（2026-10-08）。プロジェクト `spot-site`、URL `https://spot-site-six.vercel.app`。`bash site/deploy_site.sh`（ビルド込み）で更新。Vercel Authentication（`all`）で非公開、`X-Robots-Tag: noindex` 付き（`PUBLIC=1` で外す） |
| カスタムドメイン | なし（Vercel のドメイン 0 件）。`spot.video` は第三者所有 |
| Supabase | Site URL は Vercel の URL、Redirect URLs に `http://localhost:5500/**` 追加済み（2026-10-07） |
| ワーカー | Railway（停止中）。Vercel では動かせない（常駐プロセス） |

## 2. 構成（決定事項）

アプリが既に Vercel にあるので、**ランディングも同じ Vercel アカウントに置く**。ドメインは分ける。

| 役割 | URL（仮） | Vercel プロジェクト | ソース | 検索 |
|---|---|---|---|---|
| ランディング / サイト | `https://spot.creativepunx.com/` | `spot-site`（既存） | `site/dist/`（`bash site/deploy_site.sh`） | index |
| アプリ | `https://app.spot.creativepunx.com/` | `spot`（既存） | `spot-app/` | noindex（`spot-app/vercel.json`） |

同一オリジン（`/app` パス）にしない理由: 両方が `index.html` の SPA でルーティング/キャッシュ設定が衝突する、Supabase の Site URL / Redirect URL をアプリだけに向けたい、ランディングは計測タグ・OGP・SEO 重視でアプリは noindex と要件が逆。

## 3. 公開手順（ユーザー作業）— **保留中**（2026-10-08 ユーザー判断「公開まではしない」。Vercel Authentication は ON のまま、ドメインも付けない。公開を決めたらここから）

**アプリ（既存 `spot`）**
1. Vercel → Project `spot` → Settings → Deployment Protection → **Vercel Authentication を OFF**（これをしないと一般ユーザーが開けない）
2. Settings → Domains に `app.spot.creativepunx.com` を追加 → 表示された CNAME を creativepunx.com の DNS に追加
3. デプロイは従来どおり `cd spot-app && vercel --prod`（`vercel.json` の noindex / no-cache ヘッダが付く）

**サイト（既存 `spot-site`）**
1. Settings → Deployment Protection → Vercel Authentication を OFF（現在 `all`）。`PUBLIC=1 bash site/deploy_site.sh` で noindex なしで再デプロイ
2. Settings → Domains に `spot.creativepunx.com` を追加 → CNAME を DNS に追加
3. Git 連携にする場合: Root Directory `site`、Build Command `python3 build.py`、Output Directory `dist`

**Supabase**（Authentication → URL Configuration）
- Site URL: `https://app.spot.creativepunx.com/`
- Redirect URLs: `https://app.spot.creativepunx.com/**` を追加（`https://spot-smoky-six.vercel.app/**` と `http://localhost:5500/**` は残す）
- ⚠ パスワード再設定・マジックリンク・OAuth の戻りはここに無いと弾かれる
- ワーカー env `APP_URL=https://app.spot.creativepunx.com/`（完了メールのリンク先）

## 4. 流入導線と計測

ランディング / サイトの CTA はすべてアプリへ `utm_*` と `plan` を付けて送る（`site/content/common.py` の `app_link()`、`spot-landing.html` は直書き）。

| CTA | リンク |
|---|---|
| ヒーロー「7 日間無料で試す」 | `app/?utm_source=landing&utm_medium=cta&utm_campaign=hero` |
| 料金カード | `…&utm_campaign=pricing&plan=starter|team|business`（Free プランは廃止・2026-10-09） |
| 最下部 | `…&utm_campaign=final` |
| ナビ「7 日間無料で試す」 | `…&utm_campaign=nav` |
| 営業（Enterprise カードのみ） | `mailto:hello@creativepunx.com?subject=Spot%20Enterprise`（**デモ予約の導線は廃止**・2026-10-08。メールボックスの実在は未確認） |

アプリ側（`spot-app/index.html` 認証ブロック）: URL の `utm_*` / `plan` / `ref` を `localStorage.spot_attr` に保存して URL から消す → メール登録では `signUp` の metadata に同梱（030 のトリガが `profiles.signup_attribution` へ）、OAuth 登録や別タブでのサインインではサインイン後に RPC `set_signup_attribution` で保存（本人のみ、未設定のときだけ）。030 は本番適用済・通し検証済（2026-10-08）。

集計（SQL Editor）:
```sql
select signup_attribution->>'utm_source' as src, signup_attribution->>'utm_campaign' as camp,
       signup_attribution->>'plan' as plan, count(*)
from public.profiles where signup_attribution is not null group by 1,2,3 order by 4 desc;
```

サイト側の訪問計測: **Vercel Web Analytics を `spot-landing` / `spot-site` で有効化済み**（2026-10-08）。静的 HTML なので各ページが `/_vercel/insights/script.js` を読み込む（`spot-landing.html` 末尾、`site/build.py` の head）。Vercel → Project → Analytics で PV / 参照元 / 国を確認。CTA クリック率は「アプリ側の `signup_attribution` 件数 ÷ サイトの PV」で見る。Deployment Protection ON の間は Vercel ログイン者の閲覧しか計上されない。

## 5. 本番ドメインへの差し替え手順

1. `site/content/common.py` の `DOMAIN` を変更 → `python3 site/build.py`
2. `spot-landing.html` の `spot.creativepunx.com` / `app.spot.creativepunx.com` / `hello@creativepunx.com` を置換
3. `spot-app/worker/.env.example`・本ドキュメント・Vercel の Domains・Supabase URL Configuration（§3）
4. 旧 URL から 301（`vercel.json` の `redirects`）
5. Search Console / Bing に `sitemap-index.xml` を再登録（`site/README.md`）

## 6. 代替

Cloudflare Pages でも同じ構成が組める（`_headers` で同等のヘッダ）。ただしアプリが既に Vercel にあるため、分ける理由がない限り Vercel に揃える。
