#!/usr/bin/env python3
"""Idempotent pre-demo PREFLIGHT — the permanent fix.

Heals the two recurring drifts before every recording:
  - .env vars wiped by the stale VS Code buffer  -> re-asserts them
  - live brain flipped to Gemini by Codex regen   -> auto-discovers the live
    assistant from the phone number and forces it back to Nebius
Then mirrors the InsForge key and runs the full stress test (must be all green).

    make preflight        # or:  python3 scripts/preflight.py
"""
import json, os, re, subprocess, sys
from pathlib import Path

PHONE_ID = "abf0a502-02ca-4a75-8703-a304e8303a71"      # +15415269723 (phonebio)
TEST_ID = "3d425d42-cb3f-4c8e-946e-e1a84f2d6bdc"        # +15415269684 (test)
TEST_NUMBER = "+15415269684"
NEBIUS_MODEL = "Qwen/Qwen3-30B-A3B-Instruct-2507"   # FAST voice brain (~1s TTFT); 70B was 3s+/timeouts = stuck calls
NEBIUS_HEAVY_MODEL = "meta-llama/Llama-3.3-70B-Instruct"   # backend/dashboard burst only, never the live voice path
LLM_URL = "https://qfdp5nuv.function2.insforge.app/phonebio-llm"
WEBHOOK_URL = "https://qfdp5nuv.function2.insforge.app/phonebio-vapi-webhook"
ASSISTANT_TEMPLATE = Path("vapi/assistant.field-biology-worker.json")
FIRST_MESSAGE = "PhoneBio here. Take your time. Start with a field note or safety issue when ready."
EMERGENCY_PROMPT = """You are PhoneBio, a hands-free phone assistant for a field biology and lab-safety worker (no camera, weak signal, hands often busy).

Use a tool when relevant - always call the matching tool:
- a chemical or substance is named -> get_safety_sheet
- an observation or measurement to record -> compress_observation
- how to do a task or procedure -> get_protocol
- a device problem -> troubleshoot_hardware
- a sensor reading -> interpret_sensor_report
Call the tool first, then give a short spoken answer based on the result.

Keep replies under 35 words. Ask one question at a time. Never invent safety facts; if there is no record, say to stop work and call the supervisor. In an emergency (fire, smoke, exposure, injury, collapse), give the single most important life-safety action first."""


def read_env():
    e = {}
    if os.path.exists(".env"):
        for line in open(".env"):
            line = line.rstrip("\n")
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1); e[k] = v
    return e


def set_env(updates):
    s = open(".env").read() if os.path.exists(".env") else ""
    for k, v in updates.items():
        s = re.sub(rf'(?m)^{k}=.*$', f'{k}={v}', s) if re.search(rf'(?m)^{k}=', s) else s.rstrip() + f'\n{k}={v}\n'
    open(".env", "w").write(s)


def main():
    print("1) mirror InsForge key + re-assert env")
    pj = json.load(open(".insforge/project.json"))
    set_env({
        "INSFORGE_API_KEY": pj.get("api_key", ""), "INSFORGE_BASE_URL": pj.get("oss_host", ""),
        "VAPI_PHONE_NUMBER_ID": PHONE_ID, "VAPI_TEST_NUMBER": TEST_NUMBER,
        "NEBIUS_MODEL": NEBIUS_MODEL, "NEBIUS_BASE_URL": "https://api.tokenfactory.nebius.com/v1/",
        "NEBIUS_HEAVY_MODEL": NEBIUS_HEAVY_MODEL,
        "LLM_PROVIDER_ORDER": "local", "OLLAMA_MODEL": "qwen3:1.7b",
        "PUBLIC_BASE_URL": "https://qfdp5nuv.function2.insforge.app",
        "VAPI_WEBHOOK_URL": WEBHOOK_URL, "VAPI_CUSTOM_LLM_URL": LLM_URL,
    })
    env = read_env()
    KEY = env.get("VAPI_PRIVATE_KEY") or env.get("VAPI_API_KEY")
    if not KEY:
        print("   !! VAPI_PRIVATE_KEY/VAPI_API_KEY missing in .env — add it and re-run"); sys.exit(2)

    def curl(method, path, body=None):
        cmd = ["curl", "-s", "-X", method, f"https://api.vapi.ai{path}", "-H", f"Authorization: Bearer {KEY}"]
        if body is not None:
            cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
        out = subprocess.run(cmd, capture_output=True, text=True).stdout
        try: return json.loads(out)
        except Exception: return {}

    print("2) re-assert Nebius model secret + redeploy proxy")
    subprocess.run(["npx", "-y", "@insforge/cli", "secrets", "update", "NEBIUS_MODEL", "--value", NEBIUS_MODEL, "-y"], capture_output=True)
    subprocess.run(["npx", "-y", "@insforge/cli", "secrets", "update", "NEBIUS_HEAVY_MODEL", "--value", NEBIUS_HEAVY_MODEL, "-y"], capture_output=True)
    subprocess.run(["npx", "-y", "@insforge/cli", "functions", "deploy", "phonebio-llm", "--file", "functions/phonebio-llm.ts"], capture_output=True)

    print("3) discover live assistant from the phone number + force Nebius brain")
    nums = curl("GET", "/phone-number")
    live = None
    for p in (nums if isinstance(nums, list) else []):
        if p.get("number") == "+15415269723":
            live = p.get("assistantId")
    if not live:
        print("   !! +15415269723 has no assistant attached"); sys.exit(2)
    set_env({"VAPI_ASSISTANT_ID": live})
    template = json.load(open(ASSISTANT_TEMPLATE))
    template_model = template.get("model", {}) or {}
    a = curl("GET", f"/assistant/{live}"); m = a.get("model", {}) or {}
    m["provider"] = "custom-llm"; m["url"] = LLM_URL; m["model"] = NEBIUS_MODEL
    m.pop("toolIds", None); m.pop("knowledgeBase", None)
    m["messages"] = [{"role": "system", "content": EMERGENCY_PROMPT}]  # always assert canonical prompt
    m["tools"] = template_model.get("tools", [])  # always restore the complete live tool set
    curl("PATCH", f"/assistant/{live}", {
        "firstMessage": FIRST_MESSAGE,
        "model": m, "backgroundDenoisingEnabled": True,
        "artifactPlan": {"recordingEnabled": True, "recordingFormat": "mp3"},
        "startSpeakingPlan": {"waitSeconds": 1.4}, "stopSpeakingPlan": {"numWords": 5, "backoffSeconds": 2.0},
    })
    # both numbers -> the live Nebius assistant
    for pid in (PHONE_ID, TEST_ID):
        curl("PATCH", f"/phone-number/{pid}", {"assistantId": live})
    print(f"   live assistant {live} -> custom-llm {NEBIUS_MODEL}")

    print("4) re-assert reusable Vapi tools")
    subprocess.run(["python3", "scripts/upsert_vapi_tools.py"], check=True)

    print("5) stress test")
    sys.exit(subprocess.run(["python3", "scripts/stress_test.py"]).returncode)


if __name__ == "__main__":
    main()
