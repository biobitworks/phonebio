# Pre-Field Setup

Run this before a worker leaves reliable internet. The goal is to make PhoneBio
usable when mobile data fails and only a voice call gets through.

## Required Before Departure

- Confirm the worker knows the PhoneBio call number and a backup escalation
  contact.
- Place one test call in coverage and verify the assistant answers.
- Run `make prefield-check` from the repo.
- Run `make hosted-demo` if the hosted InsForge webhook was changed.
- Confirm the Vapi assistant prompt includes voice-first, no-camera,
  degraded-connectivity, and no-required-app-interaction constraints.
- Confirm the deterministic content bundle includes protocols, SDS summaries,
  hardware guides, sensor profiles, shorthand lexicon, and disaster/degraded
  connectivity docs.
- Confirm battery/power plan: phone charged, external battery, headset if
  needed, airplane/data settings understood.
- Confirm app/sensor permissions while internet is still available:
  microphone, location/GPS, motion/fitness, Bluetooth/UWB if used, background
  activity if the app exists.
- Confirm local sensor model assets if used: VAD/noise, gesture/activity,
  pocket state, multilingual keyword hints. These are optional, not v1 blockers.
- Confirm retention policy: raw audio, exact location, and personal data are not
  retained by default.

## Field Operating Modes

| Mode | Assumption | Required Interface |
|------|------------|--------------------|
| Normal data | App and voice both work | App can enrich; voice remains available |
| Degraded data | App data/maps/uploads unreliable | Voice call plus spoken readings |
| Voice only | Cellular call works, mobile data fails | Vapi call only |
| Offline app | No call/data, app still runs locally | Local packet capture, sync later |

## Call-Only Worker Instructions

Tell the worker:

1. If data fails, call PhoneBio.
2. Say the mode first: “data is down,” “hands-free,” “PPE,” or “disaster note.”
3. Say location by landmark if GPS/maps do not load.
4. Say hazard/injury before equipment or sample details.
5. Say sensor readings with units if available.
6. If the call drops, call back and start with “resume triage.”

## Operator API Timing

APIs are needed only before/after fieldwork, not from the field device during a
voice-only event:

- **Vapi API:** needed to create/update assistant, assign phone number, or verify
  call logs.
- **InsForge API:** needed to redeploy functions or approve persistence.
- **Nebius API:** needed for optional GPU processing/evals, not deterministic
  SDS/protocol authority.
- **No OpenAI API key** is required.

## Acceptance

A deployment is pre-field ready when:

- `make prefield-check` passes;
- a real Vapi call was verified recently, or the operator explicitly accepts
  that live-call verification is still open;
- the worker has the call number and backup escalation path;
- the field app/sensor path is treated as optional enrichment, not a dependency.
