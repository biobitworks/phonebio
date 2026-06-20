#!/usr/bin/env python3
"""Automated outbound Vapi-to-Vapi connectivity test for PhoneBio.

Places a real outbound call from the Vapi TEST number to the PhoneBio number so
we can verify that calls connect and do not get stuck -- without manual dialing.

The CALLER side is an inline transient Vapi assistant that role-plays a field
worker: it reads a single SCRIPT line, listens for one short reply, then says
goodbye and hangs up. Calls are kept short (~20-30s) to save credits.

Usage:
    python3 scripts/call_test.py [variation_name|all]

Default (no arg) runs just the "spill" variation -- one call.

For each call the harness creates the call, polls GET /call/{id} until the call
ends (or times out), then prints: variation name, call id, endedReason,
duration, the last 6 transcript turns, and a PASS/FAIL verdict.

PASS criteria:
  - endedReason is a clean end (customer-ended-call, assistant-ended-call,
    or either side said an end-call phrase) OR silence-timed-out after a real
    exchange, AND
  - NOT a connect failure (sip-*-before-call-connect / *-connection-failed), AND
  - the PhoneBio assistant actually spoke a grounded reply.

Secrets: the Vapi private key is read from .env (VAPI_PRIVATE_KEY or
VAPI_API_KEY) and is NEVER printed.
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

REPO_ROOT = Path(__file__).resolve().parent.parent

# --- Fixed identifiers (from operator) --------------------------------------
# TEST phone-number id -> the caller (+15415269684).
TEST_PHONE_NUMBER_ID = "3d425d42-cb3f-4c8e-946e-e1a84f2d6bdc"
# PhoneBio number to dial; its inbound assistant (f5295f73...) answers.
PHONEBIO_NUMBER = "+15415269723"

VAPI_BASE = "https://api.vapi.ai"
# Cloudflare in front of api.vapi.ai returns 403 without a browser UA.
USER_AGENT = "Mozilla/5.0"

# Custom-LLM brain so we do not need a native provider key for the caller.
CALLER_LLM_URL = "https://qfdp5nuv.function2.insforge.app/phonebio-llm"
CALLER_LLM_MODEL = "Qwen/Qwen3-30B-A3B-Instruct-2507"

CALLER_PERSONA = (
    "You are a field biology worker placing a phone call to PhoneBio, a hands-free "
    "field-safety assistant. You are on speaker and cannot touch the phone. "
    "Speak the opening line you were given. Then listen to PhoneBio's reply and, if "
    "it asks one clarifying question, answer it in one short sentence. Do not start "
    "new topics. After you hear a useful answer, say 'thank you, goodbye' and end the "
    "call. Keep every turn to one short sentence. The whole call must stay under "
    "thirty seconds."
)

# Poll/length budgets (short to conserve credits).
SILENCE_TIMEOUT_SECONDS = 20
POLL_TIMEOUT_SECONDS = 90
POLL_INTERVAL_SECONDS = 4

END_CALL_PHRASES = ["goodbye", "thank you"]

# Accessibility script variations: different phrasings / speaking styles.
VARIATIONS: list[dict[str, str]] = [
    {
        "name": "field_note",
        "line": "Log this: three juveniles near the burrow at twelve meters, eighteen degrees.",
    },
    {
        "name": "spill",
        "line": "Low-level formaldehyde cleanup. No fire. No skin contact. I forgot the SDS location step.",
        "expected": "location_check",
    },
    {
        # Tests slang/accessibility: "emelles" = mL.
        "name": "spill_colloquial",
        "line": "I dumped like fifty emelles of formalin on the bench, no flames, what now?",
    },
    {
        "name": "protocol",
        "line": "How do I set up a pitfall trap?",
    },
    {
        "name": "emergency",
        "line": "There's a small fire and I can't reach 911.",
    },
]
VARIATIONS_BY_NAME = {v["name"]: v for v in VARIATIONS}

DEFAULT_VARIATION = "spill"

# endedReason substrings that mean the call never connected.
CONNECT_FAILURE_MARKERS = (
    "before-call-connect",
    "connection-failed",
    "no-answer",
    "busy",
    "failed-to-connect",
    "twilio-failed",
    "vonage-failed",
)


def load_env() -> None:
    """Best-effort .env load so VAPI_PRIVATE_KEY/VAPI_API_KEY are available."""
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(REPO_ROOT / ".env")
        return
    except Exception:
        pass
    # Minimal fallback parser (no dependency on python-dotenv).
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def api_key() -> str:
    key = os.getenv("VAPI_PRIVATE_KEY") or os.getenv("VAPI_API_KEY") or ""
    if not key:
        raise SystemExit(
            "Missing VAPI_PRIVATE_KEY or VAPI_API_KEY in environment/.env."
        )
    return key


def _request(method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
    """Call the Vapi REST API. Always sends a browser User-Agent (Cloudflare)."""
    url = f"{VAPI_BASE}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {api_key()}")
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        # Surface the API error body (never contains the key) so we can iterate.
        raise SystemExit(
            f"Vapi {method} {path} -> HTTP {exc.code}: {body[:800]}"
        )
    except urllib.error.URLError as exc:
        raise SystemExit(f"Vapi {method} {path} network error: {exc.reason}")
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        raise SystemExit(f"Vapi {method} {path} non-JSON response: {body[:400]}")


def vapi_get(path: str) -> Any:
    return _request("GET", path)


def vapi_post(path: str, payload: dict[str, Any]) -> Any:
    return _request("POST", path, payload)


def vapi_delete(path: str) -> Any:
    return _request("DELETE", path)


def build_caller_assistant(line: str) -> dict[str, Any]:
    """Inline transient CALLER assistant (custom-llm brain, no provider key)."""
    return {
        "firstMessage": line,
        "silenceTimeoutSeconds": SILENCE_TIMEOUT_SECONDS,
        "endCallPhrases": END_CALL_PHRASES,
        "model": {
            "provider": "custom-llm",
            "url": CALLER_LLM_URL,
            "model": CALLER_LLM_MODEL,
            "messages": [
                {"role": "system", "content": CALLER_PERSONA},
            ],
        },
    }


def create_call(line: str) -> dict[str, Any]:
    payload = {
        "phoneNumberId": TEST_PHONE_NUMBER_ID,
        "customer": {"number": PHONEBIO_NUMBER},
        "assistant": build_caller_assistant(line),
    }
    return vapi_post("/call", payload)


def poll_until_ended(call_id: str) -> dict[str, Any]:
    deadline = time.time() + POLL_TIMEOUT_SECONDS
    last: dict[str, Any] = {}
    while time.time() < deadline:
        last = vapi_get(f"/call/{call_id}")
        status = str(last.get("status") or "")
        if status == "ended":
            return last
        time.sleep(POLL_INTERVAL_SECONDS)
    last["_timedOutPolling"] = True
    return last


def _duration_seconds(call: dict[str, Any]) -> float | None:
    started = call.get("startedAt")
    ended = call.get("endedAt")
    if not started or not ended:
        return None
    try:
        from datetime import datetime

        def _parse(ts: str) -> "datetime":
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))

        return round((_parse(ended) - _parse(started)).total_seconds(), 1)
    except Exception:
        return None


def _transcript_turns(call: dict[str, Any]) -> list[dict[str, str]]:
    """Extract (role, text) turns from messages or transcript string."""
    turns: list[dict[str, str]] = []
    messages = call.get("messages")
    if isinstance(messages, list):
        for m in messages:
            role = str(m.get("role") or "")
            text = m.get("message") or m.get("content") or ""
            if role in ("system",) or not str(text).strip():
                continue
            turns.append({"role": role, "text": str(text).strip()})
    if turns:
        return turns
    # Fallback: parse the flat transcript string ("User: ...\nAI: ...").
    transcript = call.get("transcript")
    if isinstance(transcript, str):
        for raw in transcript.splitlines():
            line = raw.strip()
            if not line:
                continue
            if ":" in line:
                role, _, text = line.partition(":")
                turns.append({"role": role.strip().lower(), "text": text.strip()})
            else:
                turns.append({"role": "?", "text": line})
    return turns


# Roles the *PhoneBio* (answering) side uses. From the caller's outbound call,
# PhoneBio is the "user" on the line; the caller assistant is "assistant"/"bot".
PHONEBIO_ROLES = ("user", "customer", "human")
CALLER_ROLES = ("assistant", "bot", "ai")


def _phonebio_spoke_grounded(turns: list[dict[str, str]]) -> bool:
    """True if the PhoneBio side produced a substantive (non-trivial) reply."""
    for t in turns:
        role = t["role"].lower()
        text = t["text"].strip()
        if role in PHONEBIO_ROLES and len(text.split()) >= 5:
            return True
    return False


def _phonebio_text(turns: list[dict[str, str]]) -> str:
    return " ".join(
        t["text"].strip()
        for t in turns
        if t["role"].lower() in PHONEBIO_ROLES
    ).lower()


def evaluate(call: dict[str, Any], turns: list[dict[str, str]], variation: dict[str, str]) -> tuple[bool, str]:
    ended_reason = str(call.get("endedReason") or "")
    status = str(call.get("status") or "")

    if call.get("_timedOutPolling") and status != "ended":
        return False, f"polling timed out, call still '{status or 'unknown'}'"

    lowered = ended_reason.lower()
    if any(marker in lowered for marker in CONNECT_FAILURE_MARKERS):
        return False, f"connect failure: {ended_reason}"

    phonebio_spoke = _phonebio_spoke_grounded(turns)
    phonebio_text = _phonebio_text(turns)
    if any(marker in phonebio_text for marker in ["hold on", "one moment", "just a sec", "take a second", "this will take"]):
        return False, "PhoneBio used filler/wait language"
    if variation.get("expected") == "location_check":
        if "move away from the fire" in phonebio_text or "emergency services" in phonebio_text:
            return False, "PhoneBio escalated a no-fire low-level spill as fire/emergency"
        if phonebio_spoke and not any(term in phonebio_text for term in ["where", "ventilation", "eyewash", "spill kit", "exit"]):
            return False, "PhoneBio did not ask the AMBER location/safety context question"

    # Clean endings: either side hung up, or either side spoke an end-call phrase.
    good_end = ended_reason in (
        "customer-ended-call",
        "assistant-ended-call",
        "assistant-said-end-call-phrase",
        "customer-said-end-call-phrase",
    )
    silence_after_exchange = ended_reason == "silence-timed-out" and phonebio_spoke

    if (good_end or silence_after_exchange) and phonebio_spoke:
        return True, f"connected, PhoneBio replied, ended via {ended_reason}"
    if good_end and not phonebio_spoke:
        return False, f"ended ({ended_reason}) but PhoneBio never gave a grounded reply"
    if not ended_reason:
        return False, "no endedReason recorded"
    return False, f"unexpected/insufficient outcome: {ended_reason}"


def run_variation(variation: dict[str, str]) -> dict[str, Any]:
    name = variation["name"]
    line = variation["line"]
    print(f"\n=== variation: {name} ===")
    print(f"caller line: {line}")
    print("creating outbound call (TEST number -> PhoneBio)...")

    created = create_call(line)
    call_id = created.get("id")
    if not call_id:
        print(f"FAIL: call not created. Response: {json.dumps(created)[:600]}")
        return {"name": name, "callId": None, "pass": False, "error": "not-created"}
    print(f"call id: {call_id} (status={created.get('status')}) -- polling up to {POLL_TIMEOUT_SECONDS}s")

    call = poll_until_ended(call_id)
    if call.get("_timedOutPolling") and str(call.get("status") or "") != "ended":
        try:
            vapi_delete(f"/call/{call_id}")
            call["endedReason"] = call.get("endedReason") or "deleted-after-timeout"
        except Exception as error:
            call["_cleanupError"] = f"{type(error).__name__}: {str(error)[:120]}"
    ended_reason = call.get("endedReason")
    duration = _duration_seconds(call)
    turns = _transcript_turns(call)
    passed, verdict = evaluate(call, turns, variation)

    print(f"variation:    {name}")
    print(f"call id:      {call_id}")
    print(f"status:       {call.get('status')}")
    print(f"endedReason:  {ended_reason}")
    print(f"duration:     {duration if duration is not None else 'n/a'}s")
    print("last 6 transcript turns:")
    if turns:
        for t in turns[-6:]:
            text = t["text"]
            if len(text) > 220:
                text = text[:217] + "..."
            print(f"  [{t['role']}] {text}")
    else:
        print("  (no transcript turns captured)")
    print(f"VERDICT: {'PASS' if passed else 'FAIL'} -- {verdict}")

    return {
        "name": name,
        "callId": call_id,
        "status": call.get("status"),
        "endedReason": ended_reason,
        "durationSeconds": duration,
        "transcriptTurns": len(turns),
        "pass": passed,
        "verdict": verdict,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Automated Vapi-to-Vapi PhoneBio connectivity test."
    )
    parser.add_argument(
        "variation",
        nargs="?",
        default=DEFAULT_VARIATION,
        help=(
            "Variation name to run, or 'all'. "
            f"Choices: {', '.join(VARIATIONS_BY_NAME)}, all. "
            f"Default: {DEFAULT_VARIATION} (one call)."
        ),
    )
    args = parser.parse_args()

    load_env()

    if args.variation == "all":
        targets = VARIATIONS
    elif args.variation in VARIATIONS_BY_NAME:
        targets = [VARIATIONS_BY_NAME[args.variation]]
    else:
        raise SystemExit(
            f"Unknown variation '{args.variation}'. "
            f"Choices: {', '.join(VARIATIONS_BY_NAME)}, all."
        )

    results = [run_variation(v) for v in targets]

    print("\n=== summary ===")
    all_pass = True
    for r in results:
        mark = "PASS" if r.get("pass") else "FAIL"
        all_pass = all_pass and bool(r.get("pass"))
        print(f"  {mark}  {r['name']:16s} call={r.get('callId')} reason={r.get('endedReason')}")
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
