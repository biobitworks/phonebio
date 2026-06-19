"""Configuration and path resolution for FieldBio.

Loads .env if present, exposes typed settings, and resolves the content
directory so the service runs file-local (offline) with zero external deps.
"""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # dotenv is optional at runtime
    pass

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = Path(os.getenv("CONTENT_DIR", REPO_ROOT / "content"))


def _split_csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


class Settings:
    # server
    port = int(os.getenv("PORT", "8080"))
    public_base_url = os.getenv("PUBLIC_BASE_URL", "")
    webhook_secret = os.getenv("VAPI_WEBHOOK_SECRET", "")

    # vapi
    vapi_api_key = os.getenv("VAPI_API_KEY", os.getenv("VAPI_PRIVATE_KEY", ""))
    vapi_phone_number_id = os.getenv("VAPI_PHONE_NUMBER_ID", "")
    vapi_base_url = os.getenv("VAPI_BASE_URL", "https://api.vapi.ai")

    # llm routing (offline-only by default)
    provider_order = _split_csv(os.getenv("LLM_PROVIDER_ORDER", "local"))

    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    ollama_model = os.getenv("OLLAMA_MODEL", "qwen3:1.7b")

    # Optional Nebius Token Factory route. Disabled unless NEBIUS_API_KEY is set
    # and "nebius" appears in LLM_PROVIDER_ORDER.
    nebius_api_key = os.getenv("NEBIUS_API_KEY", "")
    nebius_base_url = os.getenv("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1")
    nebius_model = os.getenv("NEBIUS_MODEL", "Qwen/Qwen3-30B-A3B-Instruct-2507")


settings = Settings()
