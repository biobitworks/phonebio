#!/usr/bin/env python3
"""Create reusable Vapi Tools for PhoneBio and attach them to the live assistant.

This keeps the Vapi dashboard Tools page aligned with the assistant's inline
tool definitions without printing secrets or raw phone numbers.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


REPO_ROOT = Path(__file__).resolve().parent.parent
ASSISTANT_TEMPLATE = REPO_ROOT / "vapi" / "assistant.field-biology-worker.json"
WEBHOOK_URL = os.getenv("VAPI_WEBHOOK_URL") or "https://qfdp5nuv.function2.insforge.app/phonebio-vapi-webhook"
DEFAULT_ASSISTANT_ID = "f5295f73-c741-4fbd-987e-cdc5b0b283cb"


def api_key() -> str:
    key = os.getenv("VAPI_PRIVATE_KEY") or os.getenv("VAPI_API_KEY") or ""
    if not key:
        raise SystemExit("Missing VAPI_PRIVATE_KEY or VAPI_API_KEY.")
    return key


def curl(method: str, path: str, body: dict[str, Any] | None = None) -> Any:
    cmd = [
        "curl",
        "-sS",
        "-X",
        method,
        f"https://api.vapi.ai{path}",
        "-H",
        f"Authorization: Bearer {api_key()}",
    ]
    if body is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
    out = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if out.returncode != 0:
        raise SystemExit(out.stderr.strip() or f"curl failed for {path}")
    try:
        data = json.loads(out.stdout)
    except json.JSONDecodeError:
        raise SystemExit(f"Unexpected Vapi response for {path}: {out.stdout[:200]}")
    if isinstance(data, dict) and data.get("error"):
        raise SystemExit(json.dumps(data, indent=2))
    return data


def template_tools() -> list[dict[str, Any]]:
    template = json.loads(ASSISTANT_TEMPLATE.read_text(encoding="utf-8"))
    tools = template.get("model", {}).get("tools", [])
    if len(tools) < 5:
        raise SystemExit("Assistant template does not contain the five core tools.")
    return tools


def tool_name(tool: dict[str, Any]) -> str:
    return str((tool.get("function") or {}).get("name") or "")


def create_tool(tool: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "type": "function",
        "function": tool["function"],
        "server": {"url": WEBHOOK_URL},
    }
    return curl("POST", "/tool", payload)


def remove_bad_placeholder_tools(existing: list[dict[str, Any]]) -> list[str]:
    removed: list[str] = []
    for tool in existing:
        if tool_name(tool) == "api_request_tool" and tool.get("url") == "https://www.vapi.ai":
            tool_id = str(tool.get("id") or "")
            if not tool_id:
                continue
            curl("DELETE", f"/tool/{tool_id}")
            removed.append(tool_id)
    return removed


def patch_assistant_tool_ids(assistant_id: str, tool_ids: list[str], inline_tools: list[dict[str, Any]]) -> dict[str, Any]:
    assistant = curl("GET", f"/assistant/{assistant_id}")
    model = assistant.get("model") or {}
    model["toolIds"] = tool_ids
    # Keep inline definitions too for demo stability. The custom LLM proxy now
    # always forwards tools, so either inline tools or reusable tool IDs work.
    model["tools"] = inline_tools
    return curl("PATCH", f"/assistant/{assistant_id}", {"model": model})


def main() -> int:
    assistant_id = os.getenv("VAPI_ASSISTANT_ID") or DEFAULT_ASSISTANT_ID
    desired = template_tools()
    existing = curl("GET", "/tool")
    if not isinstance(existing, list):
        raise SystemExit("Unexpected Vapi /tool response.")
    removed = remove_bad_placeholder_tools(existing)
    by_name = {tool_name(tool): tool for tool in existing if tool_name(tool)}

    created_or_existing: list[dict[str, Any]] = []
    for tool in desired:
        name = tool_name(tool)
        current = by_name.get(name)
        if current:
            created_or_existing.append(current)
            continue
        created = create_tool(tool)
        created_or_existing.append(created)

    tool_ids = [str(tool.get("id")) for tool in created_or_existing if tool.get("id")]
    patch_assistant_tool_ids(assistant_id, tool_ids, desired)
    print(json.dumps({
        "assistantId": assistant_id,
        "webhook": WEBHOOK_URL,
        "toolCount": len(tool_ids),
        "toolNames": [tool_name(tool) for tool in desired],
        "toolIds": tool_ids,
        "removedPlaceholderToolIds": removed,
        "note": "Reusable Vapi Tools are now present; assistant still keeps inline copies for demo stability.",
    }, indent=2))
    return 0 if len(tool_ids) == len(desired) else 1


if __name__ == "__main__":
    sys.exit(main())
