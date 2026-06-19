#!/usr/bin/env python3
"""End-to-end demo stress test. Verifies every step of the live PhoneBio demo
and prints GREEN/RED per check. Re-runnable. Exit 0 only if all green.

Vapi API is called via curl (its CDN 403s python's user-agent); InsForge
function endpoints are called via urllib.
"""
import json, subprocess, sys, urllib.request

env = {}
for line in open(".env"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1); env[k] = v
KEY = env.get("VAPI_PRIVATE_KEY") or env.get("VAPI_API_KEY")
LLM = "https://qfdp5nuv.function2.insforge.app/phonebio-llm/chat/completions"
HOOK = "https://qfdp5nuv.function2.insforge.app/phonebio-vapi-webhook"
DASH = "https://qfdp5nuv.insforge.site"

results = []
def check(name, ok, detail=""):
    results.append(ok); print(("[GREEN] " if ok else "[RED]   ") + name + (f"  ::  {detail}" if detail else ""))

def curl_vapi(path):
    out = subprocess.run(["curl", "-s", f"https://api.vapi.ai{path}", "-H", f"Authorization: Bearer {KEY}"],
                         capture_output=True, text=True)
    try: return json.loads(out.stdout)
    except Exception: return {}

def post(url, payload, timeout=90):
    r = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=timeout).read())

def status(url):
    try: return urllib.request.urlopen(url, timeout=20).status
    except Exception as e: return getattr(e, "code", 0)

print("== 1. Vapi wiring ==")
nums = curl_vapi("/phone-number")
nmap = {p.get("number"): p.get("assistantId") for p in nums} if isinstance(nums, list) else {}
aid = nmap.get("+15415269723")
check("phonebio +15415269723 attached", bool(aid), str(aid))
check("test +15415269684 attached", bool(nmap.get("+15415269684")))
a = curl_vapi(f"/assistant/{aid}") if aid else {}
m = a.get("model", {})
sys_prompt = (m.get("messages") or [{}])[0].get("content", "")
check("brain = Nebius custom-llm", m.get("provider") == "custom-llm" and "phonebio-llm" in (m.get("url") or ""), f"{m.get('provider')} {m.get('model')}")
check("tools attached (>=5)", len(m.get("tools", [])) >= 5, str(len(m.get("tools", []))))
check("serverUrl = webhook", "phonebio-vapi-webhook" in ((a.get("server") or {}).get("url") or ""))
check("denoise on", a.get("backgroundDenoisingEnabled") is True)
check("EMERGENCY MODE prompt loaded", "EMERGENCY" in sys_prompt.upper())

print("== 2. InsForge backend ==")
fns = subprocess.run(["npx", "-y", "@insforge/cli", "functions", "list"], capture_output=True, text=True).stdout
check("phonebio-llm active", "phonebio-llm" in fns and "active" in fns)
check("phonebio-vapi-webhook active", "phonebio-vapi-webhook" in fns)
q = subprocess.run(["npx", "-y", "@insforge/cli", "db", "query",
     "select (select count(*) from protocols) p,(select count(*) from safety_sheets) s,(select count(*) from hardware_guides) h,(select count(*) from sensor_profiles) n", "--json"],
     capture_output=True, text=True).stdout
try:
    row = (json.loads(q) if q.strip().startswith("[") else json.loads(q).get("rows", [{}]))[0]
    pc, sc, hc, nc = (int(row.get(k, 0)) for k in ("p", "s", "h", "n"))
    check("DB seeded", pc >= 4 and sc >= 2 and hc >= 3 and nc >= 1, f"protocols={pc} sds={sc} hw={hc} sensors={nc}")
except Exception as e:
    check("DB seeded", False, str(e)[:60])

print("== 3. Dashboard ==")
check("dashboard 200", status(DASH) == 200)
check("edge page 200", status(DASH + "/edge.html") == 200)

print("== 4. Brain tool-calling (Nebius) ==")
TOOLS = [{"type": "function", "function": {"name": n, "description": d,
        "parameters": {"type": "object", "properties": {"substance": {"type": "string"}, "task": {"type": "string"},
        "device": {"type": "string"}, "symptom": {"type": "string"}, "sensor": {"type": "string"}, "reading": {"type": "string"}, "text": {"type": "string"}}}}}
    for n, d in [("get_protocol", "field biology protocol"), ("get_safety_sheet", "safety data sheet by substance"),
                 ("troubleshoot_hardware", "troubleshoot field hardware"), ("interpret_sensor_report", "interpret a sensor reading"),
                 ("compress_observation", "log a spoken observation")]]
