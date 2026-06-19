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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fieldbio.vapi_client import (
    api_key_from_env,
    assign_phone_number,
    assistant_payload,
    create_assistant,
    create_outbound_call,
    outbound_call_payload,
    phone_assignment_payload,
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
                "payload": phone_assignment_payload(assistant_id, args.webhook_url),
            }
        _print_json(result)
        return 0

    assistant = create_assistant(api_key_from_env(), payload)
    assistant_id = assistant.get("id")
    result: dict[str, object] = {"assistant": assistant}
    if args.assign_phone:
        result["phoneNumber"] = assign_phone_number(
            api_key_from_env(),
            os.getenv("VAPI_PHONE_NUMBER_ID", ""),
            assistant_id,
            args.webhook_url,
        )
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
                "assistantIdSet": bool(assistant_id),
                "payload": phone_assignment_payload(assistant_id or "<assistant-id>", args.webhook_url),
            }
        )
        return 0
    _print_json(assign_phone_number(api_key_from_env(), phone_number_id, assistant_id, args.webhook_url))
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
                    phone_number_id or "<phone-number-id>",
                    customer_number or "<customer-e164-number>",
                ),
            }
        )
        return 0
    _print_json(create_outbound_call(api_key_from_env(), assistant_id, phone_number_id, customer_number))
    return 0


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

    outbound = subparsers.add_parser("outbound-call", help="Create an outbound test call.")
    outbound.add_argument("--assistant-id", default=None)
    outbound.add_argument("--phone-number-id", default=None)
    outbound.add_argument("--customer-number", default=None)
    outbound.add_argument("--dry-run", action="store_true")
    outbound.set_defaults(func=outbound_call_command)
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
