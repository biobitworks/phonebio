"""Probe the hosted InsForge Vapi function selected by the assistant template."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
ASSISTANT_TEMPLATE = REPO_ROOT / "vapi" / "assistant.field-biology-worker.json"

PROBE_PAYLOAD = {
    "message": {
        "type": "tool-calls",
        "toolCalls": [
            {
                "id": "hosted_probe_protocol",
                "function": {
                    "name": "get_protocol",
                    "arguments": json.dumps({"task": "surface water grab sample"}),
                },
            }
        ],
    }
}


def assistant_server_url() -> str:
    template = json.loads(ASSISTANT_TEMPLATE.read_text(encoding="utf-8"))
    return str(template.get("server", {}).get("url", ""))


def _response_summary(response: httpx.Response, *, method: str) -> dict[str, Any]:
    summary: dict[str, Any] = {"method": method, "statusCode": response.status_code, "json": False}
    try:
        body = response.json()
    except json.JSONDecodeError:
        return summary
    summary["json"] = True
    if method == "GET":
        summary["status"] = body.get("status")
        summary["service"] = body.get("service")
        summary["ok"] = response.status_code == 200 and body.get("status") == "ok"
        return summary
    first = (body.get("results") or [{}])[0]
    result = first.get("result")
    summary.update(
        {
            "toolCallId": first.get("toolCallId"),
            "resultType": type(result).__name__,
            "resultStatus": result.get("status") if isinstance(result, dict) else None,
            "sourceIdsPresent": bool(result.get("sourceIds")) if isinstance(result, dict) else False,
            "ok": response.status_code == 200
            and first.get("toolCallId") == "hosted_probe_protocol"
            and isinstance(result, dict)
            and result.get("status") == "ok",
        }
    )
    return summary


def run_probe(url: str) -> dict[str, Any]:
    if not url.startswith(("http://", "https://")):
        return {"ready": False, "error": "Assistant server URL must be absolute http(s)."}
    checks = []
    try:
        checks.append(_response_summary(httpx.get(url, timeout=20), method="GET"))
        checks.append(_response_summary(httpx.post(url, json=PROBE_PAYLOAD, timeout=20), method="POST"))
    except httpx.HTTPError as error:
        return {"ready": False, "urlSet": True, "error": error.__class__.__name__}
    return {"ready": all(item.get("ok") for item in checks), "urlSet": True, "checks": checks}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Probe hosted PhoneBio InsForge Vapi function.")
    parser.add_argument("--url", default=assistant_server_url())
    return parser


def main() -> None:
    args = build_parser().parse_args()
    report = run_probe(args.url)
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report.get("ready") else 1)


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT))
    main()
