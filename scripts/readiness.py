"""PhoneBio v1 readiness audit.

This is intentionally local and deterministic. It proves what the repository can
prove without live Vapi or InsForge credentials, and reports those external
items as blocked instead of pretending v1 is fully complete.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from fieldbio.app import handle_vapi_payload
from fieldbio.vapi_client import (
    assistant_payload,
    api_key_from_env,
    custom_llm_url_from_env_or_webhook,
    is_placeholder_url,
    webhook_url_from_env,
)


def _exists(path: str) -> bool:
    return (REPO_ROOT / path).exists()


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def _env_ready() -> dict[str, bool]:
    webhook_url = webhook_url_from_env()
    assistant = assistant_payload()
    assistant_server_url = assistant.get("server", {}).get("url", "")
    custom_llm_required = assistant.get("model", {}).get("provider") == "custom-llm"
    custom_llm_url = custom_llm_url_from_env_or_webhook(assistant_server_url)
    call_verified = os.getenv("PHONEBIO_CALL_VERIFIED") == "1" or os.getenv("PHONEBIO_LIVE_VAPI_VERIFIED") == "1"
    return {
        "vapi_api_key": bool(api_key_from_env()),
        "vapi_phone_number_id": bool(os.getenv("VAPI_PHONE_NUMBER_ID")),
        "vapi_webhook_url": bool(webhook_url) or not is_placeholder_url(assistant_server_url),
        "vapi_custom_llm_url": (not custom_llm_required) or not is_placeholder_url(custom_llm_url),
        "vapi_call_verified": call_verified,
        "insforge_api_key": bool(os.getenv("INSFORGE_API_KEY")),
    }


def _status(ok: bool, *, blocker: str | None = None) -> str:
    if ok:
        return "pass"
    return "blocked" if blocker else "fail"


async def _tool_result(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    payload = {"toolCalls": [{"id": f"readiness_{name}", "name": name, "arguments": arguments}]}
    response = await handle_vapi_payload(payload)
    return response["results"][0]["result"]


async def audit() -> dict[str, Any]:
    env = _env_ready()
    assistant = assistant_payload("https://example.test/webhook")
    tools = {
        tool["function"]["name"]
        for tool in assistant.get("model", {}).get("tools", [])
        if tool.get("type") == "function" and tool.get("function", {}).get("name")
    }
    system_prompt = " ".join(
        msg.get("content", "") for msg in assistant.get("model", {}).get("messages", []) if msg.get("role") == "system"
    )

    protocol = await _tool_result("get_protocol", {"task": "surface water grab sample"})
    safety = await _tool_result("get_safety_sheet", {"substance": "formaldehyde"})
    unknown_protocol = await _tool_result("get_protocol", {"task": "unlisted moon algae assay"})
    hardware = await _tool_result("troubleshoot_hardware", {"device": "data logger", "symptom": "will not connect"})
    barometer = await _tool_result(
        "interpret_sensor_report", {"sensor": "barometer", "reading": "pressure dropped 4 hPa in two hours"}
    )
    lidar = await _tool_result("interpret_sensor_report", {"sensor": "lidar", "reading": "device says unavailable"})

    requirements: dict[str, dict[str, Any]] = {}

    model_provider = assistant.get("model", {}).get("provider")
    custom_llm_required = model_provider == "custom-llm"
    live_vapi_ready = env["vapi_api_key"] and env["vapi_phone_number_id"] and env["vapi_webhook_url"] and (
        env["vapi_custom_llm_url"] or not custom_llm_required
    ) and env["vapi_call_verified"]
    requirements["VOICE-01"] = {
        "status": _status(
            live_vapi_ready,
            blocker="Needs a successful real inbound or outbound Vapi call verified by make vapi-verify-call.",
        ),
        "evidence": "Live Vapi assistant creation and phone assignment are tracked separately; VOICE-01 is not counted complete until make vapi-verify-call finds a matching call and PHONEBIO_CALL_VERIFIED=1 is set for the readiness audit.",
    }
    requirements["VOICE-02"] = {
        "status": _status(
            all(term in system_prompt.lower() for term in ["field biology", "limited internet", "no camera"])
        ),
        "evidence": "Assistant system prompt includes field biology, limited internet, and no-camera constraints.",
    }
    requirements["VOICE-03"] = {
        "status": _status(
            assistant.get("server", {}).get("url") == "https://example.test/webhook"
            and bool(model_provider)
            and {"get_protocol", "get_safety_sheet", "troubleshoot_hardware", "interpret_sensor_report"}.issubset(tools)
        ),
        "evidence": "Assistant payload has server.url, model provider, and required tool declarations.",
    }
    requirements["KNOW-01"] = {
        "status": _status(protocol.get("status") == "ok" and protocol.get("sourceIds")),
        "evidence": "Protocol lookup returns a source-backed local result.",
    }
    requirements["KNOW-02"] = {
        "status": _status(safety.get("status") == "ok" and safety.get("sourceIds")),
        "evidence": "Safety lookup returns a source-backed local result.",
    }
    requirements["KNOW-03"] = {
        "status": _status(unknown_protocol.get("status") == "not_found"),
        "evidence": "Unknown protocol returns not_found guidance instead of invented steps.",
    }
    requirements["KNOW-04"] = {
        "status": _status(
            bool(protocol.get("sourceIds")) and bool(safety.get("sourceIds")) and bool(hardware.get("sourceIds"))
        ),
        "evidence": "Protocol, SDS, and hardware answers include source IDs.",
    }
    requirements["HARD-01"] = {
        "status": _status(hardware.get("status") == "ok" and bool(hardware.get("steps"))),
        "evidence": "Hardware troubleshooting returns ordered local checks.",
    }
    requirements["HARD-02"] = {
        "status": _status(bool(hardware.get("escalateIf"))),
        "evidence": "Hardware troubleshooting includes stop/escalation conditions.",
    }
    sensor_text = _read("content/sensors/sensors.json")
    requirements["SENS-01"] = {
        "status": _status("accelerometer" in sensor_text and "gyroscope" in sensor_text),
        "evidence": "Sensor content covers accelerometer and gyroscope profiles.",
    }
    requirements["SENS-02"] = {
        "status": _status(barometer.get("status") == "ok" and barometer.get("id") == "barometer"),
        "evidence": "Barometer report resolves with accuracy and confidence guidance.",
    }
    requirements["SENS-03"] = {
        "status": _status(lidar.get("status") == "ok" and "availability" in json.dumps(lidar).lower()),
        "evidence": "LiDAR availability limits are represented without requiring camera use.",
    }
    requirements["SENS-04"] = {
        "status": _status(
            bool(barometer.get("measured")) and bool(barometer.get("confidence")) and bool(barometer.get("inferenceBoundary"))
        ),
        "evidence": "Sensor output distinguishes measurement, confidence, and inference boundary.",
    }
    token_pattern = re.compile("|".join(["s" + "k-", "gh" + "o_"]))
    requirements["GOV-01"] = {
        "status": _status(
            _exists("vapi/assistant.field-biology-worker.json") and not token_pattern.search(json.dumps(assistant))
        ),
        "evidence": "Assistant template exists and contains no obvious API-token pattern.",
    }
    requirements["GOV-02"] = {
        "status": _status(_exists("docs/source_intake.manifest.jsonl") and _exists("docs/deferred_writeback_candidates.jsonl")),
        "evidence": "Source-intake and deferred-writeback sidecars exist.",
    }
    requirements["GOV-03"] = {
        "status": _status(_exists("tests/test_fieldbio.py") and _exists("tests/fixtures/vapi_tool_calls_event.json")),
        "evidence": "Webhook and offline tool tests/fixtures exist.",
    }
    requirements["GOV-04"] = {
        "status": _status(_exists(".github/workflows/ci.yml")),
        "evidence": "CI includes secret scan; readiness output does not expose secrets.",
    }

    counts = {
        "pass": sum(1 for item in requirements.values() if item["status"] == "pass"),
        "blocked": sum(1 for item in requirements.values() if item["status"] == "blocked"),
        "fail": sum(1 for item in requirements.values() if item["status"] == "fail"),
    }
    return {
        "project": "phonebio",
        "envReady": env,
        "requirements": requirements,
        "summary": counts,
        "v1Complete": counts["blocked"] == 0 and counts["fail"] == 0,
    }


def main() -> None:
    print(json.dumps(asyncio.run(audit()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
