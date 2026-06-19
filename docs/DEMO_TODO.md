# PhoneBio Demo TODO

> Source of truth: `python3 scripts/stress_test.py` → **23/23 GREEN = ready.**

## Status (auto-verified by the stress test)
- [x] Vapi: both numbers → Nebius **Llama-3.3-70B** · 6 inline tools · webhook serverUrl · denoise · **EMERGENCY MODE** prompt
- [x] InsForge: `phonebio-llm` + `phonebio-vapi-webhook` active · DB seeded (4 protocols / 2 SDS / 3 hardware / 9 sensors)
- [x] Dashboard **https://qfdp5nuv.insforge.site** (sensors) + **/edge.html** (in-browser quantized LLM orchestrator)
- [x] Brain tool-calling · all 6 tools grounded · unknown → "stop work" escalation · emergency 3-leg loop gives a safe action

## Before recording (pre-field setup — do once, with signal)
- [ ] Send setup links to phone: `make send-demo-links` or `python3 scripts/send_demo_links.py --to '+1...'`
- [ ] Close the `.env` tab in VS Code so a stale buffer cannot overwrite live keys.
- [ ] Run `make recording-preflight` → Vapi + Nebius + redacted demo stress gate.
- [ ] Run `make matrix-stress` → normal, protocol, MSDS, hardware, sensor, shorthand, emergency.
- [ ] Confirm TTS rehearsal audio was generated under `recordings/tts-stress/`.
- [ ] Set OBS to capture the laptop dashboard and terminal; keep `.env`, raw numbers, keys, transcripts, and recording URLs off screen.
- [ ] Start iPhone Screen Recording before the no-touch section.
- [ ] Save contact **PhoneBio = +1 541‑526‑9723** → enables "Hey Siri, call PhoneBio" (hands-free start)
- [ ] Add `https://qfdp5nuv.insforge.site` to the iPhone Home Screen as `PhoneBio` (and `/edge.html` for the local orchestrator)
- [ ] Open the Home Screen web app once; grant mic/motion/location (iOS may re-ask — that's fine)
- [ ] Enable **Voice Control (iOS)** / **Voice Access (Android)** → voice-tap "ARM SENSORS" / "Allow" with no physical touch
- [ ] **Two devices**: Phone A = the hands-free call · Device B = the dashboard (a live call grabs the mic, keep them separate)
- [ ] Quiet room · phone on speaker ~arm's length · camera/recorder capturing the room
- [ ] Run `python3 scripts/stress_test.py` → confirm **23/23 GREEN**

## Speaker-only take (no touch)
- [ ] Start `make vapi-wait-call` before placing the call.
- [ ] "Hey Siri, call PhoneBio" (or start the call just before the no-touch section)
- [ ] Phone on speaker; do not touch it
- [ ] "Help with my experiment — I can't use my hands."
- [ ] Normal: "Mobile data is weak, but this call works."
- [ ] Protocol: "I am collecting a surface water grab sample and the bottle has an air bubble."
- [ ] MSDS: "I spilled formaldehyde on a glove."
- [ ] Name the field mode: rainforest canopy / desert / field station
- [ ] Trigger the emergency: spill + small fire (or exposure), alone, can't reach 911
- [ ] Bring in the **physical first-aid kit** only AFTER the immediate-hazard action

## Demo lines
- [ ] "The phone call is the interface — hands-free, no app, works on a voice-only line."
- [ ] "Sensors were pre-authorized before the field run."
- [ ] "Vapi is voice, InsForge is backend + dashboard, Nebius is the GPU brain. No OpenAI."
- [ ] "The local gate compresses sensor signals into a triage label."
- [ ] "PhoneBio does not replace emergency services, SDS, or site command."

## After
- [ ] Run `make vapi-verify-call`; confirm `recordingPresent` if Vapi retained call audio.
- [ ] Don't show phone numbers, API keys, transcripts, recordings, or exact private locations.
- [ ] Re-run `python3 scripts/stress_test.py` to confirm still green.
