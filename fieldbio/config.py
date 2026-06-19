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

    # llm routing (offline-first)
    provider_order = _split_csv(os.getenv("LLM_PROVIDER_ORDER", "local,nebius,openai"))

    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")

    nebius_api_key = os.getenv("NEBIUS_API_KEY", "")
    nebius_base_url = os.getenv("NEBIUS_BASE_URL", "https://api.studio.nebius.com/v1/")
    nebius_model = os.getenv("NEBIUS_MODEL", "Qwen/Qwen3-30B-A3B")

    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


settings = Settings()
