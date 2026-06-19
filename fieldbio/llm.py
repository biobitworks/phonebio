"""LLM router.

The optional custom-LLM endpoint talks to local Ollama through a
chat-completions HTTP shape by default. Nebius Token Factory can be enabled
explicitly with free hackathon credits; it uses an OpenAI-compatible HTTP API
but does not use an OpenAI key.

The deterministic tool layer (fieldbio/tools.py) stays separate and pure; this
router only powers free-form reasoning / summarization and the optional
Vapi custom-LLM endpoint.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Iterator

import httpx

from .config import settings


@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str
    model: str
    offline: bool


@dataclass(frozen=True)
class ChatResult:
    provider: str
    model: str
    text: str
    latency_ms: int


def _catalog() -> dict[str, Provider]:
    catalog = {
        "local": Provider("local", settings.ollama_base_url, settings.ollama_model, True),
    }
    if settings.nebius_api_key:
        catalog["nebius"] = Provider("nebius", settings.nebius_base_url, settings.nebius_model, False)
    return catalog


def providers() -> list[Provider]:
    """Configured providers in priority order. Unknown/cloud names are ignored."""
    catalog = _catalog()
    out: list[Provider] = []
    for name in settings.provider_order:
        p = catalog.get(name)
        if p:
            out.append(p)
    return out


def _url(p: Provider, path: str) -> str:
    return f"{p.base_url.rstrip('/')}/{path.lstrip('/')}"


def _headers(p: Provider) -> dict[str, str]:
    headers = {"content-type": "application/json"}
    if p.name == "local":
        headers["authorization"] = "Bearer ollama"
    elif p.name == "nebius":
        headers["authorization"] = f"Bearer {settings.nebius_api_key}"
    return headers


def chat(
    messages: list[dict[str, Any]],
    *,
    temperature: float = 0.4,
    max_tokens: int | None = None,
    timeout: float = 30.0,
) -> ChatResult:
    """Return the first successful completion across the provider chain."""
    errors: list[str] = []
    for p in providers():
        started = time.time()
        try:
            payload = {"model": p.model, "messages": messages, "temperature": temperature}
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(_url(p, "/chat/completions"), headers=_headers(p), json=payload)
                resp.raise_for_status()
            body = resp.json()
            text = (body["choices"][0]["message"].get("content") or "").strip()
            return ChatResult(p.name, p.model, text, int((time.time() - started) * 1000))
        except Exception as exc:  # try the next provider
            errors.append(f"{p.name}: {type(exc).__name__}: {exc}")
            continue
    raise RuntimeError("All LLM providers failed -> " + " | ".join(errors or ["none configured"]))


def stream_chat(
    messages: list[dict[str, Any]],
    *,
    temperature: float = 0.4,
    max_tokens: int | None = None,
    timeout: float = 60.0,
) -> Iterator[tuple[str, str]]:
    """Yield (provider_name, text_delta) from the first provider that streams."""
    errors: list[str] = []
    for p in providers():
        try:
            payload = {"model": p.model, "messages": messages, "temperature": temperature, "stream": True}
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens
            with httpx.Client(timeout=timeout) as client:
                with client.stream("POST", _url(p, "/chat/completions"), headers=_headers(p), json=payload) as resp:
                    resp.raise_for_status()
                    for line in resp.iter_lines():
                        if not line.startswith("data: "):
                            continue
                        data = line.removeprefix("data: ").strip()
                        if data == "[DONE]":
                            return
                        chunk = json.loads(data)
                        choices = chunk.get("choices") or []
                        delta = choices[0].get("delta", {}).get("content") if choices else None
                        if delta:
                            yield p.name, delta
            return
        except Exception as exc:
            errors.append(f"{p.name}: {type(exc).__name__}: {exc}")
            continue
    raise RuntimeError("All LLM providers failed (stream) -> " + " | ".join(errors or ["none configured"]))


def health() -> list[dict[str, Any]]:
    """Lightweight provider report."""
    report: list[dict[str, Any]] = []
    for p in providers():
        entry: dict[str, Any] = {"name": p.name, "model": p.model, "offline": p.offline}
        try:
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(_url(p, "/models"), headers=_headers(p))
                resp.raise_for_status()
            entry["status"] = "reachable"
        except Exception as exc:
            entry["status"] = f"unreachable: {type(exc).__name__}"
        report.append(entry)
    if not report:
        report.append({"name": "none", "status": "no providers configured", "model": None})
    return report


def _strip_reasoning(value: Any) -> Any:
    """Remove model-private reasoning fields before returning responses to Vapi."""
    if isinstance(value, dict):
        return {key: _strip_reasoning(item) for key, item in value.items() if key != "reasoning"}
    if isinstance(value, list):
        return [_strip_reasoning(item) for item in value]
    return value


def _sanitize_sse_line(line: str) -> str:
    if not line.startswith("data: "):
        return line
    data = line.removeprefix("data: ").strip()
    if data == "[DONE]":
        return line
    try:
        return f"data: {json.dumps(_strip_reasoning(json.loads(data)), separators=(',', ':'))}"
    except json.JSONDecodeError:
        return line


def _primary() -> Provider:
    ps = providers()
    if not ps:
        raise RuntimeError("No local provider configured (set LLM_PROVIDER_ORDER=local).")
    return ps[0]


def raw_completion(body: dict[str, Any], *, timeout: float = 120.0) -> dict[str, Any]:
    """Forward a chat-completions request (messages + tools) to local Ollama and
    return the raw completion dict, including any tool_calls. Lets the offline
    model drive Vapi function calling via the custom-LLM endpoint."""
    p = _primary()
    payload = dict(body)
    payload["model"] = p.model  # force the local model; ignore caller's model name
    payload.pop("stream", None)
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(_url(p, "/chat/completions"), headers=_headers(p), json=payload)
        resp.raise_for_status()
    return _strip_reasoning(resp.json())


def raw_stream(body: dict[str, Any], *, timeout: float = 120.0) -> Iterator[bytes]:
    """Stream local Ollama's SSE bytes verbatim, forcing the local model."""
    p = _primary()
    payload = dict(body)
    payload["model"] = p.model
    payload["stream"] = True
    with httpx.Client(timeout=timeout) as client:
        with client.stream("POST", _url(p, "/chat/completions"), headers=_headers(p), json=payload) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line:
                    yield (_sanitize_sse_line(line) + "\n\n").encode()
