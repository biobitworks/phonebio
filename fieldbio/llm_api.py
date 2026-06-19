"""Optional OpenAI-compatible custom-LLM endpoint for Vapi.

Point a Vapi assistant's model at POST {PUBLIC_BASE_URL}/custom-llm/chat/completions
with provider "custom-llm" to run the conversation brain through the offline-first
router (local Ollama first, Nebius/OpenAI as upgrades). Deterministic tools stay
on the /webhook lane; this only handles free-form reasoning.
"""
from __future__ import annotations

import json
import time
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from . import llm

router = APIRouter()


@router.get("/llm/health")
def llm_health() -> dict[str, Any]:
    return {"providers": llm.health(), "order": llm.settings.provider_order}


def _completion(result: llm.ChatResult) -> dict[str, Any]:
    return {
        "id": f"phonebio-{int(time.time() * 1000)}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": result.model,
        "x_provider": result.provider,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": result.text},
                "finish_reason": "stop",
            }
        ],
    }


def _chunk(provider: str, model: str, delta: str, finish: str | None = None) -> str:
    payload = {
        "id": f"phonebio-{int(time.time() * 1000)}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "x_provider": provider,
        "choices": [{"index": 0, "delta": {"content": delta} if delta else {}, "finish_reason": finish}],
    }
    return f"data: {json.dumps(payload)}\n\n"


@router.post("/custom-llm/chat/completions")
async def custom_llm(req: Request):
    body = await req.json()
    messages = body.get("messages", [])
    temperature = float(body.get("temperature", 0.4))
    max_tokens = body.get("max_tokens") or body.get("maxTokens")

    if not body.get("stream", False):
        result = llm.chat(messages, temperature=temperature, max_tokens=max_tokens)
        return JSONResponse(_completion(result))

    def gen():
        provider = "unknown"
        model = "unknown"
        try:
            for prov, delta in llm.stream_chat(messages, temperature=temperature, max_tokens=max_tokens):
                provider = prov
                yield _chunk(provider, model, delta)
        except Exception as exc:  # surface a spoken error rather than a dead stream
            yield _chunk(provider, model, f"[router error: {exc}]")
        yield _chunk(provider, model, "", finish="stop")
        yield "data: [DONE]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
