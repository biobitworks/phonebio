from fieldbio.app import handle_vapi_payload
from fieldbio.shorthand import compress


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


def test_shorthand_compresses_field_note():
    result = compress("Observed approximately 12 cm water sample at north transect")
    assert result["compression_ratio"] < 1
    assert result["measurements"][0]["unit"] == "cm"


def get_result(payload):
    import asyncio

    response = asyncio.run(handle_vapi_payload(payload))
    return response["results"][0]["result"]
