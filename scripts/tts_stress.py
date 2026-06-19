"""Generate text-to-voice demo prompts and stress the matching tool paths.

This uses the macOS `say` command, so it consumes no paid API budget. The audio
files are rehearsal artifacts only; Vapi STT still needs a real call test.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from fieldbio.app import handle_vapi_payload  # noqa: E402
from scripts.demo_call import SCENARIO as DEMO_SCENARIO  # noqa: E402
from scripts.demo_call import _payload, _summarize  # noqa: E402
from scripts.hosted_demo import _decode_result  # noqa: E402
from scripts.hosted_function_probe import assistant_server_url  # noqa: E402


EXTRA_SCENARIOS: list[dict[str, Any]] = [
    {
        "label": "normal-hands-free-checkin",
        "caller": "PhoneBio, I am in PPE and cannot use my hands. Mobile data is weak, but this call works.",
        "tool": "compress_observation",
        "arguments": {
            "text": "PPE, cannot use hands, mobile data weak, voice call works.",
            "connectivity": "voice only",
            "phonePlacement": "speaker",
        },
        "expect_status": "ok",
        "must_include": ["voice"],
    },
    {
        "label": "speaker-only-emergency-risk",
        "caller": (
            "PhoneBio, I am in a remote field station, speaker only, no hands. "
            "There is a chemical spill, possible hardware fire, loud machinery, "
            "two voices overlapping, and mobile data is down."
        ),
        "tool": "assess_environment_risk",
        "arguments": {
            "hazard": "chemical spill and possible hardware fire",
            "audio": "two voices overlapping and loud machinery",
            "connectivity": "mobile data down, voice only",
            "phonePlacement": "bench, speaker only",
            "description": (
                "Remote field station, chemical spill, possible hardware fire, "
                "loud machinery, two voices overlapping, mobile data down."
            ),
        },
        "expect_status": "ok",
        "must_include": ["high", "voice", "speaker"],
    },
    {
        "label": "nearby-radio-confirmation-risk",
        "caller": (
            "Stage demo mode. I am in PPE, the phone is in my pocket, data is "
            "down, I hear radio chatter and there may be another worker nearby."
        ),
        "tool": "assess_environment_risk",
        "arguments": {
            "audio": "radio chatter, possible other worker, machinery noise",
            "connectivity": "data down",
            "phonePlacement": "pocket",
            "description": "radio chatter, possible other worker nearby, PPE, data down",
        },
        "expect_status": "ok",
        "must_include": ["possible", "voice", "identity"],
    },
    {
        "label": "public-alert-context",
        "caller": "Check recent public alerts near San Francisco before I continue the field run.",
        "tool": "get_public_alert_context",
        "arguments": {
            "country": "US",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "hazardHint": "weather or disaster alert",
        },
        "expect_status": "ok",
        "must_include": ["context", "substitute"],
    },
    {
        "label": "milliliter-dialect-shorthand",
        "caller": (
            "Observed em-ells, five milliliters formalin, one point five mil "
            "tube, negative control, and old centrifuge vibration."
        ),
        "tool": "compress_observation",
        "arguments": {
            "text": (
                "Observed em-ells, five milliliters formalin, one point five mil "
                "tube, negative control, and old centrifuge vibration."
            ),
            "connectivity": "voice only",
            "phonePlacement": "pocket",
        },
        "expect_status": "ok",
        "must_include": ["negative", "centrifuge", "voice"],
    },
    {
        "label": "unknown-protocol-stop-work",
        "caller": "I need to run a xqzblorv narnix flibbert assay. What should I do?",
        "tool": "get_protocol",
        "arguments": {"task": "xqzblorv narnix flibbert assay"},
        "expect_status": "not_found",
        "must_include": ["stop", "supervisor"],
    },
]


def slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in value.lower()).strip("-")


def redact_result(result: dict[str, Any]) -> dict[str, Any]:
    redacted = {
        key: result.get(key)
        for key in (
            "status",
            "id",
            "title",
            "name",
            "device",
            "confidence",
            "riskLevel",
            "peopleSignal",
            "inferenceBoundary",
            "answer",
            "readAloudSummary",
            "disclaimer",
            "escalateIf",
            "voiceGuidance",
            "voiceReadback",
            "voice_readback",
            "fieldLine",
            "field_line",
            "readAloudSummary",
        )
        if result.get(key)
    }
    if result.get("steps"):
        redacted["stepCount"] = len(result["steps"])
    if result.get("actions"):
        redacted["actionCount"] = len(result["actions"])
        redacted["actionsPreview"] = result["actions"][:2]
    if result.get("sourceIds"):
        redacted["sourceIds"] = result["sourceIds"]
    if result.get("alerts"):
        redacted["alertCount"] = len(result["alerts"])
        redacted["alertSources"] = sorted({str(alert.get("source")) for alert in result["alerts"] if alert.get("source")})
    return redacted


def synthesize_audio(say_bin: str, case: dict[str, Any], out_dir: Path, *, voice: str, rate: int) -> dict[str, Any]:
    path = out_dir / f"{slug(case['label'])}.aiff"
    command = [say_bin, "-v", voice, "-r", str(rate), "-o", str(path), case["caller"]]
    completed = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, timeout=45, check=False)
    return {
        "ok": completed.returncode == 0 and path.exists() and path.stat().st_size > 0,
        "path": str(path.relative_to(REPO_ROOT)),
        "bytes": path.stat().st_size if path.exists() else 0,
        "returnCode": completed.returncode,
        "stderrTail": completed.stderr[-300:],
    }


async def run_local(case: dict[str, Any]) -> dict[str, Any]:
    response = await handle_vapi_payload(_payload(case))
    result = (response.get("results") or [{}])[0].get("result", {})
    return result if isinstance(result, dict) else {"status": "error", "answer": "Local result was not an object."}


def run_hosted(case: dict[str, Any], target: str) -> dict[str, Any]:
    response = httpx.post(target, json=_payload(case), timeout=20)
    response.raise_for_status()
    body = response.json()
    first = (body.get("results") or [{}])[0]
    return _decode_result(first.get("result"))


def result_has_terms(result: dict[str, Any], terms: list[str]) -> bool:
    if not terms:
        return True
    text = json.dumps(redact_result(result), sort_keys=True).lower()
    return all(term.lower() in text for term in terms)


async def stress(args: argparse.Namespace) -> dict[str, Any]:
    say_bin = shutil.which("say")
    out_dir = REPO_ROOT / args.out_dir / time.strftime("%Y%m%d-%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)

    cases = [*DEMO_SCENARIO, *EXTRA_SCENARIOS]
    hosted_url = "" if args.skip_hosted else assistant_server_url()
    turns = []
    for case in cases:
        audio = (
            synthesize_audio(say_bin, case, out_dir, voice=args.voice, rate=args.rate)
            if say_bin
            else {"ok": False, "path": None, "bytes": 0, "reason": "macOS say command not found"}
        )
        local_result = await run_local(case)
        local_ok = local_result.get("status") == case["expect_status"] and result_has_terms(
            local_result,
            case.get("must_include", []),
        )
        hosted_result: dict[str, Any] = {"status": "skipped"}
        hosted_ok = True
        if hosted_url:
            try:
                hosted_result = run_hosted(case, hosted_url)
                hosted_ok = hosted_result.get("status") == case["expect_status"] and result_has_terms(
                    hosted_result,
                    case.get("must_include", []),
                )
            except (httpx.HTTPError, json.JSONDecodeError) as error:
                hosted_result = {"status": "error", "errorType": error.__class__.__name__}
                hosted_ok = False

        turn = _summarize(case, local_result)
        turn.update(
            {
                "audio": audio,
                "localOk": local_ok,
                "hostedOk": hosted_ok,
                "hostedChecked": bool(hosted_url),
                "localResult": redact_result(local_result),
                "hostedResult": redact_result(hosted_result),
            }
        )
        turn["passed"] = bool(audio["ok"] and local_ok and hosted_ok)
        turns.append(turn)

    manifest = {
        "scenario": "phonebio-text-to-voice-component-stress",
        "budget": "offline macOS say; no paid TTS API",
        "sttBoundary": "Generated audio is for rehearsal; real Vapi STT is verified only by a live call.",
        "outDir": str(out_dir.relative_to(REPO_ROOT)),
        "voice": args.voice,
        "rate": args.rate,
        "hostedChecked": bool(hosted_url),
        "summary": {
            "cases": len(turns),
            "passed": all(turn["passed"] for turn in turns),
            "audioFiles": sum(1 for turn in turns if turn["audio"]["ok"]),
            "localPassed": sum(1 for turn in turns if turn["localOk"]),
            "hostedPassed": sum(1 for turn in turns if turn["hostedOk"]),
        },
        "turns": turns,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate TTS prompts and stress PhoneBio component routing.")
    parser.add_argument("--voice", default="Samantha", help="macOS say voice name.")
    parser.add_argument("--rate", type=int, default=185, help="macOS say speaking rate.")
    parser.add_argument("--out-dir", default="recordings/tts-stress", help="Ignored output directory for audio artifacts.")
    parser.add_argument("--skip-hosted", action="store_true", help="Skip hosted InsForge webhook checks.")
    args = parser.parse_args()

    report = asyncio.run(stress(args))
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["summary"]["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
