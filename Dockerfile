# SPOT ワーカー常駐イメージ（Railway / Fly / 任意の Docker ホスト用）
#
# 1 コンテナで動くもの:
#   - spot-app/worker/worker.py --watch --live  … Supabase jobs を拾って cm-pipeline で実生成（fal / Claude）
#   - spot-app/worker/stripe_webhook.py        … Stripe Webhook 待受（PORT、任意）
# 同梱するもの: cm-pipeline（Python）、ad-prototype（Remotion ＝ Node + Chrome Headless Shell）、ffmpeg、日本語フォント。
#
# ビルド（リポジトリ直下で）: docker build -t spot-worker .
# 実行: docker run --env-file spot-app/worker/.env -e FAL_KEY=... -e PORT=8080 spot-worker
# Railway: railway.toml が dockerfilePath=Dockerfile を指す。変数は SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY / FAL_KEY /
#          ANTHROPIC_API_KEY（任意）/ RESEND_API_KEY・RESEND_FROM・APP_URL（任意）/ STRIPE_WEBHOOK_SECRET（任意）。
#
# ※ ローカル検証（2026-10-07）では未ビルド。初回は `railway up` 前に手元で docker build を一度通すこと。

FROM node:20-bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    CM_PIPELINE_DIR=/app/cm-pipeline \
    REMOTION_DISABLE_TELEMETRY=1

# ffmpeg・Python・Chrome Headless Shell の依存ライブラリ・日本語フォント（Remotion の字幕描画に必須）
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-pip python3-venv ffmpeg ca-certificates curl \
      fonts-noto-cjk fonts-noto-color-emoji \
      libnss3 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 \
      libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 libpango-1.0-0 libcairo2 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Python（cm-pipeline ＋ worker）---
COPY cm-pipeline/requirements.txt /app/cm-pipeline/requirements.txt
COPY spot-app/worker/requirements.txt /app/spot-app/worker/requirements.txt
RUN python3 -m venv /app/.venv \
    && /app/.venv/bin/pip install --upgrade pip \
    && /app/.venv/bin/pip install -r /app/cm-pipeline/requirements.txt -r /app/spot-app/worker/requirements.txt

# --- Node（Remotion）--- 依存だけ先に入れてレイヤーをキャッシュ
COPY ad-prototype/package.json ad-prototype/package-lock.json /app/ad-prototype/
RUN cd /app/ad-prototype && npm ci --no-audit --no-fund

# --- ソース ---
COPY cm-pipeline /app/cm-pipeline
COPY ad-prototype /app/ad-prototype
COPY spot-app/worker /app/spot-app/worker

# Chrome Headless Shell をビルド時に取得（起動後の初回レンダーで落ちないように）
RUN cd /app/ad-prototype && npx remotion browser ensure

# 生成物の置き場（Railway ではボリュームを /app/cm-pipeline/projects にマウントすると再起動後も残る）
RUN mkdir -p /app/cm-pipeline/projects/_supabase /app/ad-prototype/public/projects \
    && chmod +x /app/spot-app/worker/entrypoint.sh

EXPOSE 8080
ENV PORT=8080
CMD ["/app/spot-app/worker/entrypoint.sh"]
