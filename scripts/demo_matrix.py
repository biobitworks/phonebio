#!/usr/bin/env python3
"""Run the demo variation matrix end-to-end through the LIVE brain + tools.
Normal -> protocol -> SDS -> hardware -> sensor -> emergency. Prints the actual
spoken answer per turn (full brain -> tool -> brain loop), using the live
assistant's system prompt for fidelity.

    make demo-matrix   # or:  python3 scripts/demo_matrix.py
"""
import json, subprocess, urllib.request

env = {}
for line in open(".env"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1); env[k] = v
KEY = env.get("VAPI_PRIVATE_KEY") or env.get("VAPI_API_KEY")
LIVE = env.get("VAPI_ASSISTANT_ID")
LLM = "https://qfdp5nuv.function2.insforge.app/phonebio-llm/chat/completions"
HOOK = "https://qfdp5nuv.function2.insforge.app/phonebio-vapi-webhook"

TOOLS = [
    {"type": "function", "function": {"name": "get_protocol", "description": "field biology protocol", "parameters": {"type": "object", "properties": {"task": {"type": "string"}, "organism": {"type": "string"}, "hazard": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "get_safety_sheet", "description": "safety data sheet by substance", "parameters": {"type": "object", "properties": {"substance": {"type": "string"}, "hazard": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "troubleshoot_hardware", "description": "troubleshoot field hardware", "parameters": {"type": "object", "properties": {"device": {"type": "string"}, "symptom": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "interpret_sensor_report", "description": "interpret a phone sensor reading", "parameters": {"type": "object", "properties": {"sensor": {"type": "string"}, "reading": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "compress_observation", "description": "log a spoken observation", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}}}},
]


def sys_prompt():
    out = subprocess.run(["curl", "-s", f"https://api.vapi.ai/assistant/{LIVE}", "-H", f"Authorization: Bearer {KEY}"], capture_output=True, text=True).stdout
    try:
        return json.loads(out)["model"]["messages"][0]["content"]
    except Exception:
        return "You are PhoneBio, a hands-free field assistant. Use a tool when relevant; keep replies short."


def post(url, payload):
    r = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=90).read())


def tool(name, args):
    r = post(HOOK, {"message": {"type": "tool-calls", "toolCallList": [{"id": "x", "name": name, "parameters": args}]}})
    res = r["results"][0]["result"]
    return res if isinstance(res, str) else json.dumps(res)


def turn(system, user):
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    r1 = post(LLM, {"stream": False, "temperature": 0.2, "max_tokens": 130, "messages": msgs, "tools": TOOLS})
    m1 = (r1.get("choices") or [{}])[0].get("message", {})
    tc = m1.get("tool_calls")
    if not tc:
        return "(direct)", m1.get("content", "")
    name = tc[0]["function"]["name"]
    res = tool(name, json.loads(tc[0]["function"].get("arguments") or "{}"))
    msgs += [{"role": "assistant", "tool_calls": [{"id": tc[0]["id"], "type": "function", "function": tc[0]["function"]}]},
             {"role": "tool", "tool_call_id": tc[0]["id"], "content": res}]
    r2 = post(LLM, {"stream": False, "temperature": 0.2, "max_tokens": 130, "messages": msgs})
    return name, (r2.get("choices") or [{}])[0].get("message", {}).get("content", "")


MATRIX = [
    ("NORMAL", "Hi, I'm starting my field experiment and I can't use my hands. Can you help?"),
    ("PROTOCOL", "How do I set a pitfall trap for ground beetles?"),
    ("PROTOCOL", "Walk me through taking a surface water grab sample."),
    ("MSDS/SDS", "I'm working with formaldehyde, what PPE and hazards should I know?"),
    ("MSDS/SDS", "Is seventy percent ethanol a fire risk near a heat source?"),
    ("HARDWARE", "My GPS won't get a fix, what do I do?"),
    ("SENSOR", "My barometer read one thousand three then nine ninety eight over an hour, what does that mean?"),
    ("EMERGENCY", "I spilled formaldehyde and there's a small fire, I'm alone and can't reach 911."),
]
sp = sys_prompt()
for tier, u in MATRIX:
    name, ans = turn(sp, u)
    print(f"[{tier}] {u}")
    print(f"   tool: {name}")
    print(f"   says: {ans.strip()}\n")