r = post(LLM, {"stream": False, "temperature": 0.1, "messages": [
    {"role": "system", "content": "Use a tool when relevant."},
    {"role": "user", "content": "I spilled formaldehyde, what PPE and first aid?"}], "tools": TOOLS})
model = r.get("model", ""); tc = (r.get("choices") or [{}])[0].get("message", {}).get("tool_calls")
check("brain runs Llama-3.3-70B", "Llama-3.3-70B" in model, model)
check("brain emits tool_call", bool(tc), tc[0]["function"]["name"] if tc else "none")

print("== 5. Tools (webhook, grounded) ==")
def tool(name, params):
    r = post(HOOK, {"message": {"type": "tool-calls", "toolCallList": [{"id": "x", "name": name, "parameters": params}]}})
    res = r["results"][0]["result"]
    return res if isinstance(res, dict) else json.loads(res)
check("get_safety_sheet formaldehyde", (t := tool("get_safety_sheet", {"substance": "formaldehyde"})).get("status") == "ok" and "ormaldehyde" in (t.get("name") or ""), t.get("name", ""))
check("get_protocol pitfall", (t := tool("get_protocol", {"task": "pitfall trap ground beetle"})).get("status") == "ok", t.get("id", ""))
check("get_protocol emergency", (t := tool("get_protocol", {"task": "chemical spill fire emergency cannot reach ER", "hazard": "fire"})).get("id") == "field_emergency_response", t.get("id", ""))
check("get_protocol first-aid-kit", (t := tool("get_protocol", {"task": "first aid kit cut bleeding gauze bandage"})).get("id") == "first_aid_kit_use", t.get("id", ""))
check("troubleshoot gps", (t := tool("troubleshoot_hardware", {"device": "gps", "symptom": "no fix"})).get("status") == "ok", t.get("id", ""))
check("interpret barometer", (t := tool("interpret_sensor_report", {"sensor": "barometer", "reading": "1003 then 998 hPa"})).get("status") == "ok", t.get("id", ""))
check("compress_observation", bool((t := tool("compress_observation", {"text": "observed three juvenile specimens near burrow at 12 meters temperature 18 degrees"})).get("field_line")), t.get("field_line", ""))
check("escalation not_found", tool("get_safety_sheet", {"substance": "unobtanium zzz"}).get("status") == "not_found")

print("== 6. Full emergency 3-leg loop ==")
sysm = {"role": "system", "content": sys_prompt or "You are PhoneBio, field first-response."}
um = {"role": "user", "content": "I spilled formaldehyde and there's a small fire, I can't use my hands, I'm alone and can't reach 911."}
etools = [{"type": "function", "function": {"name": "get_safety_sheet", "description": "SDS by substance", "parameters": {"type": "object", "properties": {"substance": {"type": "string"}}}}}]
r1 = post(LLM, {"stream": False, "temperature": 0.2, "messages": [sysm, um], "tools": etools})
m1 = (r1.get("choices") or [{}])[0].get("message", {}); tc1 = m1.get("tool_calls")
ans = m1.get("content", "")
if tc1:
    hk = tool(tc1[0]["function"]["name"], json.loads(tc1[0]["function"]["arguments"]))
    asst = {"role": "assistant", "tool_calls": [{"id": tc1[0]["id"], "type": "function", "function": tc1[0]["function"]}]}
    tm = {"role": "tool", "tool_call_id": tc1[0]["id"], "content": json.dumps(hk)}
    r2 = post(LLM, {"stream": False, "temperature": 0.2, "max_tokens": 130, "messages": [sysm, um, asst, tm]})
    ans = (r2.get("choices") or [{}])[0].get("message", {}).get("content", "")
kw = ["ventilat", "evacuat", "fresh air", "water", "away", "supervisor", "poison", "fire", "stop", "extinguish"]
check("emergency loop gives safe action", any(k in ans.lower() for k in kw), ans[:90])

g = sum(results); t = len(results)
print(f"\n=== {g}/{t} GREEN ===")
sys.exit(0 if g == t else 1)
