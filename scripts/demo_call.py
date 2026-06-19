"""Replay the PhoneBio hackathon call script against local Vapi tool handlers."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from fieldbio.app import handle_vapi_payload


SCENARIO = [
    {
        "label": "water-sample-air-bubble",
        "caller": "I am collecting a surface water grab sample and the bottle has an air bubble. What do I do?",
        "tool": "get_protocol",
        "arguments": {"task": "surface water grab sample", "hazard": "air bubble no headspace"},
        "expect_status": "ok",
    },
    {
        "label": "formaldehyde-glove-spill",
        "caller": "I spilled formaldehyde on a glove.",
        "tool": "get_safety_sheet",
        "arguments": {"substance": "formaldehyde", "description": "spill on glove"},
        "expect_status": "ok",
    },
    {
        "label": "centrifuge-vibration",
        "caller": "The centrifuge is vibrating after balancing.",
        "tool": "troubleshoot_hardware",
        "arguments": {"device": "centrifuge", "symptom": "vibrating after balancing"},
        "expect_status": "ok",
    },
    {
        "label": "barometer-pressure-drop",
        "caller": "My barometer dropped 4 hPa in two hours.",
        "tool": "interpret_sensor_report",
        "arguments": {"sensor": "barometer", "reading": "pressure dropped 4 hPa in two hours"},
        "expect_status": "ok",
    },
    {
        "label": "compact-field-note",
        "caller": "Observed approximately 12 cm water sample at north transect.",
        "tool": "compress_observation",
        "arguments": {"text": "Observed approximately 12 cm water sample at north transect"},
        "expect_status": "ok",
    },
]


def _payload(step: dict[str, Any]) -> dict[str, Any]:
    return {
        "message": {
            "type": "tool-calls",
            "toolCalls": [
                {
                    "id": f"demo_{step['label']}",
                    "function": {
                        "name": step["tool"],
                        "arguments": step["arguments"],
                    },
                }
            ],
        }
    }


def _summarize(step: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    summary = {
        "label": step["label"],
        "caller": step["caller"],
        "tool": step["tool"],
        "status": result.get("status"),
        "sourceIds": result.get("sourceIds", []),
    }
    for key in ("title", "name", "device", "id", "confidence", "readAloudSummary", "disclaimer", "escalateIf"):
        if result.get(key):
            summary[key] = result[key]
    if result.get("steps"):
        summary["stepCount"] = len(result["steps"])
    if result.get("compression_ratio"):
        summary["compressionRatio"] = result["compression_ratio"]
    return summary


async def run_demo() -> dict[str, Any]:
    turns = []
    for step in SCENARIO:
        response = await handle_vapi_payload(_payload(step))
        result = response["results"][0]["result"]
        turns.append(_summarize(step, result))
    passed = all(turn["status"] == step["expect_status"] for turn, step in zip(turns, SCENARIO))
    return {
        "scenario": "phonebio-hackathon-demo",
        "turns": turns,
        "summary": {"turns": len(turns), "passed": passed},
    }


def main() -> None:
    report = asyncio.run(run_demo())
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["summary"]["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
