// Supabase 接続情報のテンプレート。
// これを config.js にコピーし、あなたの Supabase プロジェクトの値を入れてください
// （config.js は .gitignore 済み。anon キーは公開前提のキーなのでフロントに置いてOK）。
//   Supabase Studio → Project Settings → API から取得:
//     Project URL         → url
//     Project API keys / anon public → anonKey
window.SPOT_CONFIG = {
  url: 'https://YOUR-PROJECT.supabase.co',
  anonKey: 'YOUR-ANON-PUBLIC-KEY',

  // 課金（任意）: Stripe の Payment Link URL を入れると「アップグレード/追加購入」が有効化されます。
  // Stripe ダッシュボード → Payment Links で各プラン・追加スポットのリンクを作成し、URL を貼るだけ。
  // 支払い完了で set_plan を反映するには Webhook 設定が必要（worker/stripe_webhook.py と README 参照）。
  // 空のままなら「準備中」表示になります。
  stripeLinks: {
    starter: '',      // 例: 'https://buy.stripe.com/xxxxx'
    team: '',
    business: '',
    enterprise: '',   // 通常は「お問い合わせ」。URL があればそれを開きます
    extraSpot: '',    // 追加スポット購入のリンク
  },
};
