"""Shared optional authentication for public Vapi-facing endpoints."""
from __future__ import annotations

from fastapi import HTTPException

from .config import settings


def webhook_secret_enabled() -> bool:
    return bool(settings.webhook_secret and settings.webhook_secret != "change-me-long-random-string")


def authorize_vapi_request(authorization: str | None, x_vapi_secret: str | None) -> None:
    if not webhook_secret_enabled():
        return
    expected = settings.webhook_secret
    if authorization == f"Bearer {expected}" or x_vapi_secret == expected:
        return
    raise HTTPException(status_code=401, detail="Invalid Vapi credential.")
