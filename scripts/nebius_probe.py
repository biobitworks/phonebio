"""Probe optional Nebius Token Factory chat-completions setup.

This is intentionally separate from the deterministic PhoneBio tool layer. It
only verifies that a configured Nebius API key/model can answer a tiny
non-sensitive request through the OpenAI-compatible endpoint.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from fieldbio.config import settings


def _redacted_key_state(value: str) -> dict[str, Any]:
    return {
        "set": bool(value),
        "length": len(value) if value else 0,
        "hasWhitespace": bool(value and value != value.strip()),
    }


def _models_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/models"


def _chat_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/chat/completions"


def _fetch_models(api_key: str, base_url: str) -> dict[str, Any]:
    response = httpx.get(
        _models_url(base_url),
        headers={"authorization": f"Bearer {api_key}"},
        timeout=30,
    )
    result: dict[str, Any] = {"httpStatus": response.status_code}
    response.raise_for_status()
    body = response.json()
    data = body.get("data") if isinstance(body, dict) else None
    model_ids = [item.get("id") for item in data if isinstance(item, dict) and item.get("id")] if isinstance(data, list) else []
    result["modelCount"] = len(model_ids)
    result["modelIds"] = model_ids
    return result


def _choose_model(configured: str, model_ids: list[str]) -> tuple[str, bool]:
    if configured in model_ids:
        return configured, False
    # Prefer a close model from the same family if the configured name is stale.
    prefix = configured.rsplit("-", 1)[0] if "-" in configured else configured
    for model_id in model_ids:
        if configured and (configured in model_id or prefix in model_id):
            return model_id, True
    for model_id in model_ids:
        if model_id.startswith("Qwen/"):
            return model_id, True
    return configured, False


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe optional Nebius Token Factory setup.")
    parser.add_argument("--list-models", action="store_true", help="List available model IDs with no chat-completion request.")
    parser.add_argument("--no-fallback", action="store_true", help="Do not auto-select a nearby available model for the probe.")
    args = parser.parse_args()

    api_key = (os.getenv("NEBIUS_API_KEY") or settings.nebius_api_key).strip()
    base_url = (os.getenv("NEBIUS_BASE_URL") or settings.nebius_base_url).rstrip("/")
    model = os.getenv("NEBIUS_MODEL") or settings.nebius_model
    result: dict[str, Any] = {
        "provider": "nebius",
        "configured": bool(api_key),
        "apiKey": _redacted_key_state(api_key),
        "baseUrlHost": base_url.removeprefix("https://").removeprefix("http://").split("/")[0],
        "model": model,
    }
    if not api_key:
        result["ok"] = False
        result["reason"] = "missing NEBIUS_API_KEY"
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(2)

    try:
        models = _fetch_models(api_key, base_url)
        result["modelsHttpStatus"] = models["httpStatus"]
        result["modelCount"] = models["modelCount"]
        if args.list_models:
            result["ok"] = True
            result["modelIds"] = models["modelIds"]
            print(json.dumps(result, indent=2, sort_keys=True))
            raise SystemExit(0)
        selected_model, used_fallback = _choose_model(model, models["modelIds"])
        result["model"] = selected_model
        result["configuredModel"] = model
        result["usedModelFallback"] = used_fallback
        if used_fallback and args.no_fallback:
            result["ok"] = False
            result["reason"] = "configured model unavailable"
            print(json.dumps(result, indent=2, sort_keys=True))
            raise SystemExit(2)
        model = selected_model
    except httpx.HTTPStatusError as error:
        result["ok"] = False
        result["httpStatus"] = error.response.status_code
        result["reason"] = "models_http_error"
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(1)
    except httpx.HTTPError as error:
        result["ok"] = False
        result["reason"] = error.__class__.__name__
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(1)

    started = time.time()
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Reply with exactly: phonebio-nebius-ok"},
            {"role": "user", "content": "Health check."},
        ],
        "temperature": 0,
        "max_tokens": 16,
    }
    try:
        response = httpx.post(
            _chat_url(base_url),
            headers={"authorization": f"Bearer {api_key}", "content-type": "application/json"},
            json=payload,
            timeout=30,
        )
        result["httpStatus"] = response.status_code
        response.raise_for_status()
        body = response.json()
        text = (body.get("choices") or [{}])[0].get("message", {}).get("content", "")
        result["ok"] = bool(text)
        result["responsePresent"] = bool(text)
        result["latencyMs"] = int((time.time() - started) * 1000)
    except httpx.HTTPStatusError as error:
        result["ok"] = False
        result["httpStatus"] = error.response.status_code
        result["reason"] = "http_error"
    except httpx.HTTPError as error:
        result["ok"] = False
        result["reason"] = error.__class__.__name__

    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
