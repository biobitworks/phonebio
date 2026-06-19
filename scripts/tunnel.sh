#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8080}"
DRY_RUN="${TUNNEL_DRY_RUN:-0}"

run_or_print() {
  if [[ "$DRY_RUN" == "1" ]]; then
    printf '%q ' "$@"
    printf '\n'
    exit 0
  fi
  exec "$@"
}

if command -v ngrok >/dev/null 2>&1; then
  run_or_print ngrok http "$PORT"
fi

if command -v cloudflared >/dev/null 2>&1; then
  run_or_print cloudflared tunnel --url "http://localhost:${PORT}"
fi

if command -v lt >/dev/null 2>&1; then
  run_or_print lt --port "$PORT"
fi

if command -v npx >/dev/null 2>&1; then
  run_or_print npx --yes localtunnel --port "$PORT"
fi

cat >&2 <<MSG
No supported tunnel command found.

Install one of:
  - ngrok
  - cloudflared
  - localtunnel (lt), or use npx localtunnel through npm

Then run:
  make dev
  make tunnel

Use the public HTTPS base URL for:
  PUBLIC_BASE_URL=https://...
  VAPI_WEBHOOK_URL=\${PUBLIC_BASE_URL}/webhook
  VAPI_CUSTOM_LLM_URL=\${PUBLIC_BASE_URL}/custom-llm
MSG
exit 1
