"""Replay the PhoneBio hackathon demo against the hosted assistant server URL."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.demo_call import SCENARIO, _payload, _summarize  # noqa: E402
from scripts.hosted_function_probe import assistant_server_url  # noqa: E402


def _decode_result(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return result
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            return {"status": "error", "answer": "Hosted function returned a non-JSON string result."}
        return parsed if isinstance(parsed, dict) else {"status": "error", "answer": "Hosted function returned non-object JSON."}
    return {"status": "error", "answer": f"Hosted function returned unsupported result type: {type(result).__name__}."}


def run_hosted_demo(url: str | None = None) -> dict[str, Any]:
    target = url or assistant_server_url()
    turns = []
    for step in SCENARIO:
        response = httpx.post(target, json=_payload(step), timeout=20)
        response.raise_for_status()
        body = response.json()
        first = (body.get("results") or [{}])[0]
        result = _decode_result(first.get("result"))
        turn = _summarize(step, result)
        turn["toolCallId"] = first.get("toolCallId")
        turns.append(turn)
    passed = all(turn["status"] == step["expect_status"] for turn, step in zip(turns, SCENARIO))
    return {
        "scenario": "phonebio-hosted-hackathon-demo",
        "assistantServerUrlSet": bool(target),
        "turns": turns,
        "summary": {"turns": len(turns), "passed": passed},
    }


def main() -> None:
    report = run_hosted_demo()
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["summary"]["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
