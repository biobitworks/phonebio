"""Create a Vapi assistant from the local template.

This script intentionally refuses to run without VAPI_API_KEY or VAPI_PRIVATE_KEY.
It does not assign a phone number; do that in the dashboard or after confirming
the target VAPI_PHONE_NUMBER_ID.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx


REPO_ROOT = Path(__file__).resolve().parent.parent
ASSISTANT_PATH = REPO_ROOT / "vapi" / "assistant.field-biology-worker.json"


def main() -> None:
    api_key = os.getenv("VAPI_API_KEY") or os.getenv("VAPI_PRIVATE_KEY")
    if not api_key:
        print("Missing VAPI_API_KEY or VAPI_PRIVATE_KEY. Refusing to call Vapi API.", file=sys.stderr)
        raise SystemExit(1)

    assistant = json.loads(ASSISTANT_PATH.read_text(encoding="utf-8"))
    response = httpx.post(
        "https://api.vapi.ai/assistant",
        headers={"authorization": f"Bearer {api_key}", "content-type": "application/json"},
        json=assistant,
        timeout=30,
    )
    if response.is_error:
        print(f"Vapi assistant creation failed: {response.status_code}", file=sys.stderr)
        print(response.text, file=sys.stderr)
        raise SystemExit(1)
    print(response.text)


if __name__ == "__main__":
    main()

