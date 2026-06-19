#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8080}"

if command -v ngrok >/dev/null 2>&1; then
  exec ngrok http "$PORT"
fi

if command -v cloudflared >/dev/null 2>&1; then
  exec cloudflared tunnel --url "http://localhost:${PORT}"
fi

if command -v lt >/dev/null 2>&1; then
  exec lt --port "$PORT"
fi

cat >&2 <<MSG
No supported tunnel command found.

Install one of:
  - ngrok
  - cloudflared
  - localtunnel (lt)

Then run:
  make dev
  make tunnel

Use the public HTTPS base URL for:
  PUBLIC_BASE_URL=https://...
  VAPI_WEBHOOK_URL=\${PUBLIC_BASE_URL}/webhook
  VAPI_CUSTOM_LLM_URL=\${PUBLIC_BASE_URL}/custom-llm
MSG
exit 1
