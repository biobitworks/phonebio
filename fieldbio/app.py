"""FastAPI webhook for Vapi custom tools."""
from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI, Header

from .auth import authorize_vapi_request
from .llm_api import router as llm_router
from .tools import TOOLS

app = FastAPI(title="PhoneBio", version="0.1.0")
# Offline LLM lane (local Ollama only): /llm/health and the optional Vapi
# custom-LLM endpoint. Deterministic tools stay on /webhook.
app.include_router(llm_router)


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
    authorize_vapi_request(authorization, x_vapi_secret)
    return await handle_vapi_payload(payload)
