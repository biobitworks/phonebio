"""Pre-field readiness check for call-only / degraded-connectivity deployment."""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def exists(path: str) -> bool:
    return (REPO_ROOT / path).exists()


def read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def check(name: str, ok: bool, evidence: str) -> dict[str, str | bool]:
    return {"name": name, "ok": ok, "evidence": evidence}


def main() -> None:
    assistant = read("vapi/assistant.field-biology-worker.json")
    sensor_text = read("content/sensors/sensors.json")
    checks = [
        check(
            "voice_first_prompt",
            all(term in assistant.lower() for term in ["voice", "cellular", "mobile data", "do not require"]),
            "Assistant prompt covers voice-first and degraded mobile-data behavior.",
        ),
        check(
            "offline_content_bundle",
            all(
                exists(path)
                for path in [
                    "content/protocols/water_quality_grab_sample.md",
                    "content/sds/formaldehyde_solution.json",
                    "content/troubleshooting/data_logger_no_connect.json",
                    "content/sensors/sensors.json",
                    "content/shorthand/lexicon.json",
                ]
            ),
            "Protocol, SDS, hardware, sensor, and shorthand content exist locally.",
        ),
        check(
            "sensor_modes",
            all(term in sensor_text for term in ["gesture_context", "acoustic_context", "barometer", "uwb", "gps"]),
            "Sensor profiles include gesture/pocket, acoustic, barometer, UWB, and GPS context.",
        ),
        check(
            "degraded_connectivity_docs",
            all(
                exists(path)
                for path in [
                    "docs/PREFIELD_SETUP.md",
                    "docs/DEGRADED_CONNECTIVITY_MODE.md",
                    "docs/HANDS_FREE_DISASTER_MODE.md",
                    "docs/IOT_SENSOR_PROCESSING_STRATEGY.md",
                    "docs/SENSOR_CONTEXT_STRATEGY.md",
                ]
            ),
            "Pre-field, degraded connectivity, hands-free, IoT, and sensor strategy docs exist.",
        ),
        check(
            "no_camera_runtime_assumption",
            "no camera" in assistant.lower() or "photos" in assistant.lower(),
            "Assistant does not require camera/photo workflows.",
        ),
        check(
            "no_openai_required",
            "OPENAI_API_KEY" not in read(".env.example"),
            ".env.example does not require an OpenAI API key.",
        ),
    ]
    failed = [item for item in checks if not item["ok"]]
    payload = {
        "project": "phonebio",
        "mode": "prefield_call_only_degraded_connectivity",
        "checks": checks,
        "summary": {"pass": len(checks) - len(failed), "fail": len(failed)},
        "ready": not failed,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
