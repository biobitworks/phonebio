import httpx

from scripts.hosted_function_probe import _response_summary, run_probe


def test_hosted_function_post_requires_object_result():
    response = httpx.Response(
        200,
        json={"results": [{"toolCallId": "hosted_probe_protocol", "result": {"status": "ok", "sourceIds": ["x"]}}]},
    )

    summary = _response_summary(response, method="POST")

    assert summary["ok"] is True
    assert summary["resultType"] == "dict"
    assert summary["sourceIdsPresent"] is True


def test_hosted_function_post_rejects_stringified_result():
    response = httpx.Response(
        200,
        json={"results": [{"toolCallId": "hosted_probe_protocol", "result": "{\"status\":\"ok\"}"}]},
    )

    summary = _response_summary(response, method="POST")

    assert summary["ok"] is False
    assert summary["resultType"] == "str"


def test_hosted_function_probe_rejects_non_absolute_url():
    assert run_probe("not-a-url") == {
        "ready": False,
        "error": "Assistant server URL must be absolute http(s).",
    }
