"""Offline-first LLM router.

Tries providers in a configured order so the agent can reason on-device first
and only reach the network when allowed/available:

    local (Ollama, OpenAI-compatible)  ->  Nebius Token Factory  ->  OpenAI

This is the "processing is offline" lane: a field worker calls in, and the
brain runs against a local model with zero internet. Nebius is the drop-in
cloud upgrade once API credits land (same OpenAI-compatible interface).

The deterministic tool layer (fieldbio/tools.py) stays separate and pure; this
router only powers free-form reasoning / summarization and the optional
Vapi custom-LLM endpoint.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Iterator

from .config import settings

try:  # openai SDK is optional at import time
    from openai import OpenAI
except Exception:  # pragma: no cover - exercised only without the dep
    OpenAI = None  # type: ignore[assignment]


@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str
    api_key: str
    model: str
    offline: bool


@dataclass(frozen=True)
class ChatResult:
    provider: str
    model: str
    text: str
    latency_ms: int


def _catalog() -> dict[str, Provider]:
    return {
        # local needs no real key; the OpenAI client just requires a non-empty string
        "local": Provider("local", settings.ollama_base_url, "ollama", settings.ollama_model, True),
        "nebius": Provider("nebius", settings.nebius_base_url, settings.nebius_api_key, settings.nebius_model, False),
        "openai": Provider("openai", settings.openai_base_url, settings.openai_api_key, settings.openai_model, False),
    }


def providers() -> list[Provider]:
    """Configured providers in priority order (local always eligible)."""
    catalog = _catalog()
    out: list[Provider] = []
    for name in settings.provider_order:
        p = catalog.get(name)
        if not p:
            continue
        if p.name == "local" or p.api_key:
            out.append(p)
    return out


def _client(p: Provider, timeout: float):
    if OpenAI is None:
        raise RuntimeError("openai package not installed; run: pip install -r requirements.txt")
    return OpenAI(base_url=p.base_url, api_key=p.api_key, timeout=timeout)


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
            resp = _client(p, timeout).chat.completions.create(
                model=p.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            text = (resp.choices[0].message.content or "").strip()
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
            stream = _client(p, timeout).chat.completions.create(
                model=p.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    yield p.name, delta
            return
        except Exception as exc:
            errors.append(f"{p.name}: {type(exc).__name__}: {exc}")
            continue
    raise RuntimeError("All LLM providers failed (stream) -> " + " | ".join(errors or ["none configured"]))


def health() -> list[dict[str, Any]]:
    """Lightweight provider report. Pings local; reports cloud by config only."""
    report: list[dict[str, Any]] = []
    for p in providers():
        entry: dict[str, Any] = {"name": p.name, "model": p.model, "offline": p.offline}
        if p.name == "local":
            try:
                _client(p, timeout=3.0).models.list()
                entry["status"] = "reachable"
            except Exception as exc:
                entry["status"] = f"unreachable: {type(exc).__name__}"
        else:
            entry["status"] = "configured"
        report.append(entry)
    if not report:
        report.append({"name": "none", "status": "no providers configured", "model": None})
    return report
