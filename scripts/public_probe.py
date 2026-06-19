"""Probe a public PhoneBio deployment/tunnel without printing secrets."""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx


WEBHOOK_PAYLOAD = {
    "toolCalls": [
        {
            "id": "public_probe_protocol",
            "name": "get_protocol",
            "arguments": {"task": "surface water grab sample"},
        }
    ]
}


@dataclass(frozen=True)
class ProbeTarget:
    name: str
    method: str
    path: str
    expected_status: int
    json_body: dict[str, Any] | None = None


TARGETS = [
    ProbeTarget("health", "GET", "/health", 200),
    ProbeTarget("webhook", "POST", "/webhook", 200, WEBHOOK_PAYLOAD),
    ProbeTarget("llm_health", "GET", "/llm/health", 200),
]


def normalize_base_url(value: str) -> str:
    cleaned = value.strip().rstrip("/")
    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Base URL must be an absolute http(s) URL.")
    return cleaned


def _headers(secret: str) -> dict[str, str]:
    headers = {"content-type": "application/json"}
    if secret:
        headers["x-vapi-secret"] = secret
    return headers


def _result_from_response(target: ProbeTarget, response: httpx.Response) -> dict[str, Any]:
    item: dict[str, Any] = {
        "name": target.name,
        "method": target.method,
        "path": target.path,
        "statusCode": response.status_code,
        "ok": response.status_code == target.expected_status,
    }
    try:
        body = response.json()
    except json.JSONDecodeError:
        item["json"] = False
        return item
    item["json"] = True
    if target.name == "health":
        item["service"] = body.get("service")
    elif target.name == "webhook":
        item["resultStatus"] = body.get("results", [{}])[0].get("result", {}).get("status")
        item["toolCallId"] = body.get("results", [{}])[0].get("toolCallId")
    elif target.name == "llm_health":
        item["providers"] = [provider.get("name") for provider in body.get("providers", [])]
    return item


def probe_target(base_url: str, target: ProbeTarget, secret: str = "") -> dict[str, Any]:
    url = f"{base_url}{target.path}"
    try:
        response = httpx.request(
            target.method,
            url,
            headers=_headers(secret),
            json=target.json_body,
            timeout=15,
        )
    except httpx.HTTPError as error:
        return {
            "name": target.name,
            "method": target.method,
            "path": target.path,
            "ok": False,
            "error": error.__class__.__name__,
        }
    return _result_from_response(target, response)


def run_probe(base_url: str, secret: str = "") -> dict[str, Any]:
    normalized = normalize_base_url(base_url)
    parsed = urlparse(normalized)
    results = [probe_target(normalized, target, secret) for target in TARGETS]
    return {
        "baseUrl": {"scheme": parsed.scheme, "host": parsed.netloc},
        "secretHeaderSet": bool(secret),
        "checks": results,
        "ready": all(item.get("ok") for item in results),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Probe public PhoneBio webhook/custom-LLM reachability.")
    parser.add_argument("--base-url", default=os.getenv("PUBLIC_BASE_URL", ""))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        report = run_probe(args.base_url, os.getenv("VAPI_WEBHOOK_SECRET", ""))
    except ValueError as error:
        print(json.dumps({"ready": False, "error": str(error)}, indent=2, sort_keys=True))
        raise SystemExit(1)
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["ready"] else 1)


if __name__ == "__main__":
    main()
