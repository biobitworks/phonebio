"""Send first-time PhoneBio demo links through macOS Messages.

The recipient is read from --to, DEMO_SMS_TO, or VAPI_TEST_NUMBER. The script
does not print phone numbers, API keys, transcripts, or message contents unless
--dry-run is used.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")
except Exception:
    pass


MESSAGE = """PhoneBio demo setup

1. Save contact: PhoneBio
2. Open dashboard: https://qfdp5nuv.insforge.site
3. Add to iPhone Home Screen as PhoneBio
4. Optional edge orchestrator: https://qfdp5nuv.insforge.site/edge.html
5. Pre-authorize permissions before recording
6. During take: speaker only, no touch

Script line:
PhoneBio, I cannot use my hands. I am on speaker only. I am at a remote field station and need help triaging an experiment incident.
"""


def recipient_from_env() -> str:
    return (os.getenv("DEMO_SMS_TO") or os.getenv("VAPI_TEST_NUMBER") or "").strip()


def redacted(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) <= 4:
        return "set" if cleaned else "missing"
    return f"***{cleaned[-4:]}"


def send_with_messages(recipient: str, body: str) -> tuple[bool, str]:
    script = """
on run argv
  set targetBuddyId to item 1 of argv
  set messageBody to item 2 of argv
  tell application "Messages"
    repeat with serviceKind in {iMessage, SMS}
      try
        set targetService to first service whose service type = serviceKind
        set targetBuddy to buddy targetBuddyId of targetService
        send messageBody to targetBuddy
        return "sent"
      end try
    end repeat
  end tell
  return "no_messages_service"
end run
"""
    result = subprocess.run(
        ["osascript", "-e", script, recipient, body],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        return False, result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "osascript_failed"
    return result.stdout.strip() == "sent", result.stdout.strip() or "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description="Send PhoneBio demo setup links via macOS Messages.")
    parser.add_argument("--to", default=recipient_from_env(), help="Recipient phone number or iMessage address.")
    parser.add_argument("--dry-run", action="store_true", help="Show redacted target and message body without sending.")
    args = parser.parse_args()

    if not args.to:
        print(
            "No demo recipient configured. Set DEMO_SMS_TO in .env or run: "
            "python3 scripts/send_demo_links.py --to '+1...'",
            file=sys.stderr,
        )
        raise SystemExit(2)

    if args.dry_run:
        print(f"recipient={redacted(args.to)}")
        print(MESSAGE)
        return

    ok, detail = send_with_messages(args.to, MESSAGE)
    print({"sent": ok, "recipient": redacted(args.to), "detail": detail})
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
