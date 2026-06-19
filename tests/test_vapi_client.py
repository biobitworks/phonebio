import httpx

import fieldbio.vapi_client as vapi_client
from fieldbio.vapi_client import (
    api_key_from_env,
    assistant_payload,
    outbound_call_payload,
    phone_assignment_payload,
    redacted_call_record,
    redacted_phone_number_record,
    verify_recent_call,
    vapi_preflight,
)


def test_vapi_private_key_takes_priority_over_generic_api_key(monkeypatch):
    monkeypatch.setenv("VAPI_API_KEY", "wrong-public-or-stale-key")
    monkeypatch.setenv("VAPI_PRIVATE_KEY", "sk-private")

    assert api_key_from_env() == "sk-private"


def test_assistant_payload_uses_current_server_shape():
    payload = assistant_payload("https://example.test/webhook")
    assert payload["server"]["url"] == "https://example.test/webhook"
    assert payload["model"]["provider"] in {"custom-llm", "google"}
    if payload["model"]["provider"] == "custom-llm":
        assert payload["model"]["url"] == "https://example.test/custom-llm"
    else:
        assert payload["model"]["model"]
    assert "serverUrl" not in payload


def test_phone_assignment_payload_can_include_server_url():
    payload = phone_assignment_payload("asst_123", "https://example.test/webhook")
    assert payload == {
        "assistantId": "asst_123",
        "server": {"url": "https://example.test/webhook"},
    }


def test_outbound_call_payload_shape():
    payload = outbound_call_payload("asst_123", "pn_123", "REDACTED_E164")
    assert payload["assistantId"] == "asst_123"
    assert payload["phoneNumberId"] == "pn_123"
    assert payload["customer"]["number"] == "REDACTED_E164"


def test_phone_number_redaction_does_not_return_raw_number():
    fake_number = "+" + "15555550123"
    redacted = redacted_phone_number_record(
        {
            "id": "pn_123",
            "provider": "vapi",
            "assistantId": "asst_123",
            "number": fake_number,
        }
    )

    assert redacted["id"] == "pn_123"
    assert redacted["assistantId"] == "asst_123"
    assert redacted["numberPresent"] is True
    assert fake_number not in str(redacted)


def test_call_redaction_does_not_return_transcript_or_customer_number():
    fake_number = "+" + "15555550123"
    transcript = "Caller said the centrifuge is vibrating."
    redacted = redacted_call_record(
        {
            "id": "call_123",
            "type": "inboundPhoneCall",
            "status": "ended",
            "assistantId": "asst_123",
            "phoneNumberId": "pn_123",
            "customer": {"number": fake_number},
            "messages": [{"role": "user", "message": transcript}],
            "artifact": {"transcript": transcript, "recordingUrl": "https://recording.example.test/private.wav"},
            "analysis": {"summary": "Caller asked for troubleshooting."},
        }
    )

    assert redacted["id"] == "call_123"
    assert redacted["customerNumberPresent"] is True
    assert redacted["messageCount"] == 1
    assert redacted["transcriptPresent"] is True
    assert redacted["recordingPresent"] is True
    assert fake_number not in str(redacted)
    assert transcript not in str(redacted)
    assert "recording.example.test" not in str(redacted)


def test_verify_recent_call_matches_assistant_and_phone():
    calls = [
        {"id": "call_other", "assistantId": "asst_other", "phoneNumberId": "pn_123"},
        {"id": "call_match", "assistantId": "asst_123", "phoneNumberId": "pn_123"},
    ]

    result = verify_recent_call(calls, "asst_123", "pn_123")

    assert result["verified"] is True
    assert result["matchingCount"] == 1
    assert result["matches"][0]["id"] == "call_match"


def test_verify_recent_call_reports_missing_match():
    result = verify_recent_call([{"id": "call_other", "assistantId": "asst_other"}], "asst_123", "pn_123")

    assert result["verified"] is False
    assert result["matchingCount"] == 0


def test_vapi_preflight_auto_selects_single_phone_number(monkeypatch):
    fake_number = "+" + "15555550123"
    monkeypatch.delenv("VAPI_PHONE_NUMBER_ID", raising=False)
    monkeypatch.setenv("VAPI_ASSISTANT_ID", "asst_123")
    monkeypatch.setattr(
        vapi_client,
        "list_phone_numbers",
        lambda api_key: [{"id": "pn_123", "provider": "vapi", "number": fake_number, "assistantId": "asst_123"}],
    )

    result = vapi_preflight(api_key="test-key", webhook_url="https://example.test/webhook")

    assert result["liveReady"] is True
    assert result["apiKey"]["source"] == "argument"
    assert result["assistantPayloadReady"] is True
    assert result["phoneSelection"]["source"] == "single-vapi-phone-number"
    assert result["phoneSelection"]["selectedPhoneNumberId"] == "pn_123"
    assert result["phoneSelection"]["selectedAssistantId"] == "asst_123"
    assert result["phoneSelection"]["expectedAssistantMatch"] is True
    assert fake_number not in str(result)


def test_vapi_preflight_reports_missing_explicit_phone_number(monkeypatch):
    monkeypatch.setenv("VAPI_PHONE_NUMBER_ID", "pn_missing")
    monkeypatch.delenv("VAPI_ASSISTANT_ID", raising=False)
    monkeypatch.setattr(
        vapi_client,
        "list_phone_numbers",
        lambda api_key: [{"id": "pn_123", "provider": "vapi", "assistantId": "asst_123"}],
    )

    result = vapi_preflight(api_key="test-key", webhook_url="https://example.test/webhook")

    assert result["liveReady"] is False
    assert result["phoneSelection"]["status"] == "fail"
    assert result["phoneSelection"]["selectedPhoneNumberId"] == "pn_missing"


def test_vapi_preflight_reports_unauthorized_without_key_value(monkeypatch):
    request = httpx.Request("GET", "https://api.vapi.ai/phone-number")
    response = httpx.Response(401, request=request)
    error = httpx.HTTPStatusError("unauthorized", request=request, response=response)
    monkeypatch.delenv("VAPI_PHONE_NUMBER_ID", raising=False)
    monkeypatch.setattr(vapi_client, "list_phone_numbers", lambda api_key: (_ for _ in ()).throw(error))

    result = vapi_preflight(api_key="secret-test-key", webhook_url="https://example.test/webhook")

    assert result["liveReady"] is False
    assert result["phoneNumbers"]["status"] == "fail"
    assert result["phoneNumbers"]["httpStatus"] == 401
    assert "secret-test-key" not in str(result)


def test_vapi_preflight_reports_private_key_source_without_value(monkeypatch):
    monkeypatch.setenv("VAPI_API_KEY", "generic-key")
    monkeypatch.setenv("VAPI_PRIVATE_KEY", "sk-private")
    monkeypatch.setattr(
        vapi_client,
        "list_phone_numbers",
        lambda api_key: [{"id": "pn_123", "provider": "vapi"}],
    )

    result = vapi_preflight(webhook_url="https://example.test/webhook")

    assert result["apiKey"]["source"] == "VAPI_PRIVATE_KEY"
    assert result["apiKey"]["shadowedSources"] == ["VAPI_API_KEY"]
    assert result["apiKey"]["startsWithSk"] is True
    assert "sk-private" not in str(result)
    assert "generic-key" not in str(result)
