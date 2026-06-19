import httpx
import pytest

import scripts.public_probe as public_probe
from scripts.public_probe import ProbeTarget, normalize_base_url, run_probe


def test_normalize_base_url_requires_absolute_http_url():
    assert normalize_base_url("https://example.test/") == "https://example.test"

    with pytest.raises(ValueError):
        normalize_base_url("example.test")


def test_probe_target_summarizes_webhook_response_without_secret_value():
    request = httpx.Request("POST", "https://example.test/webhook")
    response = httpx.Response(
        200,
        request=request,
        json={"results": [{"toolCallId": "probe", "result": {"status": "ok"}}]},
    )

    result = public_probe._result_from_response(
        ProbeTarget("webhook", "POST", "/webhook", 200),
        response,
    )

    assert result["ok"] is True
    assert result["resultStatus"] == "ok"
    assert "secret" not in str(result).lower()


def test_run_probe_reports_public_base_and_secret_presence(monkeypatch):
    def fake_probe_target(base_url, target, secret=""):
        return {"name": target.name, "path": target.path, "ok": True}

    monkeypatch.setattr(public_probe, "probe_target", fake_probe_target)

    result = run_probe("https://public.example.test/", "secret-token")

    assert result["ready"] is True
    assert result["baseUrl"] == {"scheme": "https", "host": "public.example.test"}
    assert result["secretHeaderSet"] is True
    assert [check["name"] for check in result["checks"]] == ["health", "webhook", "llm_health"]
    assert "secret-token" not in str(result)
