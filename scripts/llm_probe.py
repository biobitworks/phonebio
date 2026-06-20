"""Probe local Ollama custom-LLM tool calling for PhoneBio."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from fieldbio import llm


def _provider_state() -> list[dict[str, Any]]:
    return [{"name": p.name, "baseUrl": p.base_url, "model": p.model, "offline": p.offline} for p in llm.providers()]


def _print_report(report: dict[str, Any]) -> None:
    print(json.dumps(report, indent=2, sort_keys=True))


def main() -> None:
    body = {
        "messages": [
            {
                "role": "system",
                "content": "You are PhoneBio. Use tools for protocol, safety, hardware, and sensor questions.",
            },
            {
                "role": "user",
                "content": "I am collecting a surface water grab sample and the bottle has an air bubble. What do I do?",
            },
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_protocol",
                    "description": "Retrieve a local field biology protocol.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task": {"type": "string"},
                            "hazard": {"type": "string"},
                            "description": {"type": "string"},
                        },
                        "required": ["task"],
                    },
                },
            }
        ],
        "tool_choice": "auto",
        "temperature": 0.0,
    }
    try:
        result = llm.raw_completion(body, timeout=60)
    except Exception as error:
        _print_report(
            {
                "ready": False,
                "status": "blocked",
                "errorType": error.__class__.__name__,
                "error": str(error),
                "providers": _provider_state(),
                "nextActions": [
                    "Confirm Ollama is responsive at OLLAMA_BASE_URL.",
                    "Free memory or refresh Ollarma selection if local model loading times out.",
                    "Use the hosted Nebius/Vapi path for live calls when local Ollama is degraded.",
                ],
            }
        )
        raise SystemExit(2)
    message = result.get("choices", [{}])[0].get("message", {})
    tool_calls = message.get("tool_calls") or []
    report = {
        "ready": bool(tool_calls) and "reasoning" not in json.dumps(result),
        "status": "pass" if tool_calls else "fail",
        "model": result.get("model"),
        "hasReasoning": "reasoning" in json.dumps(result),
        "toolCallCount": len(tool_calls),
        "toolCalls": tool_calls,
    }
    _print_report(report)
    if not tool_calls:
        raise SystemExit("No tool call emitted by local model.")
    if "reasoning" in json.dumps(result):
        raise SystemExit("Local model response still contains reasoning.")


if __name__ == "__main__":
    main()
