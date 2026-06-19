from fieldbio.vapi_client import (
    assistant_payload,
    outbound_call_payload,
    phone_assignment_payload,
    redacted_phone_number_record,
)


def test_assistant_payload_uses_current_server_shape():
    payload = assistant_payload("https://example.test/webhook")
    assert payload["server"]["url"] == "https://example.test/webhook"
    assert payload["model"]["provider"] == "custom-llm"
    assert payload["model"]["url"] == "https://example.test/custom-llm"
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
    assert redacted["numberPresent"] is True
    assert fake_number not in str(redacted)
