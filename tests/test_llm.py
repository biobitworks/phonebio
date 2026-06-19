"""Offline-safe tests for the LLM router and custom-LLM endpoint (no network)."""
from __future__ import annotations

from fastapi.testclient import TestClient

from fieldbio import llm
from fieldbio.app import app

client = TestClient(app)


def test_provider_order_respects_keys(monkeypatch):
    monkeypatch.setattr(llm.settings, "provider_order", ["local", "paid-cloud"])
    names = [p.name for p in llm.providers()]
    assert names == ["local"]  # cloud names are ignored; no paid fallback path


def test_custom_llm_non_stream(monkeypatch):
    monkeypatch.setattr(
        llm, "chat", lambda *a, **k: llm.ChatResult("local", "qwen2.5:1.5b", "Stop and ventilate.", 12)
    )
    r = client.post("/custom-llm/chat/completions", json={"messages": [{"role": "user", "content": "hi"}]})
    assert r.status_code == 200
    body = r.json()
    assert body["choices"][0]["message"]["content"] == "Stop and ventilate."
    assert body["x_provider"] == "local"


def test_custom_llm_stream(monkeypatch):
    monkeypatch.setattr(llm, "stream_chat", lambda *a, **k: iter([("local", "ven"), ("local", "tilate")]))
    r = client.post(
        "/custom-llm/chat/completions",
        json={"messages": [{"role": "user", "content": "hi"}], "stream": True},
    )
    assert r.status_code == 200
    assert "ven" in r.text
    assert "tilate" in r.text
    assert "[DONE]" in r.text
