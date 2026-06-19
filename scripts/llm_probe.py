"""Probe local Ollama custom-LLM tool calling for PhoneBio."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from fieldbio import llm


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
    result = llm.raw_completion(body, timeout=60)
    message = result.get("choices", [{}])[0].get("message", {})
    tool_calls = message.get("tool_calls") or []
    print(
        json.dumps(
            {
                "model": result.get("model"),
                "hasReasoning": "reasoning" in json.dumps(result),
                "toolCallCount": len(tool_calls),
                "toolCalls": tool_calls,
            },
            indent=2,
            sort_keys=True,
        )
    )
    if not tool_calls:
        raise SystemExit("No tool call emitted by local model.")
    if "reasoning" in json.dumps(result):
        raise SystemExit("Local model response still contains reasoning.")


if __name__ == "__main__":
    main()
