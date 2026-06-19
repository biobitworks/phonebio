"""Offline-safe tests for the LLM router and custom-LLM endpoint (no network)."""
from __future__ import annotations

import json

from fastapi.testclient import TestClient

from fieldbio import llm
from fieldbio.app import app

client = TestClient(app)


def test_provider_order_respects_keys(monkeypatch):
    monkeypatch.setattr(llm.settings, "provider_order", ["local", "paid-cloud"])
    names = [p.name for p in llm.providers()]
    assert names == ["local"]  # cloud names are ignored; no paid fallback path


def test_custom_llm_non_stream(monkeypatch):
    def fake_raw_completion(body):
        return {
            "model": "qwen3:1.7b",
            "choices": [{"message": {"content": "Stop and ventilate.", "tool_calls": body.get("tools", [])}}],
        }

    monkeypatch.setattr(llm, "raw_completion", fake_raw_completion)
    r = client.post(
        "/custom-llm/chat/completions",
        json={"messages": [{"role": "user", "content": "hi"}], "tools": [{"type": "function"}]},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["choices"][0]["message"]["content"] == "Stop and ventilate."
    assert body["choices"][0]["message"]["tool_calls"] == [{"type": "function"}]


def test_custom_llm_stream(monkeypatch):
    monkeypatch.setattr(llm, "raw_stream", lambda *a, **k: iter([b"data: ven\n\n", b"data: tilate\n\n"]))
    r = client.post(
        "/custom-llm/chat/completions",
        json={"messages": [{"role": "user", "content": "hi"}], "stream": True},
    )
    assert r.status_code == 200
    assert "ven" in r.text
    assert "tilate" in r.text


def test_llm_response_sanitizer_removes_reasoning_but_keeps_tool_calls():
    response = {
        "choices": [
            {
                "message": {
                    "content": "",
                    "reasoning": "private chain-of-thought",
                    "tool_calls": [{"function": {"name": "get_protocol", "arguments": "{}"}}],
                }
            }
        ]
    }

    sanitized = llm._strip_reasoning(response)

    assert "reasoning" not in sanitized["choices"][0]["message"]
    assert sanitized["choices"][0]["message"]["tool_calls"][0]["function"]["name"] == "get_protocol"


def test_llm_sse_sanitizer_removes_reasoning_delta():
    line = 'data: {"choices":[{"delta":{"reasoning":"private","content":"ok"}}]}'

    sanitized = llm._sanitize_sse_line(line)
    payload = json.loads(sanitized.removeprefix("data: "))

    assert "reasoning" not in payload["choices"][0]["delta"]
    assert payload["choices"][0]["delta"]["content"] == "ok"
