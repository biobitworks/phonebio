# PhoneBio — Demo Call Script + 3-Minute Video Plan

**Call the live agent:** **+1 541‑526‑9723** (phonebio line). Speak naturally; wait
for the agent to finish before replying. Backup line: +1 541‑526‑9684 (not attached).

**Stack on screen (the story):** Vapi (phone) → Nebius GPU brain (Qwen3-30B) via an
InsForge edge proxy → InsForge tools + Postgres. **No OpenAI. Runs on a plain voice
call (no data needed on the caller's side). Hands-free, camera-free.**

---

## A. Call script — scenarios with variations (record several, keep best takes)

Each scenario lists what to SAY (with variations) and what the agent should DO.
Pause ~1s after the agent speaks so cuts are clean.

### 0. Opener (it answers)
> *Agent:* "PhoneBio here. Tell me the field task, material or device, and what changed."

### 1. Safety Data Sheet (chemical hazard)
- "I spilled formaldehyde on the bench — what PPE and first aid?"
- *var:* "Got formalin on my glove, what do I do?"
- *var:* "Seventy percent ethanol spill near a heat source — is that dangerous?"
> *Does:* `get_safety_sheet` → PPE (nitrile gloves, goggles, face shield), eye/skin rinse 15 min, ventilation, poison control. Cites it's a field quick-reference, not the official SDS.

### 2. Protocol lookup
- "How do I set a pitfall trap for ground beetles?"
- *var:* "Walk me through taking a surface water grab sample."
> *Does:* `get_protocol` → flush-set cups + preservative + raised cover + georeference (trap); rinse 3x, fill from below surface upstream, no headspace, cool & dark (water).

### 3. Hardware troubleshooting (old/field gear)
- "My GPS won't get a fix."
- *var:* "The Bluetooth data logger keeps dropping the connection."
> *Does:* `troubleshoot_hardware` → ordered checks (open sky / wait 60–90s / high-accuracy mode …), and a camera-free fallback (landmark + bearing).

### 4. Sensor interpretation (camera-free, read aloud)
- "My barometer read 1003 then 998 over an hour — what does that mean?"
- *var:* "How accurate is the phone accelerometer for leveling a scope?"
> *Does:* `interpret_sensor_report` → relative-altitude ±1 m, flags a falling-pressure / weather-trend warning, gives confidence + that caller readings aren't calibrated instruments.

### 5. Hands-free field log → shorthand (the wow)
- "Log this: observed three juvenile specimens near the burrow at approximately 12 meters, temperature 18 degrees."
> *Does:* `compress_observation` → stores `obs thr juv spcmns near brw ~ 12 m tmp 18 deg` + structured measurements; can read it back verbatim. **Show the row appearing in the InsForge DB.**

### 6. Safety escalation (the trust moment — no hallucination)
- "How do I neutralize a tank of [obscure/unknown chemical]?"
> *Does:* returns *not found* → "Stop work, isolate if safe, don't mix chemicals, contact your supervisor / incident lead." **It refuses to guess** — show this; it's the rigor beat.

---

## B. 3-minute video plan (180s, shot-by-shot)

Format suggestion: **split screen** — left = phone on speaker (or a call-UI), right
= a screen recording of the InsForge dashboard (DB rows / function logs updating).
Add captions for every spoken line (field audio is noisy on purpose = authentic).

| Time | Visual | Narration / on-screen text |
|---|---|---|
| 0:00–0:15 | Field worker in gloves/PPE, phone in pocket, bad-signal bars, no camera allowed | "Field and disaster workers can't tap apps, can't use a camera, and barely have a signal — but a **phone call** still gets through." |
| 0:15–0:30 | Title card + architecture lower-third | "**PhoneBio**: call in, get protocols, safety sheets, hardware help, sensor guidance. Brain on **Nebius GPU**, backend on **InsForge**, phone via **Vapi**. No OpenAI." |
| 0:30–0:55 | Live call — **Scenario 1 (formaldehyde)**; right side shows the tool call + SDS row | "Real call. It pulls the safety sheet from our database and tells her exactly what PPE and first aid — grounded, not guessed." |
| 0:55–1:20 | **Scenario 3 (GPS/logger)** | "Old gear acting up in the field? Step-by-step troubleshooting, with a camera-free fallback." |
| 1:20–1:45 | **Scenario 4 (barometer)** | "No camera — so the phone's other sensors do the work. It interprets a barometer trend and flags incoming weather, with honest error bars." |
| 1:45–2:10 | **Scenario 5 (shorthand)**; right side shows the compact log line write to InsForge | "Hands-free, she just talks. We compress it — Gregg-shorthand style — into a tiny structured record that survives a weak link, and read it right back." |
| 2:10–2:30 | **Scenario 6 (escalation)** | "And when it doesn't know? It says **stop work, call your supervisor** — it refuses to hallucinate safety advice." |
| 2:30–2:50 | Map/diagram: voice-only call + offline buffer + sensor fusion → triage board | "It runs on a **voice-only** line with no data, hands-free under PPE — and the same sensor signals feed **downstream disaster triage**." |
| 2:50–3:00 | Close card: repo URL + stack logos | "Built in a day — Claude + Codex pair-programming. Vapi · InsForge · Nebius. github.com/biobitworks/phonebio." |

### Recording tips
- Put the phone on **speaker**; record in a quiet room, then add light "field" ambience under it.
- Screen-record the **InsForge dashboard** (insforge.dev → project phonebio) and `npx @insforge/cli logs function.logs` so viewers see tools firing live.
- Keep each agent answer short (system prompt already caps ~35 words) → tight cuts.
- Have the **number on screen** early; show a real inbound call.
- Best order for impact: **1 → 5 → 6** are the strongest three if you need to trim.

### If you only have 60 seconds
Hook (0:10) → Scenario 1 SDS (0:20) → Scenario 5 shorthand (0:15) → Scenario 6 escalation (0:10) → close (0:05).
