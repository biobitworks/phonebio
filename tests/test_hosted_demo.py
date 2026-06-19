import json

import httpx

import scripts.hosted_demo as hosted_demo


def test_decode_result_accepts_object_result():
    assert hosted_demo._decode_result({"status": "ok"}) == {"status": "ok"}


def test_decode_result_rejects_stringified_result_as_compatibility_fallback():
    assert hosted_demo._decode_result(json.dumps({"status": "ok"})) == {"status": "ok"}
    assert hosted_demo._decode_result("not json")["status"] == "error"


def test_hosted_demo_uses_vapi_tool_call_payloads(monkeypatch):
    calls = []

    def fake_post(url, json, timeout):
        calls.append(json)
        request = httpx.Request("POST", url, json=json)
        result = {"status": "ok", "id": "mock", "sourceIds": ["mock"]}
        return httpx.Response(
            200,
            request=request,
            json={"results": [{"toolCallId": json["message"]["toolCalls"][0]["id"], "result": result}]},
        )

    monkeypatch.setattr(hosted_demo.httpx, "post", fake_post)

    report = hosted_demo.run_hosted_demo("https://example.test/phonebio-vapi-webhook")

    assert report["summary"] == {"turns": 5, "passed": True}
    assert len(calls) == 5
    assert calls[0]["message"]["type"] == "tool-calls"
    assert calls[0]["message"]["toolCalls"][0]["function"]["name"] == "get_protocol"
