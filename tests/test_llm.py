"""Offline-safe tests for the LLM router and custom-LLM endpoint (no network)."""
from __future__ import annotations

import json

from fastapi.testclient import TestClient

from fieldbio import llm
from fieldbio.app import app
from fieldbio.config import settings

client = TestClient(app)


def test_provider_order_respects_keys(monkeypatch):
    monkeypatch.setattr(llm.settings, "provider_order", ["local", "paid-cloud"])
    names = [p.name for p in llm.providers()]
    assert names == ["local"]  # cloud names are ignored; no paid fallback path


def test_nebius_provider_requires_key(monkeypatch):
    monkeypatch.setattr(llm.settings, "provider_order", ["nebius", "local"])
    monkeypatch.setattr(llm.settings, "nebius_api_key", "")

    names = [p.name for p in llm.providers()]

    assert names == ["local"]


def test_nebius_provider_can_be_enabled_with_key(monkeypatch):
    monkeypatch.setattr(llm.settings, "provider_order", ["nebius", "local"])
    monkeypatch.setattr(llm.settings, "nebius_api_key", "test-nebius-key")
    monkeypatch.setattr(llm.settings, "nebius_base_url", "https://api.tokenfactory.nebius.com/v1")
    monkeypatch.setattr(llm.settings, "nebius_model", "Qwen/Qwen3-30B-A3B-Instruct-2507")

    providers = llm.providers()

    assert [p.name for p in providers] == ["nebius", "local"]
    assert providers[0].base_url == "https://api.tokenfactory.nebius.com/v1"
    assert providers[0].model == "Qwen/Qwen3-30B-A3B-Instruct-2507"
    assert providers[0].offline is False


def test_nebius_headers_use_nebius_key_not_openai(monkeypatch):
    monkeypatch.setattr(llm.settings, "nebius_api_key", "test-nebius-key")
    provider = llm.Provider("nebius", "https://api.tokenfactory.nebius.com/v1", "model", False)

    headers = llm._headers(provider)

    assert headers["authorization"] == "Bearer test-nebius-key"
    assert "OPENAI" not in str(headers)


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


def test_custom_llm_auth_when_secret_configured(monkeypatch):
    monkeypatch.setattr(settings, "webhook_secret", "test-webhook-secret")
    monkeypatch.setattr(llm, "raw_completion", lambda body: {"choices": [{"message": {"content": "ok"}}]})

    rejected = client.post("/custom-llm/chat/completions", json={"messages": []})
    assert rejected.status_code == 401

    accepted = client.post(
        "/custom-llm/chat/completions",
        json={"messages": []},
        headers={"authorization": "Bearer test-webhook-secret"},
    )
    assert accepted.status_code == 200


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
