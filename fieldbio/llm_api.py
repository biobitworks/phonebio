"""Optional custom-LLM endpoint for Vapi.

Point a Vapi assistant's model at POST {PUBLIC_BASE_URL}/custom-llm/chat/completions
with provider "custom-llm" to run the conversation brain through local Ollama.
The endpoint forwards Vapi's chat-completions payload so tool declarations and
tool-call responses survive the round trip.
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse, StreamingResponse

from . import llm
from .auth import authorize_vapi_request

router = APIRouter()


@router.get("/llm/health")
def llm_health() -> dict[str, Any]:
    return {"providers": llm.health(), "order": llm.settings.provider_order}


@router.post("/custom-llm/chat/completions")
async def custom_llm(
    req: Request,
    authorization: str | None = Header(default=None),
    x_vapi_secret: str | None = Header(default=None),
):
    """Chat-completions endpoint Vapi points its custom-llm model at.

    Forwards messages + tool definitions to the local offline model and proxies
    the reply (content AND tool_calls) so the offline brain drives Vapi function
    calling for free. Deterministic tool execution stays on /webhook.
    """
    authorize_vapi_request(authorization, x_vapi_secret)
    body = await req.json()

    if not body.get("stream", False):
        return JSONResponse(llm.raw_completion(body))

    def gen():
        try:
            for chunk in llm.raw_stream(body):
                yield chunk
        except Exception as exc:  # keep the SSE stream well-formed on failure
            yield f"data: {json.dumps({'error': str(exc)})}\n\n".encode()
            yield b"data: [DONE]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
