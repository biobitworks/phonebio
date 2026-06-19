"""PhoneBio Vapi wiring CLI.

Examples:
  python3 vapi/wire.py create-assistant --assign-phone --dry-run
  Set Vapi env vars in the shell, then run:
    python3 vapi/wire.py create-assistant --assign-phone
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fieldbio.vapi_client import (
    api_key_from_env,
    assign_phone_number,
    assistant_payload,
    create_assistant,
    create_outbound_call,
    list_calls,
    list_phone_numbers,
    outbound_call_payload,
    phone_assignment_payload,
    phone_number_id_from_env_or_single,
    redacted_call_record,
    redacted_phone_number_record,
    vapi_preflight,
    verify_recent_call,
    webhook_url_from_env,
)


def _redacted_env_state() -> dict[str, bool]:
    return {
        "VAPI_API_KEY_or_PRIVATE_KEY": bool(api_key_from_env()),
        "VAPI_PHONE_NUMBER_ID": bool(os.getenv("VAPI_PHONE_NUMBER_ID")),
        "VAPI_ASSISTANT_ID": bool(os.getenv("VAPI_ASSISTANT_ID")),
        "VAPI_WEBHOOK_URL_or_PUBLIC_BASE_URL": bool(webhook_url_from_env()),
    }


def _print_json(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def _redacted_url(value: str) -> dict[str, str | None]:
    parsed = urlparse(value)
    return {
        "scheme": parsed.scheme or None,
        "host": parsed.netloc or None,
        "path": parsed.path or None,
    }


def _redacted_assistant_record(record: dict[str, Any]) -> dict[str, Any]:
    tools = [
        tool.get("function", {}).get("name")
        for tool in record.get("model", {}).get("tools", [])
        if tool.get("type") == "function" and tool.get("function", {}).get("name")
    ]
    return {
        "id": record.get("id"),
        "name": record.get("name"),
        "createdAt": record.get("createdAt"),
        "updatedAt": record.get("updatedAt"),
        "serverUrl": _redacted_url(record.get("server", {}).get("url", "")),
        "modelProvider": record.get("model", {}).get("provider"),
        "model": record.get("model", {}).get("model"),
        "toolNames": tools,
    }


def _redacted_call_record(record: dict[str, Any]) -> dict[str, Any]:
    return redacted_call_record(record)


def create_assistant_command(args: argparse.Namespace) -> int:
    payload = assistant_payload(args.webhook_url)
    if args.dry_run:
        result = {
            "dryRun": True,
            "envReady": _redacted_env_state(),
            "createAssistant": payload,
        }
        if args.assign_phone:
            assistant_id = os.getenv("VAPI_ASSISTANT_ID") or "<assistant-id-from-create-response>"
            result["assignPhone"] = {
                "phoneNumberIdSet": bool(os.getenv("VAPI_PHONE_NUMBER_ID")),
                "phoneNumberIdAutoDiscovery": "enabled-for-live-call",
                "payload": phone_assignment_payload(assistant_id, args.webhook_url),
            }
        _print_json(result)
        return 0

    assistant = create_assistant(api_key_from_env(), payload)
    assistant_id = assistant.get("id")
    result: dict[str, object] = {"assistant": _redacted_assistant_record(assistant)}
    if args.assign_phone:
        result["phoneNumber"] = assign_phone_number(
            api_key_from_env(),
            phone_number_id_from_env_or_single(api_key_from_env()),
            assistant_id,
            args.webhook_url,
        )
        result["phoneNumber"] = redacted_phone_number_record(result["phoneNumber"])
    _print_json(result)
    return 0


def assign_phone_command(args: argparse.Namespace) -> int:
    assistant_id = args.assistant_id or os.getenv("VAPI_ASSISTANT_ID", "")
    phone_number_id = args.phone_number_id or os.getenv("VAPI_PHONE_NUMBER_ID", "")
    if args.dry_run:
        _print_json(
            {
                "dryRun": True,
                "envReady": _redacted_env_state(),
                "phoneNumberIdSet": bool(phone_number_id),
                "phoneNumberIdAutoDiscovery": "enabled-for-live-call",
                "assistantIdSet": bool(assistant_id),
                "payload": phone_assignment_payload(assistant_id or "<assistant-id>", args.webhook_url),
            }
        )
        return 0
    phone_number_id = phone_number_id or phone_number_id_from_env_or_single(api_key_from_env())
    _print_json(redacted_phone_number_record(assign_phone_number(api_key_from_env(), phone_number_id, assistant_id, args.webhook_url)))
    return 0


def outbound_call_command(args: argparse.Namespace) -> int:
    assistant_id = args.assistant_id or os.getenv("VAPI_ASSISTANT_ID", "")
    phone_number_id = args.phone_number_id or os.getenv("VAPI_PHONE_NUMBER_ID", "")
    customer_number = args.customer_number or os.getenv("VAPI_TEST_NUMBER", "")
    if args.dry_run:
        _print_json(
            {
                "dryRun": True,
                "envReady": _redacted_env_state(),
                "customerNumberSet": bool(customer_number),
                "payload": outbound_call_payload(
                    assistant_id or "<assistant-id>",
                    phone_number_id or "<phone-number-id-or-single-vapi-number>",
                    customer_number or "<customer-e164-number>",
                ),
            }
        )
        return 0
    phone_number_id = phone_number_id or phone_number_id_from_env_or_single(api_key_from_env())
    _print_json(_redacted_call_record(create_outbound_call(api_key_from_env(), assistant_id, phone_number_id, customer_number)))
    return 0


def list_calls_command(args: argparse.Namespace) -> int:
    calls = list_calls(api_key_from_env(), limit=args.limit)
    _print_json(
        {
            "count": len(calls),
            "calls": [redacted_call_record(record) for record in calls],
        }
    )
    return 0


def _selected_phone_record(phone_numbers: list[dict[str, Any]], phone_number_id: str) -> dict[str, Any] | None:
    return next((record for record in phone_numbers if str(record.get("id", "")) == phone_number_id), None)


def verify_call_command(args: argparse.Namespace) -> int:
    result = _verify_recent_call_result(args)
    _print_json(result)
    return 0 if result["verified"] else 1


def _verify_recent_call_result(args: argparse.Namespace) -> dict[str, Any]:
    phone_number_id = args.phone_number_id or os.getenv("VAPI_PHONE_NUMBER_ID", "")
    if not phone_number_id:
        phone_number_id = phone_number_id_from_env_or_single(api_key_from_env())
    phone_numbers = list_phone_numbers(api_key_from_env())
    selected_phone = _selected_phone_record(phone_numbers, phone_number_id)
    attached_assistant_id = str(selected_phone.get("assistantId", "")) if selected_phone else ""
    assistant_id = args.assistant_id or attached_assistant_id
    calls = list_calls(api_key_from_env(), limit=args.limit)
    result = verify_recent_call(calls, assistant_id, phone_number_id)
    result["assistantIdSource"] = "argument" if args.assistant_id else "selected-phone-number"
    result["selectedPhoneNumberFound"] = bool(selected_phone)
    return result


def wait_call_command(args: argparse.Namespace) -> int:
    started_at = time.monotonic()
    attempts = 0
    last_result: dict[str, Any] = {}
    polling_errors: list[dict[str, Any]] = []
    while True:
        attempts += 1
        try:
            last_result = _verify_recent_call_result(args)
            if last_result["verified"]:
                last_result["wait"] = {
                    "status": "verified",
                    "attempts": attempts,
                    "elapsedSeconds": round(time.monotonic() - started_at, 3),
                    "pollingErrorCount": len(polling_errors),
                }
                _print_json(last_result)
                return 0
        except Exception as error:
            polling_errors.append(
                {
                    "attempt": attempts,
                    "errorType": error.__class__.__name__,
                }
            )
        elapsed = time.monotonic() - started_at
        if elapsed >= args.timeout:
            last_result["wait"] = {
                "status": "timeout",
                "attempts": attempts,
                "elapsedSeconds": round(elapsed, 3),
                "timeoutSeconds": args.timeout,
                "pollingErrorCount": len(polling_errors),
                "pollingErrors": polling_errors[-3:],
            }
            _print_json(last_result)
            return 1
        time.sleep(args.interval)


def list_phone_numbers_command(args: argparse.Namespace) -> int:
    phone_numbers = list_phone_numbers(api_key_from_env())
    _print_json(
        {
            "count": len(phone_numbers),
            "phoneNumbers": [redacted_phone_number_record(record) for record in phone_numbers],
        }
    )
    return 0


def preflight_command(args: argparse.Namespace) -> int:
    result = vapi_preflight(webhook_url=args.webhook_url)
    _print_json(result)
    return 0 if result["liveReady"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Wire PhoneBio to Vapi without storing secrets.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create-assistant", help="Create the PhoneBio assistant.")
    create.add_argument("--webhook-url", default=None)
    create.add_argument("--assign-phone", action="store_true")
    create.add_argument("--dry-run", action="store_true")
    create.set_defaults(func=create_assistant_command)

    assign = subparsers.add_parser("assign-phone", help="Assign an assistant to a Vapi phone number.")
    assign.add_argument("--assistant-id", default=None)
    assign.add_argument("--phone-number-id", default=None)
    assign.add_argument("--webhook-url", default=None)
    assign.add_argument("--dry-run", action="store_true")
    assign.set_defaults(func=assign_phone_command)

    list_numbers = subparsers.add_parser("list-phone-numbers", help="List Vapi phone numbers with phone values redacted.")
    list_numbers.set_defaults(func=list_phone_numbers_command)

    preflight = subparsers.add_parser("preflight", help="Check live Vapi readiness without exposing secrets.")
    preflight.add_argument("--webhook-url", default=None)
    preflight.set_defaults(func=preflight_command)

    outbound = subparsers.add_parser("outbound-call", help="Create an outbound test call.")
    outbound.add_argument("--assistant-id", default=None)
    outbound.add_argument("--phone-number-id", default=None)
    outbound.add_argument("--customer-number", default=None)
    outbound.add_argument("--dry-run", action="store_true")
    outbound.set_defaults(func=outbound_call_command)

    calls = subparsers.add_parser("list-calls", help="List recent Vapi calls with transcripts and numbers redacted.")
    calls.add_argument("--limit", type=int, default=10)
    calls.set_defaults(func=list_calls_command)

    verify = subparsers.add_parser("verify-call", help="Verify a recent call for the selected assistant/phone pair.")
    verify.add_argument("--assistant-id", default=None)
    verify.add_argument("--phone-number-id", default=None)
    verify.add_argument("--limit", type=int, default=10)
    verify.set_defaults(func=verify_call_command)

    wait = subparsers.add_parser("wait-call", help="Poll until a recent call matches the selected assistant/phone pair.")
    wait.add_argument("--assistant-id", default=None)
    wait.add_argument("--phone-number-id", default=None)
    wait.add_argument("--limit", type=int, default=10)
    wait.add_argument("--timeout", type=float, default=180.0)
    wait.add_argument("--interval", type=float, default=5.0)
    wait.set_defaults(func=wait_call_command)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        raise SystemExit(args.func(args))
    except Exception as error:
        print(f"Vapi wiring failed: {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
