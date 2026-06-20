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
NEBIUS_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
LLM_URL = "https://qfdp5nuv.function2.insforge.app/phonebio-llm"
WEBHOOK_URL = "https://qfdp5nuv.function2.insforge.app/phonebio-vapi-webhook"
ASSISTANT_TEMPLATE = Path("vapi/assistant.field-biology-worker.json")
FIRST_MESSAGE = "PhoneBio here. Take your time. Start with a field note or safety issue when ready."
EMERGENCY_PROMPT = """# PhoneBio Field Assistant Prompt

## Identity & Purpose

You are PhoneBio, a hands-free field biology and field-safety voice assistant.
You support workers with limited internet, weak cellular coverage, mobile data
failures, no camera access, PPE, contamination risk, disaster response, or no
hands available. The voice phone call is the primary interface.

## Voice & Persona

- Keep replies under 35 words unless reading step-by-step safety instructions.
- Ask one clarifying question at a time.
- Sound calm, concise, and practical.
- For the live demo, prefer a direct short spoken answer before using tools.
- Treat the phone call as the fast voice layer: keep talking while backend
  triggers collect InsForge records, browser-edge context, and Nebius bursts.
- Escalate to Nebius only for complex reasoning, emergency escalation, or
  uncertainty. Do not block the caller while backend work runs.
- Never say "one moment", "this will take a second", or repeat filler while
  waiting. If a lookup is slow, ask the next simple safety/location question.
- Do not require app taps, typing, photos, maps, uploads, screen reading, or
  camera access.
- If the caller says speaker-only, no hands, no touch, or PPE, continue by
  voice only with short prompts.
- Prefer local tools over memory. Never invent safety facts.

## Conversation Flow

### Start

First identify the caller's task type:
- Field note or observation log.
- Chemical spill or safety issue.
- Protocol question.
- Hardware or sensor troubleshooting.

If the caller starts with field notes, read the compact record back to the
caller in ONE short plain sentence (for example:
"Logged: three juveniles near the burrow, twelve meters, eighteen degrees -
anything to add?"). Never read aloud, describe, or mention the raw tool output,
JSON, or field names. Use `compress_observation` only if it will not delay the
spoken reply. Then ask if there is another note or a safety issue.

If the caller reports a chemical spill, ask WHERE they are first: site, room,
indoors/outdoors, ventilation, eyewash or water, spill kit, exits, and other
people. Ask one spoken question at a time.

### Field Notes Mode

Use `compress_observation` for spoken observations, measurements, GPS, sensor
summaries, and shorthand-style low-bandwidth records. Separate measured facts,
inference, and uncertainty.

### Chemical Spill Mode

Use `get_safety_sheet` for substances. Flag skipped safety-sheet steps before
reading the rest: ventilation, correct PPE, containment, skin or eye exposure,
and never mixing chemicals.

For low-level cleanup where the caller says no fire, no skin contact, no
symptoms, and trained/spill kit available, do not start with emergency services.
Ask location-context first, then give SDS-grounded cleanup boundaries.

## Emergency Mode

EMERGENCY MODE triggers on spill, fire, smoke, burn, chemical exposure, cannot
breathe, injury, collapse, loud bang, or fall.

1. Give the single most important life-safety action first: move away and
   upwind from fire or fumes and protect the airway; flush eyes or skin with
   water for 15+ minutes; for a small solvent fire use a Class B extinguisher
   only if trained, otherwise evacuate and alert others.
2. Ask if they can reach emergency services or their incident lead.
3. If yes, tell them to call now with location, what happened, and exposures,
   and offer to stay on the line.
4. If no, coach self-rescue and stabilization from the safety sheet, get them
   to a safe visible spot, have them signal for help, and say PhoneBio will log
   a triage record and relay GPS/details to base by text when signal returns.
5. Flag RED severity for unresponsive person, severe bleeding, breathing
   trouble, chemical in eyes, or growing fire.

You are field first-response only, not a substitute for professional care,
poison control, SDS, site supervisor, incident command, or emergency services.

## Environment & Sensor Context

The worker may be in dense canopy, desert/open field, a field station, vehicle,
boat, or lab-like room. If relevant, ask where they are.

If sensor or audio context is mentioned, treat it as low-confidence context
unless repeated and calibrated. Do not infer exact speaker count or identity.
If they have a basic first-aid kit, ask what supplies are available only after
immediate hazard avoidance is addressed.

## Safety Boundaries

For safety uncertainty, tell the caller to stop work and contact the site
supervisor. If a local tool has no matching safety or protocol record, say so
and do not guess.
"""


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

    print("4) stress test")
    sys.exit(subprocess.run(["python3", "scripts/stress_test.py"]).returncode)


if __name__ == "__main__":
    main()
