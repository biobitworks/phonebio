"""Before-recording gate for the PhoneBio demo.

This command repairs only non-secret demo defaults that are safe to reassert
when an editor stale buffer blanks them. It never prints or writes API keys,
phone numbers, transcripts, or recording URLs.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional dependency in some shells
    load_dotenv = None


REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = REPO_ROOT / ".env"

HOSTED_DEFAULTS = {
    "VAPI_WEBHOOK_URL": "https://qfdp5nuv.function2.insforge.app/phonebio-vapi-webhook",
    "VAPI_CUSTOM_LLM_URL": "https://qfdp5nuv.function2.insforge.app/phonebio-llm",
    "NEBIUS_BASE_URL": "https://api.tokenfactory.nebius.com/v1",
    "NEBIUS_MODEL": "Qwen/Qwen3-30B-A3B-Instruct-2507",
    "OLLAMA_BASE_URL": "http://localhost:11434/v1",
    "OLLAMA_MODEL": "qwen3:1.7b",
}

SECRET_OR_PRIVATE_KEYS = [
    "VAPI_PRIVATE_KEY",
    "VAPI_API_KEY",
    "VAPI_PHONE_NUMBER_ID",
    "VAPI_ASSISTANT_ID",
    "VAPI_TEST_NUMBER",
    "NEBIUS_API_KEY",
    "INSFORGE_API_KEY",
]


def parse_env(path: Path) -> tuple[list[str], dict[str, str]]:
    if not path.exists():
        return [], {}
    lines = path.read_text(encoding="utf-8").splitlines()
    values: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return lines, values


def write_env(path: Path, lines: list[str], updates: dict[str, str]) -> None:
    seen: set[str] = set()
    output: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in updates:
                output.append(f"{key}={updates[key]}")
                seen.add(key)
                continue
        output.append(line)
    if updates.keys() - seen:
        if output and output[-1].strip():
            output.append("")
        output.append("# Reasserted by scripts/recording_preflight.py")
        for key in sorted(updates.keys() - seen):
            output.append(f"{key}={updates[key]}")
    path.write_text("\n".join(output) + "\n", encoding="utf-8")


def blank_or_placeholder(value: str) -> bool:
    lowered = value.lower()
    return (
        not value.strip()
        or "your-tunnel-or-deploy.example.com" in lowered
        or "your-forwarded-or-hosted-url" in lowered
        or value.strip() == "change-me-long-random-string"
    )


def reassert_env(*, repair: bool) -> dict[str, Any]:
    lines, values = parse_env(ENV_PATH)
    repairs: dict[str, str] = {}
    for key, expected in HOSTED_DEFAULTS.items():
        if blank_or_placeholder(values.get(key, "")):
            repairs[key] = expected

    if values.get("NEBIUS_API_KEY") and blank_or_placeholder(values.get("LLM_PROVIDER_ORDER", "")):
        repairs["LLM_PROVIDER_ORDER"] = "nebius,local"
    elif blank_or_placeholder(values.get("LLM_PROVIDER_ORDER", "")):
        repairs["LLM_PROVIDER_ORDER"] = "local"

    if repair and repairs:
        write_env(ENV_PATH, lines, repairs)
        if load_dotenv:
            load_dotenv(ENV_PATH, override=True)
    elif load_dotenv:
        load_dotenv(ENV_PATH, override=True)

    _, refreshed = parse_env(ENV_PATH)
    secret_state = {
        key: {
            "set": bool((os.getenv(key) or refreshed.get(key, "")).strip()),
            "length": len((os.getenv(key) or refreshed.get(key, "")).strip()),
        }
        for key in SECRET_OR_PRIVATE_KEYS
    }
    configured_state = {
        key: {
            "set": bool((os.getenv(key) or refreshed.get(key, "")).strip()),
            "expected": (os.getenv(key) or refreshed.get(key, "")) == expected,
        }
        for key, expected in HOSTED_DEFAULTS.items()
    }
    return {
        "name": "env_reassert",
        "status": "pass" if not repairs or repair else "blocked",
        "envFilePresent": ENV_PATH.exists(),
        "repairMode": repair,
        "repairedKeys": sorted(repairs) if repair else [],
        "pendingRepairKeys": sorted(repairs) if not repair else [],
        "secrets": secret_state,
        "configured": configured_state,
        "providerOrder": os.getenv("LLM_PROVIDER_ORDER") or refreshed.get("LLM_PROVIDER_ORDER", ""),
    }


def run_command(name: str, command: list[str], *, timeout: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"name": name, "status": "fail", "detail": "timeout"}
    return {
        "name": name,
        "status": "pass" if completed.returncode == 0 else "fail",
        "returnCode": completed.returncode,
        "stdoutTail": completed.stdout[-1200:],
        "stderrTail": completed.stderr[-1200:],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the redacted PhoneBio before-recording preflight.")
    parser.add_argument("--repair", action="store_true", help="Repair safe non-secret .env defaults before checks.")
    parser.add_argument("--skip-checks", action="store_true", help="Only inspect/repair .env.")
    args = parser.parse_args()

    checks: list[dict[str, Any]] = [reassert_env(repair=args.repair)]
    if not args.skip_checks:
        checks.extend(
            [
                run_command("vapi_preflight", ["make", "vapi-preflight"], timeout=90),
                run_command("nebius_probe", ["make", "nebius-probe"], timeout=90),
                run_command("tts_stress", ["make", "tts-stress"], timeout=180),
                run_command("demo_stress", ["make", "demo-stress"], timeout=240),
            ]
        )

    summary = {
        "pass": sum(1 for check in checks if check["status"] == "pass"),
        "blocked": sum(1 for check in checks if check["status"] == "blocked"),
        "fail": sum(1 for check in checks if check["status"] == "fail"),
    }
    report = {
        "project": "phonebio",
        "mode": "before_recording",
        "checks": checks,
        "summary": summary,
        "readyToRecord": summary["fail"] == 0 and checks[0]["status"] == "pass",
        "commitGate": "Run the live call verifier first; commit/push only after the intended demo state is green.",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["readyToRecord"] else 1)


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT))
    main()
