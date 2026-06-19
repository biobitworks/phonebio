"""End-to-end demo stress gate for PhoneBio.

This runner is intentionally redacted and conservative. It proves the demo
surfaces that can be tested before the real phone call, and reports the live
Vapi call as a separate gate.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DASHBOARD = "https://qfdp5nuv.insforge.site/dashboard.html"
PUBLIC_MANIFEST = "https://qfdp5nuv.insforge.site/manifest.webmanifest"

try:
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")
except Exception:
    pass


def read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def run_command(name: str, command: list[str], *, timeout: int = 90) -> dict[str, Any]:
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


def text_check(name: str, path: str, terms: list[str]) -> dict[str, Any]:
    text = read(path).lower()
    missing = [term for term in terms if term.lower() not in text]
    return {
        "name": name,
        "status": "pass" if not missing else "fail",
        "path": path,
        "missing": missing,
    }


def public_dashboard_check() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    try:
        html = httpx.get(PUBLIC_DASHBOARD, timeout=20).text
        manifest = httpx.get(PUBLIC_MANIFEST, timeout=20).json()
        script = httpx.get(PUBLIC_DASHBOARD.replace("dashboard.html", "dashboard.js"), timeout=20).text
    except (httpx.HTTPError, json.JSONDecodeError) as error:
        return {"name": "public_dashboard", "status": "fail", "error": error.__class__.__name__}
    checks.append({"item": "html_has_executorch_gate", "ok": "ExecuTorch gate" in html})
    checks.append({"item": "html_has_orchestrator", "ok": "Local Quantized Orchestrator" in html})
    checks.append({"item": "manifest_standalone", "ok": manifest.get("display") == "standalone"})
    checks.append({"item": "script_has_speaker_lane", "ok": "stage speakerphone echo" in script})
    checks.append({"item": "script_has_emergency_lane", "ok": "emergency_priority" in script})
    checks.append({"item": "script_has_executorch_route", "ok": "ExecuTorch local .pte" in script})
    return {"name": "public_dashboard", "status": "pass" if all(item["ok"] for item in checks) else "fail", "checks": checks}


def vapi_preflight_check() -> dict[str, Any]:
    if not (os.getenv("VAPI_PRIVATE_KEY") or os.getenv("VAPI_API_KEY")):
        return {"name": "vapi_preflight", "status": "blocked", "detail": "Vapi key not present in environment."}
    return run_command("vapi_preflight", ["make", "vapi-preflight"], timeout=90)


def vapi_call_check() -> dict[str, Any]:
    if os.getenv("PHONEBIO_CALL_VERIFIED") == "1" or os.getenv("PHONEBIO_LIVE_VAPI_VERIFIED") == "1":
        return {"name": "vapi_call_verified", "status": "pass", "detail": "PHONEBIO_CALL_VERIFIED is set."}
    if not (os.getenv("VAPI_PRIVATE_KEY") or os.getenv("VAPI_API_KEY")):
        return {"name": "vapi_call_verified", "status": "blocked", "detail": "No Vapi key; cannot verify call evidence."}
    result = run_command("vapi_call_verified", ["make", "vapi-verify-call"], timeout=90)
    if result["status"] == "fail":
        result["status"] = "blocked"
        result["detail"] = "No matching real call evidence yet. Place the demo call, then rerun."
    return result


def ollarma_review() -> dict[str, Any]:
    prompt = (
        "PhoneBio demo stress review. The live call is speaker-only, no touch, no headset. "
        "Sensors are pre-authorized before recording. Dashboard is public static demo with "
        "ExecuTorch gate, noisy_confirmation, and emergency_priority. Identify one blocker "
        "only if it prevents a recorded demo today; otherwise answer READY."
    )
    try:
        response = httpx.post("http://127.0.0.1:8484/chat", json={"prompt": prompt}, timeout=45)
        body = response.json()
    except (httpx.HTTPError, json.JSONDecodeError) as error:
        return {"name": "ollarma_local_review", "status": "blocked", "error": error.__class__.__name__}
    text = str(body.get("response", ""))
    return {
        "name": "ollarma_local_review",
        "status": "pass" if response.status_code == 200 and text else "blocked",
        "model": body.get("model"),
        "response": text[:800],
    }


def main() -> None:
    checks = [
        run_command("node_tests", ["npm", "test"], timeout=120),
        run_command("python_fieldbio_tests", ["python3", "-m", "pytest", "tests/test_fieldbio.py", "-q"], timeout=120),
        run_command("prefield_check", ["make", "prefield-check"], timeout=90),
        run_command("shorthand_stress", ["make", "shorthand-stress"], timeout=90),
        run_command("hosted_probe", ["make", "hosted-probe"], timeout=90),
        run_command("hosted_demo", ["make", "hosted-demo"], timeout=120),
        public_dashboard_check(),
        text_check(
            "speaker_only_docs",
            "docs/SPEAKER_ONLY_VOICE_DEMO.md",
            ["no touching the phone", "one-time pre-authorization", "sensor website boundary", "repeat"],
        ),
        text_check(
            "stage_guide_docs",
            "docs/STAGE_TEST_CALL_GUIDE.md",
            ["speaker only", "pre-authorized", "emergency services", "first-aid kit"],
        ),
        text_check(
            "assistant_prompt_constraints",
            "vapi/assistant.field-biology-worker.json",
            ["speaker-only", "no hands", "emergency services", "basic first-aid kit", "dense canopy"],
        ),
        text_check(
            "iphone_11_sensor_profile",
            "docs/IPHONE_11_FIELD_PROFILE.md",
            ["iphone 11", "lidar", "humidity sensor", "accelerometer", "barometer"],
        ),
        text_check(
            "sensor_matrix",
            "docs/SENSOR_TRIAGE_MATRIX.md",
            ["relative humidity", "lidar", "radar-like", "barometer boundary", "emergency_priority"],
        ),
        vapi_preflight_check(),
        vapi_call_check(),
        ollarma_review(),
    ]
    summary = {
        "pass": sum(1 for check in checks if check["status"] == "pass"),
        "blocked": sum(1 for check in checks if check["status"] == "blocked"),
        "fail": sum(1 for check in checks if check["status"] == "fail"),
    }
    report = {
        "project": "phonebio",
        "scenario": "speaker_only_pre_authorized_demo",
        "publicDashboard": PUBLIC_DASHBOARD,
        "checks": checks,
        "summary": summary,
        "demoReady": summary["fail"] == 0,
        "liveCallVerified": next(
            (check["status"] == "pass" for check in checks if check["name"] == "vapi_call_verified"),
            False,
        ),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["demoReady"] else 1)


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT))
    main()
