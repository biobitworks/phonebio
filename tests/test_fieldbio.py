import json
from pathlib import Path

from fieldbio.app import handle_vapi_payload
from fieldbio.config import settings
from fieldbio.shorthand import compress, expand_field_line

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


def test_sensor_lookup_prefers_exact_sensor_id():
    result = get_result(
        {
            "toolCalls": [
                {
                    "id": "call_lidar",
                    "name": "interpret_sensor_report",
                    "arguments": {"sensor": "lidar", "reading": "device says unavailable"},
                }
            ]
        }
    )
    assert result["status"] == "ok"
    assert result["id"] == "lidar"
    assert "Only some phones" in result["availability"]


def test_sensor_lookup_handles_acoustic_context():
    result = get_result(
        {
            "toolCalls": [
                {
                    "id": "call_audio",
                    "name": "interpret_sensor_report",
                    "arguments": {"sensor": "microphone", "reading": "two voices and loud vibration near centrifuge"},
                }
            ]
        }
    )
    assert result["status"] == "ok"
    assert result["id"] == "acoustic_context"
    assert "Do not claim exact speaker count" in result["voiceGuidance"]


def test_sensor_lookup_handles_gesture_pocket_context():
    result = get_result(
        {
            "toolCalls": [
                {
                    "id": "call_gesture",
                    "name": "interpret_sensor_report",
                    "arguments": {"sensor": "gesture", "reading": "phone is in pocket, repeated double tap"},
                }
            ]
        }
    )
    assert result["status"] == "ok"
    assert result["id"] == "gesture_context"
    assert "pocket" in result["voiceGuidance"].lower()


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


def test_environment_risk_flags_biohazard_and_possible_multiple_speakers():
    result = get_result(
        {
            "toolCalls": [
                {
                    "id": "call_risk",
                    "name": "assess_environment_risk",
                    "arguments": {
                        "hazard": "biohazard spill with formaldehyde",
                        "audio": "two voices overlapping and loud machinery",
                        "vibration": "centrifuge vibration",
                        "connectivity": "voice only, data down",
                        "phonePlacement": "pocket",
                        "description": "Biohazard spill near centrifuge, possible exposure, two voices, phone in pocket.",
                    },
                }
            ]
        }
    )
    assert result["status"] == "ok"
    assert result["riskLevel"] == "high"
    assert result["peopleSignal"] == "possible_multiple_speakers_or_bystanders"
    assert "exact speaker count" in result["inferenceBoundary"]


def test_public_alert_context_is_context_only_offline():
    result = get_result(
        {
            "toolCalls": [
                {
                    "id": "call_alerts",
                    "name": "get_public_alert_context",
                    "arguments": {"country": "US", "hazardHint": "wildfire smoke", "offline": True},
                }
            ]
        }
    )
    assert result["status"] == "ok"
    assert result["alerts"][0]["source"] == "demo-static"
    assert "context only" in result["actions"][0]
    assert "not as a substitute" in result["inferenceBoundary"]


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
    assert "observed" in result["voice_readback"]


def test_shorthand_lab_jargon_round_trips_for_voice_readback():
    result = compress("Aliquot 20 ul buffer with the micropipette and run a negative control")
    assert result["compression_ratio"] < 0.8
    assert result["measurements"][0]["unit"] == "ul"
    assert "aliquot" in result["voice_readback"]
    assert "micropipette" in result["voice_readback"]
    assert "negative control" in result["voice_readback"]
    assert expand_field_line(result["field_line"], result["token_map"]) == result["voice_readback"]


def test_compress_observation_preserves_location_and_magnetometer_context():
    result = get_result(
        {
            "toolCalls": [
                {
                    "id": "call_context",
                    "name": "compress_observation",
                    "arguments": {
                        "text": "Biohazard note near transect alpha, phone in pocket, data down.",
                        "latitude": 37.8715,
                        "longitude": -122.273,
                        "locationAccuracyMeters": 8,
                        "barometricPressureHpa": 1004.2,
                        "magneticHeadingDegrees": 278,
                        "magneticFieldMicrotesla": "43, -12, 8",
                        "phonePlacement": "pocket",
                        "connectivity": "voice_only",
                    },
                }
            ]
        }
    )
    assert result["status"] == "ok"
    assert result["sensorContext"]["latitude"] == 37.8715
    assert result["sensorContext"]["magneticHeadingDegrees"] == 278
    assert "magnetic moment" in result["magnetometerBoundary"]


def get_result(payload):
    import asyncio

    response = asyncio.run(handle_vapi_payload(payload))
    return response["results"][0]["result"]


def load_fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))
