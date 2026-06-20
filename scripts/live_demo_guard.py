#!/usr/bin/env python3
"""Fast read-only guard for keeping the live PhoneBio demo green.

This is intentionally lighter than scripts/preflight.py and make demo-stress:
it does not redeploy, repair, place calls, or spend Vapi outbound credits. It
checks the live surfaces that can drift during a presentation and reports the
optional Claude/Ollarma lane as a warning when degraded.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DASHBOARD = "https://qfdp5nuv.insforge.site/live.html"
PUBLIC_EDGE = "https://qfdp5nuv.insforge.site/edge.html"
LLM_URL = "https://qfdp5nuv.function2.insforge.app/phonebio-llm/chat/completions"
WEBHOOK_URL = "https://qfdp5nuv.function2.insforge.app/phonebio-vapi-webhook"
OLLARMA_READINESS = "http://127.0.0.1:8484/startup/readiness"
WATCHTOWER_BRIDGE = "http://127.0.0.1:8002/api/ollarma/bridge-status"
EXPECTED_TOOLS = {
    "compress_observation",
    "get_protocol",
    "get_safety_sheet",
    "interpret_sensor_report",
    "troubleshoot_hardware",
}
LLM_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_protocol",
            "description": "Retrieve a local field biology protocol by task, organism, hazard, or description.",
            "parameters": {"type": "object", "properties": {"task": {"type": "string"}, "hazard": {"type": "string"}, "description": {"type": "string"}}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_safety_sheet",
            "description": "Retrieve a local safety-material summary by substance, hazard, or description.",
            "parameters": {"type": "object", "properties": {"substance": {"type": "string"}, "hazard": {"type": "string"}, "description": {"type": "string"}}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "troubleshoot_hardware",
            "description": "Return local troubleshooting checks for field hardware symptoms.",
            "parameters": {"type": "object", "properties": {"device": {"type": "string"}, "symptom": {"type": "string"}, "description": {"type": "string"}}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "interpret_sensor_report",
            "description": "Interpret camera-free phone sensor readings with confidence limits.",
            "parameters": {"type": "object", "properties": {"sensor": {"type": "string"}, "reading": {"type": "string"}, "context": {"type": "string"}}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compress_observation",
            "description": "Compress a spoken field observation into a compact audit record.",
            "parameters": {"type": "object", "properties": {"text": {"type": "string"}, "task": {"type": "string"}}},
        },
    },
]


def get_json(url: str, *, headers: dict[str, str] | None = None, timeout: float = 8) -> tuple[int, Any]:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"raw": raw[:500]}
        return response.status, data


def post_json(url: str, payload: dict[str, Any], *, timeout: float = 8) -> tuple[int, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def get_text(url: str, *, timeout: float = 8) -> tuple[int, str]:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.status, response.read().decode("utf-8", errors="replace")


def check(name: str, ok: bool, detail: str = "", *, warning: bool = False) -> dict[str, Any]:
    status = "pass" if ok else ("warning" if warning else "fail")
    return {"name": name, "status": status, "detail": detail}


def vapi_key() -> str:
    return os.getenv("VAPI_PRIVATE_KEY") or os.getenv("VAPI_API_KEY") or ""


def check_vapi() -> list[dict[str, Any]]:
    key = vapi_key()
    assistant_id = os.getenv("VAPI_ASSISTANT_ID") or "f5295f73-c741-4fbd-987e-cdc5b0b283cb"
    if not key:
        return [check("vapi_auth", False, "missing VAPI_PRIVATE_KEY/VAPI_API_KEY")]

    headers = {"Authorization": f"Bearer {key}", "User-Agent": "Mozilla/5.0"}
    try:
        _, tools = get_json("https://api.vapi.ai/tool", headers=headers, timeout=10)
        _, assistant = get_json(f"https://api.vapi.ai/assistant/{assistant_id}", headers=headers, timeout=10)
    except Exception as error:
        return [check("vapi_api", False, f"{type(error).__name__}: {str(error)[:120]}")]

    global_names = {
        str((tool.get("function") or {}).get("name") or "")
        for tool in tools
        if isinstance(tool, dict)
    }
    model = assistant.get("model") if isinstance(assistant.get("model"), dict) else {}
    inline_names = {
        str((tool.get("function") or {}).get("name") or "")
        for tool in (model.get("tools") or [])
        if isinstance(tool, dict)
    }
    tool_ids = model.get("toolIds") or []
    server_url = (assistant.get("server") or {}).get("url") or ""
    return [
        check("vapi_global_tools", EXPECTED_TOOLS <= global_names, ",".join(sorted(global_names))),
        check("vapi_assistant_tools", EXPECTED_TOOLS <= inline_names or len(tool_ids) >= 5, f"inline={len(inline_names)} toolIds={len(tool_ids)}"),
        check("vapi_model", model.get("provider") == "custom-llm" and "Qwen3-30B" in str(model.get("model")), str(model.get("model"))),
        check("vapi_server", "phonebio-vapi-webhook" in server_url, server_url),
    ]


def check_public_pages() -> list[dict[str, Any]]:
    try:
        dash_status, dash = get_text(PUBLIC_DASHBOARD, timeout=10)
        edge_status, edge = get_text(PUBLIC_EDGE, timeout=10)
    except Exception as error:
        return [check("public_pages", False, f"{type(error).__name__}: {str(error)[:120]}")]
    return [
        check("dashboard_live", dash_status == 200 and "PHONEBIO" in dash and "Start scripted auto demo" in dash, str(dash_status)),
        check("edge_page", edge_status == 200 and "EDGE ORCHESTRATOR" in edge, str(edge_status)),
    ]


def check_webhook() -> list[dict[str, Any]]:
    payload = {
        "message": {
            "type": "tool-calls",
            "toolCallList": [
                {"id": "guard_sds", "name": "get_safety_sheet", "parameters": {"substance": "formaldehyde"}},
                {"id": "guard_note", "name": "compress_observation", "parameters": {"text": "field note three juveniles twelve meters eighteen degrees"}},
            ],
        }
    }
    try:
        status, data = post_json(WEBHOOK_URL, payload, timeout=10)
    except Exception as error:
        return [check("insforge_webhook", False, f"{type(error).__name__}: {str(error)[:120]}")]
    results = data.get("results") if isinstance(data, dict) else []
    ok = status == 200 and isinstance(results, list) and len(results) == 2
    return [check("insforge_webhook", ok, f"status={status} results={len(results) if isinstance(results, list) else 'na'}")]


def check_voice_beats() -> list[dict[str, Any]]:
    system = {
        "role": "system",
        "content": (
            "You are PhoneBio. Use a tool for field notes, chemicals, protocols, "
            "hardware, and sensor readings. Keep spoken text short."
        ),
    }
    turns = [
        ("field_note", "Field note. Observed three juvenile specimens near the burrow at 12 meters, 18 degrees.", "compress_observation"),
        ("spill_location", "Low-level formaldehyde cleanup. No fire. No skin contact. I forgot the SDS location step.", "get_safety_sheet"),
        ("protocol", "How do I set up a pitfall trap for ground beetles?", "get_protocol"),
        ("barometer", "My barometer dropped 4 hPa in two hours.", "interpret_sensor_report"),
    ]
    checks: list[dict[str, Any]] = []
    for name, text, expected_tool in turns:
        messages = [system, {"role": "user", "content": text}]
        payload = {"stream": False, "messages": messages, "temperature": 0.1, "tools": LLM_TOOLS, "tool_choice": "auto"}
        started = time.time()
        try:
            _, data = post_json(LLM_URL, payload, timeout=12)
        except Exception as error:
            checks.append(check(f"voice_{name}", False, f"{type(error).__name__}: {str(error)[:120]}"))
            continue
        elapsed = time.time() - started
        message = ((data.get("choices") or [{}])[0].get("message") or {})
        tool_calls = message.get("tool_calls") or []
        tool_names = [
            str(((tool_call.get("function") or {}).get("name")) or "")
            for tool_call in tool_calls
            if isinstance(tool_call, dict)
        ]
        content = str(message.get("content") or "")
        model = str(data.get("model") or "")
        not_fallback = "fallback" not in model.lower()
        no_canned = "i am still here" not in content.lower()
        ok = expected_tool in tool_names and not_fallback and no_canned
        checks.append(check(f"voice_{name}", ok, f"{elapsed:.2f}s model={model} tools={','.join(tool_names) or 'none'}"))
    return checks


def check_ollarma() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    try:
        status, data = get_json(OLLARMA_READINESS, timeout=3)
        readiness = str(data.get("status", "unknown"))
        model = ((data.get("model_availability") or {}).get("effective_model") or "unknown")
        ok = status == 200 and readiness in {"ready", "degraded"}
        checks.append(check("ollarma_readiness", ok, f"{readiness} model={model}", warning=not ok))
        if readiness == "degraded":
            checks[-1]["status"] = "warning"
    except Exception as error:
        checks.append(check("ollarma_readiness", False, f"{type(error).__name__}: {str(error)[:120]}", warning=True))

    try:
        status, _ = get_json(WATCHTOWER_BRIDGE, timeout=3)
        checks.append(check("watchtower_ollarma_bridge", status == 200, str(status), warning=True))
    except Exception as error:
        checks.append(check("watchtower_ollarma_bridge", False, f"{type(error).__name__}: {str(error)[:120]}", warning=True))
    return checks


def run_once() -> dict[str, Any]:
    checks = []
    checks.extend(check_public_pages())
    checks.extend(check_vapi())
    checks.extend(check_webhook())
    checks.extend(check_voice_beats())
    checks.extend(check_ollarma())
    summary = {
        "pass": sum(1 for item in checks if item["status"] == "pass"),
        "warning": sum(1 for item in checks if item["status"] == "warning"),
        "fail": sum(1 for item in checks if item["status"] == "fail"),
    }
    return {
        "project": "phonebio",
        "mode": "live_demo_guard",
        "checks": checks,
        "summary": summary,
        "demoGreen": summary["fail"] == 0,
        "warningPolicy": "Ollarma/Watchtower warnings do not block the Vapi live demo path.",
    }


def print_human(report: dict[str, Any]) -> None:
    for item in report["checks"]:
        marker = {"pass": "PASS", "warning": "WARN", "fail": "FAIL"}[item["status"]]
        print(f"{marker:4} {item['name']}: {item.get('detail', '')}")
    s = report["summary"]
    print(f"\nsummary: pass={s['pass']} warning={s['warning']} fail={s['fail']} demoGreen={report['demoGreen']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fast read-only PhoneBio live demo guard.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of compact human output.")
    args = parser.parse_args()
    report = run_once()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0 if report["demoGreen"] else 1


if __name__ == "__main__":
    sys.exit(main())
