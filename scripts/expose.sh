#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8080}"
exec vapi listen --forward-to "localhost:${PORT}/webhook"

