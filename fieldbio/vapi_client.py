"""Small Vapi API client for PhoneBio wiring.

The functions in this module are intentionally boring and explicit: they build
payloads, refuse placeholder webhook URLs for live calls, and never print
secrets. Tests exercise the payload construction without contacting Vapi.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx


REPO_ROOT = Path(__file__).resolve().parent.parent
ASSISTANT_TEMPLATE = REPO_ROOT / "vapi" / "assistant.field-biology-worker.json"
DEFAULT_VAPI_BASE_URL = "https://api.vapi.ai"
PLACEHOLDER_URL = "https://YOUR-FORWARDED-OR-HOSTED-URL/webhook"


def api_key_from_env() -> str:
    return os.getenv("VAPI_API_KEY") or os.getenv("VAPI_PRIVATE_KEY") or ""


def vapi_base_url_from_env() -> str:
    return os.getenv("VAPI_BASE_URL", DEFAULT_VAPI_BASE_URL).rstrip("/")


def webhook_url_from_env() -> str:
    explicit = os.getenv("VAPI_WEBHOOK_URL")
    if explicit:
        return explicit
    public_base = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
    return f"{public_base}/webhook" if public_base else ""


def load_assistant_template(path: Path = ASSISTANT_TEMPLATE) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def assistant_payload(webhook_url: str | None = None) -> dict[str, Any]:
    payload = load_assistant_template()
    url = webhook_url or webhook_url_from_env() or payload.get("server", {}).get("url") or PLACEHOLDER_URL
    payload["server"] = {"url": url}
    payload.pop("serverUrl", None)
    return payload


def _ensure_live_ready(api_key: str, payload: dict[str, Any]) -> None:
    if not api_key:
        raise RuntimeError("Missing VAPI_API_KEY or VAPI_PRIVATE_KEY.")
    url = payload.get("server", {}).get("url", "")
    if not url or "YOUR-FORWARDED-OR-HOSTED-URL" in url:
        raise RuntimeError("Set VAPI_WEBHOOK_URL or PUBLIC_BASE_URL before making a live Vapi API call.")


def auth_headers(api_key: str) -> dict[str, str]:
    return {"authorization": f"Bearer {api_key}", "content-type": "application/json"}


def create_assistant(api_key: str, payload: dict[str, Any], base_url: str | None = None) -> dict[str, Any]:
    _ensure_live_ready(api_key, payload)
    response = httpx.post(
        f"{(base_url or vapi_base_url_from_env()).rstrip('/')}/assistant",
        headers=auth_headers(api_key),
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def phone_assignment_payload(assistant_id: str, webhook_url: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"assistantId": assistant_id}
    url = webhook_url or webhook_url_from_env()
    if url:
        payload["server"] = {"url": url}
    return payload


def assign_phone_number(
    api_key: str,
    phone_number_id: str,
    assistant_id: str,
    webhook_url: str | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    if not api_key:
        raise RuntimeError("Missing VAPI_API_KEY or VAPI_PRIVATE_KEY.")
    if not phone_number_id:
        raise RuntimeError("Missing VAPI_PHONE_NUMBER_ID.")
    if not assistant_id:
        raise RuntimeError("Missing assistant ID.")
    payload = phone_assignment_payload(assistant_id, webhook_url)
    response = httpx.patch(
        f"{(base_url or vapi_base_url_from_env()).rstrip('/')}/phone-number/{phone_number_id}",
        headers=auth_headers(api_key),
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def outbound_call_payload(assistant_id: str, phone_number_id: str, customer_number: str) -> dict[str, Any]:
    return {
        "assistantId": assistant_id,
        "phoneNumberId": phone_number_id,
        "customer": {"number": customer_number},
    }


def create_outbound_call(
    api_key: str,
    assistant_id: str,
    phone_number_id: str,
    customer_number: str,
    base_url: str | None = None,
) -> dict[str, Any]:
    if not api_key:
        raise RuntimeError("Missing VAPI_API_KEY or VAPI_PRIVATE_KEY.")
    payload = outbound_call_payload(assistant_id, phone_number_id, customer_number)
    response = httpx.post(
        f"{(base_url or vapi_base_url_from_env()).rstrip('/')}/call",
        headers=auth_headers(api_key),
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()

