#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8080}"
exec python3 -m uvicorn fieldbio.app:app --host 0.0.0.0 --port "$PORT" --reload

