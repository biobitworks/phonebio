# PhoneBio - LIVE Demo Script (in-person, to judges)

> This is the **live** run sheet. For the recorded video, see `DEMO_VIDEO_SCRIPT.md`.
> Two screens: **(A) the phone** for the real call and **(B) `live.html`** on the laptop/projector.

## 0. Pre-demo (60s before you start)
- Run `make demo-stress` and confirm **16 pass / 0 fail** and `demoReady: true`.
- Open **https://qfdp5nuv.insforge.site/live.html** on the laptop/projector.
- Optional phone sensor page: from the live page press **Open approved edge sensors**, then on the edge page press **Start browser quantized simulation** and **Arm sensors**.
- Phone: contact **PhoneBio** saved; speaker available; quiet-ish spot if possible.
- Say once, honestly: *"The phone call, InsForge tools, and Nebius 70B bursts are live. The dashboard sensor streams and edge model are labeled simulations for the stage."*

## 1. Hook (15s)
> "Field and disaster workers can't tap an app, can't use a camera, and barely have signal - but a **phone call** still gets through. PhoneBio is a hands-free call-in safety agent."

## 2. Start the call (15s)
- Say: **"Hey Siri, call PhoneBio."**
- If iOS does not start in speaker mode, tap speaker once before the no-touch portion.
- First line to the agent:
  > "PhoneBio, this is a live stage demo. I am hands-free, on speaker, and I need help with a field safety situation."

## 3. Live call - field note first (30s)
Say:

> "Field note. Observed three juvenile specimens near the burrow at 12 meters, 18 degrees. Save that as a compact field record."

Expected behavior:
- The agent uses `compress_observation`.
- It keeps the reply short and confirms the compact audit record.
- This proves hands-free field logging before the safety scenario.

## 4. Live call - formaldehyde location check (60s)
Say:

> "Low-level formaldehyde cleanup. No fire. No skin contact. I forgot the SDS location step. Ask me where I am relative to ventilation, eyewash, spill kit, exits, and other people before cleanup."

Expected behavior:
- The agent asks for location/context before cleanup: ventilation, eyewash, spill kit, exits, and nearby people.
- It uses the safety sheet path and keeps this as **AMBER**: contain, ventilate, PPE, do not escalate to emergency by default.

Answer when asked:

> "I am near open ventilation. Eyewash is across the room. The spill kit is behind me. The exit is clear. One person is nearby."

If you want the escalation beat, say:

> "Now there is a small fire and I cannot reach emergency services."

Expected behavior:
- **RED**: move away, warn others, avoid re-entry, relay location/hazard/injury facts. Same substance, harder tier.

## 5. Dashboard - edge to 70B interplay (45s)
On `live.html`, use the clearly labeled controls:
- **Live inputs**: press **Start live mic** only if you want laptop audio features.
- **Scripted demo controls**: press **Start scripted auto demo** for the clean judge-facing visualization.
- Optional single beat: press **script: formaldehyde location check** if you want the dashboard to match the call.

Narrate:

> "Routine field notes stay compact and cheap. Higher-risk spill prompts burst to the real Llama-70B on Nebius through the InsForge proxy. The dashboard shows edge-only count, escalated-to-70B count, and bytes sent to cloud."

## 6. Quick no-hallucination beat (15s)
- **No hallucination:** *"How do I neutralize a tank of [unknown chemical]?"* -> "Stop work, don't mix, call your supervisor."

## 7. Close (20s)
> "Three sponsors, one agent: **Vapi** is the always-available voice line, **InsForge** is the DB + tools + dashboard, **Nebius Llama-70B** is the brain. Hands-free, camera-free, voice-only-capable - and the same signals feed downstream disaster triage."

---

## If something wobbles LIVE (don't panic)
- **Call goes quiet**: pause, then say "Repeat. Speaker-only demo. Continue by voice only."
- **Agent loops on "one moment"**: stop the call beat and use **Start scripted auto demo** on the dashboard while narrating the fallback.
- **Tool is slow**: tools are bounded; keep the demo moving with the dashboard scripted controls.
- **Anything red locally**: run `make demo-stress` and use the visible pass/fail output.
- **No Wi-Fi for the dashboard**: the dashboard runs with labeled simulated data; the phone-call story still works over voice.
- **iPhone edge page**: `edge.html` runs the browser-local quantized simulation on iPhone; no WebGPU is required for the staged edge story.

## Honest live-vs-simulated labels
- **LIVE:** the phone call, the Nebius 70B bursts, the InsForge tool lookups.
- **SIMULATED (labeled on screen):** the dashboard sensor streams and browser-local quantized edge model.

## One-line close
> "Vapi is the resilient voice line, InsForge is the tools and demo surface, Nebius is the 70B brain, and the phone/browser edge layer decides what can stay local when the field link is weak."
