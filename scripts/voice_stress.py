#!/usr/bin/env python3
"""Voice-path stress test: macOS `say` (TTS) -> whisper (STT) -> Nebius brain.

A proxy for the live phone path (Vapi's STT differs, but this catches whether
scientific terms survive speech recognition and the agent still routes to a
tool). Run before the demo.

    make voice-stress   # or:  python3 scripts/voice_stress.py
"""
import json, os, subprocess, urllib.request

env = {}
for line in open(".env"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1); env[k] = v
LLM = "https://qfdp5nuv.function2.insforge.app/phonebio-llm/chat/completions"
TOOLS = [{"type": "function", "function": {"name": n, "description": d, "parameters": {"type": "object",
        "properties": {"substance": {"type": "string"}, "task": {"type": "string"}, "device": {"type": "string"},
        "sensor": {"type": "string"}, "reading": {"type": "string"}, "text": {"type": "string"}}}}}
    for n, d in [("get_protocol", "field protocol"), ("get_safety_sheet", "safety data sheet by substance"),
                 ("troubleshoot_hardware", "troubleshoot hardware"), ("interpret_sensor_report", "interpret sensor reading"),
                 ("compress_observation", "log a spoken observation")]]


def brain(text):
    r = urllib.request.Request(LLM, data=json.dumps({"stream": False, "temperature": 0.1, "tools": TOOLS,
        "messages": [{"role": "system", "content": "Use a tool when relevant."}, {"role": "user", "content": text}]}).encode(),
        headers={"Content-Type": "application/json"})
    d = json.loads(urllib.request.urlopen(r, timeout=60).read())
    return (d.get("choices") or [{}])[0].get("message", {}).get("tool_calls")


SCENARIOS = [
    ("get_safety_sheet", "I spilled formaldehyde on the bench, what PPE and first aid?"),
    ("get_protocol", "How do I set a pitfall trap for ground beetles?"),
    ("troubleshoot_hardware", "My GPS won't get a fix."),
    ("interpret_sensor_report", "My barometer read one thousand three then nine ninety eight, what does that mean?"),
]
os.makedirs("demo_audio", exist_ok=True)
passed = 0
for i, (expect, text) in enumerate(SCENARIOS):
    aiff = f"demo_audio/scn{i}.aiff"
    subprocess.run(["say", "-o", aiff, text], check=True)
    subprocess.run(["whisper", aiff, "--model", "tiny.en", "--language", "en", "--fp16", "False",
                    "--output_format", "txt", "--output_dir", "demo_audio"], capture_output=True, text=True)
    txtf = aiff[:-5] + ".txt"
    heard = open(txtf).read().strip() if os.path.exists(txtf) else "(whisper failed)"
    tc = brain(heard)
    name = tc[0]["function"]["name"] if tc else "NONE"
    ok = bool(tc)
    passed += ok
    print(("[GREEN] " if ok else "[RED]   ") + f"SAID: {text}")
    print(f"        HEARD: {heard}")
    print(f"        TOOL:  {name}  (expected ~{expect})")
print(f"\n=== voice path: {passed}/{len(SCENARIOS)} routed to a tool ===")
