# PhoneBio — LIVE Demo Script (in-person, to judges)

> This is the **live** run sheet. For the recorded video, see `DEMO_VIDEO_SCRIPT.md`.
> Two screens: **(A) the phone** (real call) · **(B) `live.html`** on a laptop/projector.

## 0. Pre-demo (60s before you start)
- `make preflight` → wait for **23/23 GREEN** (re-asserts Nebius brain + everything).
- Open **https://qfdp5nuv.insforge.site/live.html** on the laptop/projector.
- Phone: contact **PhoneBio** saved; ringer/speaker on; quiet-ish spot.
- Say once, honestly: *"Sensors on the dashboard are simulated and labeled; the phone call and the 70B answers are live."*

## 1. Hook (15s)
> "Field and disaster workers can't tap an app, can't use a camera, and barely have signal — but a **phone call** still gets through. PhoneBio is a hands-free call-in safety agent."

## 2. Live call — the spill→fire gradation (60s)
- **"Hey Siri, call PhoneBio."** (phone on speaker, don't touch it)
- Say: *"I spilled a little formaldehyde on the bench."*
  → it **asks where you are** (ventilation/eyewash/exits) and gives SDS + cleanup → tier **AMBER**.
- Say: *"Now there's a small fire and I can't reach 911."*
  → **RED**: life-safety first, then the **can't-reach-ER** self-rescue + relay path. *Same substance, harder tier.*

## 3. Dashboard — edge ⇄ 70B interplay (45s)
On `live.html`, press **▶ Auto demo** (or click EMERGENCY):
- Routine/sensor → handled on the **edge** (browser-local quantized **simulation**, offline, runs on a phone).
- **EMERGENCY → bursts to the real Llama‑70B on Nebius** (cloud lane lights up + bytes-on-the-wire).
- Point out: *"Cheap and offline at the edge; the big GPU only when it matters."*

## 4. Two quick proof beats (30s)
- **Shorthand:** *"Log this: three juveniles near the burrow at 12 meters, 18 degrees."* → ~50% smaller, fits one SMS.
- **No hallucination:** *"How do I neutralize a tank of [unknown chemical]?"* → "Stop work, don't mix, call your supervisor."

## 5. Close (20s)
> "Three sponsors, one agent: **Vapi** is the always-available voice line, **InsForge** is the DB + tools + dashboard, **Nebius Llama‑70B** is the brain. Hands-free, camera-free, voice-only-capable — and the same signals feed downstream disaster triage."

---

## If something wobbles LIVE (don't panic)
- **Call goes quiet** → the proxy now returns a **spoken fallback** (never silence); just keep talking.
- **A tool is slow** → all tools are bounded (≤4s), can't hang.
- **Anything red** → `make preflight` re-greens it in one command.
- **No Wi-Fi for the dashboard** → it runs on **simulated data**, so it animates regardless; the phone call rides the voice channel.
- **iPhone** → `live.html` works (no WebGPU needed); the real WebLLM model (`edge.html`) needs Chrome/desktop.

## Honest live-vs-simulated labels
- **LIVE:** the phone call, the Nebius 70B bursts, the InsForge tool lookups.
- **SIMULATED (labeled on screen):** the dashboard sensor streams, the edge quantized model.
