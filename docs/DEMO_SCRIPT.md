# PhoneBio — Demo Run Sheet + 3-Minute Video Plan

> ⭐ **Reference recording (best call session):** [`media/demo-2026-06-19-1515.mov`](../media/demo-2026-06-19-1515.mov)

**Stack on screen:** Vapi (phone) → **Nebius Llama-3.3-70B** via an InsForge edge proxy → InsForge tools + Postgres + hosting. **No OpenAI. Voice-only-capable (no caller data). Hands-free, camera-free.**
**Call-in:** **+1 541‑526‑9723** (backup line +1 541‑526‑9684) · **"Hey Siri, call PhoneBio"** · **Dashboard:** https://qfdp5nuv.insforge.site/live.html

---

## Scene (OBS, 1920×1080)
- **Browser Source → `https://qfdp5nuv.insforge.site/live.html`** (right ⅔). Right-click → **Interact**; press **▶ Auto demo** or click buttons. *(Simulated sensor data — labeled — so it runs with no real sensors.)*
- **iPhone screen recording** of the real call (left ⅓). **Webcam** PIP corner.
- Pre-flight before rolling: `make preflight` → **23/23 GREEN**. Clean audio after: `make recording`.

## A. The call beats (what to say → what it does)
**0. Hands-free start:** "Hey Siri, call PhoneBio." → *"PhoneBio here. Tell me the task, material, or device, and what changed."*

**1. Proactive coach (asks where you are):** "I spilled a little formaldehyde on the bench."
> Agent asks **WHERE/ventilation** and flags a forgotten step before reading steps → `get_safety_sheet` → PPE + **spill cleanup** (absorb, ventilate, don't drain) + first aid. Tier **AMBER** (contain + PPE).

**2. Severity gradation → emergency:** "Now there's a small fire and I can't reach 911."
> Tier **RED** → life-safety **first** ("move away/upwind, protect airway"), then the **can't-reach-ER** path (self-rescue + log + relay GPS). Same substance, harder tier.

**3. First-aid kit (physical prop):** "I have my first aid kit — what do I use?"
> `get_protocol` → names the items in a basic kit, hands-free; improvises if one's missing.

**4. Hardware / sensor (camera-free):** "My GPS won't get a fix" · "barometer read 1003 then 998."
> `troubleshoot_hardware` / `interpret_sensor_report` → ordered steps / weather-trend warning with honest error bars.

**5. Hands-free log → shorthand:** "Log this: observed three juvenile specimens near the burrow at 12 meters, 18 degrees."
> `compress_observation` → `obs thr juv spcmns near brw ~ 12 m tmp 18 deg` + measurements; ~50% smaller, fits one SMS.

**6. Trust beat (no hallucination):** "How do I neutralize a tank of [unknown chemical]?"
> *not found* → "Stop work, don't mix, contact your supervisor." Refuses to guess.

## B. The dashboard beats (live.html, Interact / Auto demo)
- **Edge ⇄ 70B interplay:** routine/sensor → handled at **EDGE** (offline, ~ms); **EMERGENCY** → escalates to **Llama-70B** (cloud lane fires) — tally shows *edge-only vs escalated vs bytes-to-cloud*.
- **Shorthand efficiency + lab jargon:** % smaller, "fits 1 SMS", and the lab-term map (centrifuge→cfg, pcr, formaldehyde→form…) highlighting used terms.
- **Bandwidth tags:** each sensor labeled EDGE (high raw bw) vs cloud-ok (tiny).

## C. 3-minute video plan (180s)
| Time | Visual | Narration |
|---|---|---|
| 0:00–0:15 | gloved worker, bad signal, no camera | "Field & disaster workers can't tap apps or use a camera, and barely have signal — but a **phone call** gets through." |
| 0:15–0:30 | title + stack | "**PhoneBio**: call in for protocols, safety sheets, hardware, sensor triage. Brain = **Nebius Llama-70B**, backend = **InsForge**, phone = **Vapi**. No OpenAI." |
| 0:30–1:00 | call beat 1+2 + dashboard | "It asks *where she is*, pulls the real safety sheet, and as it escalates from spill to **fire**, the triage jumps **AMBER→RED**." |
| 1:00–1:30 | dashboard interplay | "Routine stays on the **on-device quantized** model — offline. Only the emergency **escalates to the 70B**. That's the bandwidth play." |
| 1:30–2:00 | shorthand beat 5 | "Hands-free, she just talks; we compress it Gregg-style into a record that **survives a weak link** and reads back." |
| 2:00–2:30 | beat 3 (first-aid kit) + beat 6 | "It walks her through her kit by voice — and when it doesn't know, it says **stop work, call your supervisor**." |
| 2:30–3:00 | map + close | "Voice-only, hands-free, camera-free — feeding **downstream disaster triage**. Built with Vapi · InsForge · Nebius. github.com/biobitworks/phonebio" |

**60-sec cut:** hook (0:10) → spill→fire gradation (0:25) → shorthand (0:15) → close (0:10).
**Trim priority:** beats **1→2 (gradation)**, **5 (shorthand)**, **6 (no-hallucination)** are the strongest.
