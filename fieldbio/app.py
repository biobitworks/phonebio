"""FastAPI webhook for Vapi custom tools."""
from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI, Header, HTTPException

from .config import settings
from .llm_api import router as llm_router
from .tools import TOOLS

app = FastAPI(title="PhoneBio", version="0.1.0")
# Offline-first LLM lane (local Ollama -> Nebius -> OpenAI): /llm/health and the
# optional Vapi custom-LLM endpoint. Deterministic tools stay on /webhook.
app.include_router(llm_router)


def _webhook_secret_enabled() -> bool:
    return bool(settings.webhook_secret and settings.webhook_secret != "change-me-long-random-string")


def _authorize_webhook(authorization: str | None, x_vapi_secret: str | None) -> None:
    if not _webhook_secret_enabled():
        return
    expected = settings.webhook_secret
    if authorization == f"Bearer {expected}" or x_vapi_secret == expected:
        return
    raise HTTPException(status_code=401, detail="Invalid webhook credential.")


def _tool_calls(payload: dict[str, Any]) -> list[dict[str, Any]]:
    message = payload.get("message", payload)
    calls = (
        message.get("toolCalls")
        or message.get("toolCallList")
        or payload.get("toolCalls")
        or payload.get("toolCallList")
        or []
    )
    return calls if isinstance(calls, list) else []


def _tool_name(call: dict[str, Any]) -> str:
    return (
        call.get("function", {}).get("name")
        or call.get("name")
        or call.get("toolName")
        or call.get("type")
        or ""
    )


def _tool_args(call: dict[str, Any]) -> dict[str, Any]:
    args = call.get("function", {}).get("arguments", call.get("arguments", call.get("args", {})))
    if isinstance(args, str):
        try:
            parsed = json.loads(args)
            return parsed if isinstance(parsed, dict) else {"description": args}
        except json.JSONDecodeError:
            return {"description": args}
    return args if isinstance(args, dict) else {}


async def handle_vapi_payload(payload: dict[str, Any]) -> dict[str, Any]:
    calls = _tool_calls(payload)
    if not calls:
        return {"status": "ignored", "message": "No tool calls found."}

    results = []
    for call in calls:
        name = _tool_name(call)
        tool = TOOLS.get(name)
        tool_call_id = call.get("id") or call.get("toolCallId") or name or "unknown"
        if not tool:
            results.append(
                {
                    "toolCallId": tool_call_id,
                    "result": {"status": "error", "answer": f"Unsupported tool: {name}"},
                }
            )
            continue
        results.append({"toolCallId": tool_call_id, "result": tool(_tool_args(call))})
    return {"results": results}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "phonebio-vapi-webhook"}


@app.post("/webhook")
async def webhook(
    payload: dict[str, Any],
    authorization: str | None = Header(default=None),
    x_vapi_secret: str | None = Header(default=None),
) -> dict[str, Any]:
    _authorize_webhook(authorization, x_vapi_secret)
    return await handle_vapi_payload(payload)
