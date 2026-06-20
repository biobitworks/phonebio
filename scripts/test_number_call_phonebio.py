#!/usr/bin/env python3
"""Place or dry-run a Vapi test-number call to the PhoneBio number.

Default is dry-run so credits are not spent accidentally. Use --place-call only
when the operator is ready to run the controlled Vapi-to-Vapi connectivity test.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PHONE_ID = "abf0a502-02ca-4a75-8703-a304e8303a71"
DEFAULT_TEST_ID = "3d425d42-cb3f-4c8e-946e-e1a84f2d6bdc"

try:
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")
except Exception:
    pass


VARIATIONS = {
    "siri": [
        "Hey Siri, call PhoneBio.",
        "PhoneBio, I am on speaker only and cannot touch the phone.",
        "Field note. Observed three juvenile specimens near the burrow at 12 meters, 18 degrees.",
        "Low-level formaldehyde cleanup. No fire. No skin contact. I forgot the SDS location step.",
        "I am near open ventilation. Eyewash is across the room. The spill kit is behind me. The exit is clear.",
    ],
    "voice-control": [
        "Voice Control is enabled before field work.",
        "Show names. Tap PhoneBio.",
        "PhoneBio, mobile data is weak, but this call works.",
        "Low-level formaldehyde cleanup. No fire. No skin contact. Ask my location checks before cleanup.",
    ],
    "switch-control": [
        "Switch Control is preconfigured before field work.",
        "Start the PhoneBio contact from the saved accessibility action.",
        "PhoneBio, I cannot use my hands. Keep questions short.",
        "Now there is a small fire and I cannot reach emergency services.",
    ],
    "noisy-stage": [
        "PhoneBio, this is a noisy stage test. I am on speaker only.",
        "Field note. Observed three juvenile specimens near the burrow at 12 meters, 18 degrees.",
        "Repeat if needed. Do not ask me to touch the phone.",
    ],
}


def api_key() -> str:
    key = os.getenv("VAPI_PRIVATE_KEY") or os.getenv("VAPI_API_KEY") or ""
    if not key:
        raise SystemExit("Missing VAPI_PRIVATE_KEY or VAPI_API_KEY.")
    return key


def vapi_get(path: str) -> Any:
    out = subprocess.run(
        ["curl", "-sS", f"https://api.vapi.ai{path}", "-H", f"Authorization: Bearer {api_key()}"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    return json.loads(out)


def vapi_post(path: str, payload: dict[str, Any]) -> Any:
    out = subprocess.run(
        [
            "curl",
            "-sS",
            "-X",
            "POST",
            f"https://api.vapi.ai{path}",
            "-H",
            f"Authorization: Bearer {api_key()}",
            "-H",
            "Content-Type: application/json",
            "-d",
            json.dumps(payload),
        ],
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    return json.loads(out)


def redact(value: str | None) -> str:
    if not value:
        return "missing"
    cleaned = str(value)
    return f"***{cleaned[-4:]}" if len(cleaned) > 4 else "set"


def select_number(numbers: list[dict[str, Any]], number_id: str) -> dict[str, Any]:
    for record in numbers:
        if str(record.get("id")) == number_id:
            return record
    raise SystemExit(f"Vapi phone-number id not found: {number_id}")


def print_variation(name: str) -> None:
    lines = VARIATIONS[name]
    print(f"\nACCESSIBILITY_VARIATION: {name}")
    for index, line in enumerate(lines, start=1):
        print(f"{index}. {line}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Use the Vapi test number to call the PhoneBio number.")
    parser.add_argument("--place-call", action="store_true", help="Actually create the outbound Vapi call.")
    parser.add_argument("--variation", choices=sorted(VARIATIONS) + ["all"], default="siri")
    parser.add_argument("--test-phone-number-id", default=os.getenv("VAPI_TEST_PHONE_NUMBER_ID") or DEFAULT_TEST_ID)
    parser.add_argument("--phonebio-phone-number-id", default=os.getenv("VAPI_PHONE_NUMBER_ID") or DEFAULT_PHONE_ID)
    parser.add_argument("--assistant-id", default=os.getenv("VAPI_ASSISTANT_ID", ""))
    args = parser.parse_args()

    numbers = vapi_get("/phone-number")
    if not isinstance(numbers, list):
        raise SystemExit("Unexpected Vapi phone-number response.")
    test_number = select_number(numbers, args.test_phone_number_id)
    phonebio_number = select_number(numbers, args.phonebio_phone_number_id)
    assistant_id = args.assistant_id or str(test_number.get("assistantId") or phonebio_number.get("assistantId") or "")
    destination = str(phonebio_number.get("number") or "")
    if not assistant_id:
        raise SystemExit("No assistant id found for test call.")
    if not destination:
        raise SystemExit("PhoneBio phone number record does not include a callable number.")

    payload = {
        "assistantId": assistant_id,
        "phoneNumberId": args.test_phone_number_id,
        "customer": {"number": destination},
    }
    report = {
        "dryRun": not args.place_call,
        "direction": "Vapi test number -> PhoneBio number",
        "assistantId": assistant_id,
        "originPhoneNumberId": args.test_phone_number_id,
        "destinationPhoneNumberId": args.phonebio_phone_number_id,
        "originNumber": redact(test_number.get("number")),
        "destinationNumber": redact(destination),
        "warning": "This is a controlled connectivity test. For the live demo, prefer a human phone call.",
    }
    print(json.dumps(report, indent=2, sort_keys=True))

    if args.variation == "all":
        for name in sorted(VARIATIONS):
            print_variation(name)
    else:
        print_variation(args.variation)

    if not args.place_call:
        print("\nDRY_RUN_ONLY: add --place-call to create the Vapi outbound call.")
        return

    call = vapi_post("/call", payload)
    print(json.dumps({
        "created": True,
        "callId": call.get("id"),
        "status": call.get("status"),
        "type": call.get("type"),
        "assistantId": call.get("assistantId"),
        "phoneNumberId": call.get("phoneNumberId"),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
