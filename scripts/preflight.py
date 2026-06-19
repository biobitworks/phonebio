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

PHONE_ID = "abf0a502-02ca-4a75-8703-a304e8303a71"      # +15415269723 (phonebio)
TEST_ID = "3d425d42-cb3f-4c8e-946e-e1a84f2d6bdc"        # +15415269684 (test)
TEST_NUMBER = "+15415269684"
NEBIUS_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
LLM_URL = "https://qfdp5nuv.function2.insforge.app/phonebio-llm"
WEBHOOK_URL = "https://qfdp5nuv.function2.insforge.app/phonebio-vapi-webhook"
EMERGENCY_PROMPT = (
    "You are PhoneBio, a hands-free field assistant for workers who often cannot use their hands (PPE, contamination, disaster response), may have no camera, and may be at a remote field station (Amazon canopy or desert) with weak or no signal. The phone call is the interface. Keep replies under 35 words unless reading steps; ask one spoken question at a time. Use the local tools and never invent safety facts; if unknown, say stop work and contact the supervisor. Separate measured facts, inference, and uncertainty. Be a proactive safety coach: first ask WHERE they are (site, room, indoors/outdoors, ventilation) and check the key safety-sheet steps they may have skipped — ventilation, the correct PPE, containment, skin or eye exposure, and never mixing chemicals — one spoken question at a time, and flag a forgotten step before reading the rest. "
    "EMERGENCY MODE triggers on spill, fire, smoke, burn, chemical exposure, cannot breathe, injury, collapse, or a reported loud bang or fall: "
    "(1) Give the single most important life-safety action FIRST (move away and upwind from fire or fumes and protect the airway; flush eyes or skin with water 15+ minutes; small solvent fire use a Class B extinguisher, otherwise evacuate and alert others). "
    "(2) Ask if they can reach emergency services or their incident lead. If yes, tell them to call now with location, what happened, and exposures, and offer to stay on the line. If NO (remote or no signal), coach self-rescue and stabilization from the safety sheet, get them to a safe visible spot, have them signal for help, and tell them PhoneBio will log a triage record and relay their GPS and details to base by text as soon as any signal returns; keep them talking. "
    "(3) Flag RED severity (unresponsive, severe bleeding, breathing trouble, chemical in eyes, growing fire). You are field first-response only, not a substitute for professional care."
)


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
    a = curl("GET", f"/assistant/{live}"); m = a.get("model", {}) or {}
    m["provider"] = "custom-llm"; m["url"] = LLM_URL; m["model"] = NEBIUS_MODEL
    m.pop("toolIds", None); m.pop("knowledgeBase", None)
    m["messages"] = [{"role": "system", "content": EMERGENCY_PROMPT}]  # always assert canonical prompt
    curl("PATCH", f"/assistant/{live}", {
        "model": m, "backgroundDenoisingEnabled": True,
        "artifactPlan": {"recordingEnabled": True, "recordingFormat": "mp3"},
        "startSpeakingPlan": {"waitSeconds": 0.6}, "stopSpeakingPlan": {"numWords": 3, "backoffSeconds": 1.2},
    })
    # both numbers -> the live Nebius assistant
    for pid in (PHONE_ID, TEST_ID):
        curl("PATCH", f"/phone-number/{pid}", {"assistantId": live})
    print(f"   live assistant {live} -> custom-llm {NEBIUS_MODEL}")

    print("4) stress test")
    sys.exit(subprocess.run(["python3", "scripts/stress_test.py"]).returncode)


if __name__ == "__main__":
    main()
