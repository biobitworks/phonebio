import json
from pathlib import Path

from fieldbio.app import handle_vapi_payload
from fieldbio.config import settings
from fieldbio.shorthand import compress

FIXTURES = Path(__file__).parent / "fixtures"


def test_protocol_lookup():
    result = get_result(
        {
            "message": {
                "toolCalls": [
                    {
                        "id": "call_protocol",
                        "function": {
                            "name": "get_protocol",
                            "arguments": {"task": "surface water grab sample"},
                        },
                    }
                ]
            }
        }
    )
    assert result["status"] == "ok"
    assert "water" in result["title"].lower()
    assert result["sourceIds"]


def test_safety_lookup_keeps_disclaimer():
    result = get_result(
        {
            "toolCalls": [
                {
                    "id": "call_sds",
                    "name": "get_safety_sheet",
                    "arguments": '{"substance":"formaldehyde"}',
                }
            ]
        }
    )
    assert result["status"] == "ok"
    assert "NOT the authoritative Safety Data Sheet" in result["disclaimer"]


def test_vapi_tool_calls_event_shape():
    result = get_result(
        {
            "message": {
                "type": "tool-calls",
                "toolCalls": [
                    {
                        "id": "call_event",
                        "function": {
                            "name": "get_protocol",
                            "arguments": '{"task":"pitfall trap setup"}',
                        },
                    }
                ],
            }
        }
    )
    assert result["status"] == "ok"
    assert "pitfall" in result["title"].lower()


def test_vapi_tool_calls_fixture_through_http():
    from fastapi.testclient import TestClient
    from fieldbio.app import app

    payload = load_fixture("vapi_tool_calls_event.json")
    client = TestClient(app)

    response = client.post("/webhook", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["results"][0]["toolCallId"] == "fixture_tool_calls_protocol"
    assert body["results"][0]["result"]["status"] == "ok"
    assert "water" in body["results"][0]["result"]["title"].lower()


def test_vapi_tool_call_list_fixture_through_http():
    from fastapi.testclient import TestClient
    from fieldbio.app import app

    payload = load_fixture("vapi_tool_call_list_event.json")
    client = TestClient(app)

    response = client.post("/webhook", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["results"][0]["toolCallId"] == "fixture_tool_call_list_sensor"
    assert body["results"][0]["result"]["status"] == "ok"
    assert body["results"][0]["result"]["id"] == "barometer"


def test_unknown_hardware_does_not_hallucinate():
    result = get_result(
        {
            "toolCalls": [
                {
                    "id": "call_unknown",
                    "name": "troubleshoot_hardware",
                    "arguments": {"device": "unlisted spectrometer"},
                }
            ]
        }
    )
    assert result["status"] == "not_found"
    assert "Power down" in result["answer"]


def test_webhook_auth_when_secret_configured(monkeypatch):
    from fastapi.testclient import TestClient
    from fieldbio.app import app

    monkeypatch.setattr(settings, "webhook_secret", "test-webhook-secret")
    client = TestClient(app)
    payload = {"toolCalls": [{"id": "call_auth", "name": "get_protocol", "arguments": {"task": "water sample"}}]}

    rejected = client.post("/webhook", json=payload)
    assert rejected.status_code == 401

    accepted = client.post("/webhook", json=payload, headers={"authorization": "Bearer test-webhook-secret"})
    assert accepted.status_code == 200
    assert accepted.json()["results"][0]["result"]["status"] == "ok"


def test_shorthand_compresses_field_note():
    result = compress("Observed approximately 12 cm water sample at north transect")
    assert result["compression_ratio"] < 1
    assert result["measurements"][0]["unit"] == "cm"


def get_result(payload):
    import asyncio

    response = asyncio.run(handle_vapi_payload(payload))
    return response["results"][0]["result"]


def load_fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))
