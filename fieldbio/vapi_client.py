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

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


REPO_ROOT = Path(__file__).resolve().parent.parent
ASSISTANT_TEMPLATE = REPO_ROOT / "vapi" / "assistant.field-biology-worker.json"
DEFAULT_VAPI_BASE_URL = "https://api.vapi.ai"
PLACEHOLDER_URL = "https://YOUR-FORWARDED-OR-HOSTED-URL/webhook"
PLACEHOLDER_CUSTOM_LLM_URL = "https://YOUR-FORWARDED-OR-HOSTED-URL/custom-llm"
PLACEHOLDER_HOST = "your-tunnel-or-deploy.example.com"


def is_placeholder_url(value: str | None) -> bool:
    if not value:
        return True
    lowered = value.lower()
    return "your-forwarded-or-hosted-url" in lowered or PLACEHOLDER_HOST in lowered


def api_key_from_env() -> str:
    return os.getenv("VAPI_API_KEY") or os.getenv("VAPI_PRIVATE_KEY") or ""


def vapi_base_url_from_env() -> str:
    return os.getenv("VAPI_BASE_URL", DEFAULT_VAPI_BASE_URL).rstrip("/")


def webhook_url_from_env() -> str:
    explicit = os.getenv("VAPI_WEBHOOK_URL")
    if explicit and not is_placeholder_url(explicit):
        return explicit
    public_base = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
    return f"{public_base}/webhook" if public_base and not is_placeholder_url(public_base) else ""


def _custom_llm_url_from_webhook(webhook_url: str) -> str:
    if webhook_url.endswith("/webhook"):
        return f"{webhook_url[:-len('/webhook')]}/custom-llm"
    return ""


def custom_llm_url_from_env_or_webhook(webhook_url: str, *, prefer_env: bool = True) -> str:
    derived = _custom_llm_url_from_webhook(webhook_url)
    if not prefer_env and derived:
        return derived
    explicit = os.getenv("VAPI_CUSTOM_LLM_URL", "").rstrip("/")
    if explicit and not is_placeholder_url(explicit):
        return explicit
    if derived:
        return derived
    public_base = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
    if public_base and not is_placeholder_url(public_base):
        return f"{public_base}/custom-llm"
    return PLACEHOLDER_CUSTOM_LLM_URL


def load_assistant_template(path: Path = ASSISTANT_TEMPLATE) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def assistant_payload(webhook_url: str | None = None) -> dict[str, Any]:
    payload = load_assistant_template()
    url = webhook_url or webhook_url_from_env() or payload.get("server", {}).get("url") or PLACEHOLDER_URL
    payload["server"] = {"url": url}
    if payload.get("model", {}).get("provider") == "custom-llm":
        payload["model"]["url"] = custom_llm_url_from_env_or_webhook(url, prefer_env=webhook_url is None)
    payload.pop("serverUrl", None)
    return payload


def _ensure_live_ready(api_key: str, payload: dict[str, Any]) -> None:
    if not api_key:
        raise RuntimeError("Missing VAPI_API_KEY or VAPI_PRIVATE_KEY.")
    url = payload.get("server", {}).get("url", "")
    if is_placeholder_url(url):
        raise RuntimeError("Set VAPI_WEBHOOK_URL or PUBLIC_BASE_URL before making a live Vapi API call.")
    model_url = payload.get("model", {}).get("url", "")
    if payload.get("model", {}).get("provider") == "custom-llm" and is_placeholder_url(model_url):
        raise RuntimeError("Set VAPI_CUSTOM_LLM_URL or PUBLIC_BASE_URL before making a live custom-LLM Vapi API call.")


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


def list_phone_numbers(api_key: str, base_url: str | None = None) -> list[dict[str, Any]]:
    if not api_key:
        raise RuntimeError("Missing VAPI_API_KEY or VAPI_PRIVATE_KEY.")
    response = httpx.get(
        f"{(base_url or vapi_base_url_from_env()).rstrip('/')}/phone-number",
        headers=auth_headers(api_key),
        timeout=30,
    )
    response.raise_for_status()
    body = response.json()
    if isinstance(body, list):
        return body
    if isinstance(body, dict) and isinstance(body.get("results"), list):
        return body["results"]
    raise RuntimeError("Unexpected Vapi phone-number list response.")


def phone_number_id_from_env_or_single(api_key: str) -> str:
    explicit = os.getenv("VAPI_PHONE_NUMBER_ID", "")
    if explicit:
        return explicit
    phone_numbers = list_phone_numbers(api_key)
    if len(phone_numbers) == 1 and phone_numbers[0].get("id"):
        return str(phone_numbers[0]["id"])
    if not phone_numbers:
        raise RuntimeError("No Vapi phone numbers found; create one in Vapi before assigning PhoneBio.")
    raise RuntimeError("Multiple Vapi phone numbers found; set VAPI_PHONE_NUMBER_ID explicitly.")


def redacted_phone_number_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": record.get("id"),
        "provider": record.get("provider"),
        "assistantIdSet": bool(record.get("assistantId")),
        "createdAt": record.get("createdAt"),
        "updatedAt": record.get("updatedAt"),
        "numberPresent": bool(record.get("number") or record.get("fallbackDestination", {}).get("number")),
    }


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
