from fieldbio.vapi_client import assistant_payload, outbound_call_payload, phone_assignment_payload


def test_assistant_payload_uses_current_server_shape():
    payload = assistant_payload("https://example.test/webhook")
    assert payload["server"]["url"] == "https://example.test/webhook"
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
