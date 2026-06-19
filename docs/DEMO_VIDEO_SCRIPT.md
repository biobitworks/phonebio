# PhoneBio 3 Minute Demo Video Script

## Goal

Show PhoneBio as a voice-first field biology and disaster-triage assistant for
cases where camera use is unavailable, hands are constrained by PPE, and mobile
data may fail while phone calls still work.

## 3 Minute Structure

### 0:00-0:20 Opening

**Say:**

“This is PhoneBio. It is a phone-call agent for field biology, lab safety, old
equipment troubleshooting, and disaster triage when the worker may have PPE on,
no camera access, and degraded cell service where only calls work.”

**Show:**

- Vapi phone agent screen or local runbook.
- One terminal tab with `make prefield-check`.

### 0:20-0:45 Pre-Field Setup

**Say:**

“Before the worker goes into the field, we run a pre-field check. It verifies the
assistant prompt, local protocols, SDS summaries, hardware guides, sensor
profiles, shorthand compression, and call-only degraded-connectivity docs. No
OpenAI key is required.”

**Run or show:**

```bash
make prefield-check
```

**Expected line to mention:**

“Ready is true: the offline content bundle and voice-first mode are prepared
before internet goes out.”

### 0:45-1:20 Core Voice Demo

**Say as caller:**

“Low-level formaldehyde cleanup. No fire. No skin contact. I forgot the SDS
location step. Ask me where I am relative to ventilation, eyewash, spill kit,
exits, and other people before cleanup.”

**Narrate:**

“Vapi owns the phone call. Nebius 70B handles the live reasoning turn. InsForge
hosts the deterministic SDS/tool backend, so safety facts come from source-backed
records, not a guess.”

**Expected behavior:**

- The agent asks for missing location context first: ventilation/open air,
  eyewash or water, spill kit, exits, and nearby people.
- It can call `get_safety_sheet` for the formaldehyde SDS quick-reference.
- It does not jump to emergency services because the caller explicitly says no
  fire, no skin contact, no symptoms, and low-level cleanup.
- It escalates only if the caller adds fire, symptoms, skin/eye contact, a large
  spill, lack of training, or uncertainty.

### 1:20-1:55 Old Equipment + Sensors

**Say as caller:**

“The legacy centrifuge is vibrating after balancing. The phone is in my pocket,
there is loud machinery, and I hear two voices overlapping.”

**Narrate:**

“Phone sensors are low-level context: vibration, pocket state, audio overlap,
GPS, barometer, UWB, and gestures. A single phone can flag possible multiple
speakers or risk context; it does not claim exact identity or headcount.”

**Expected behavior:**

- Calls `troubleshoot_hardware` for centrifuge.
- Calls or describes `assess_environment_risk`.
- Says stop work if repeated vibration or biohazard risk is present.

### 1:55-2:25 Gregg-Style Compression

**Say:**

“PhoneBio also compresses lab jargon into a Gregg-inspired field note and reads
it back for confirmation.”

**Run or show:**

```bash
make shorthand-stress
```

**Read one example:**

“Aliquot 20 microliters buffer with the micropipette, then run a negative
control and positive control.”

**Explain:**

“The compact note preserves aliquot, buffer, micropipette, control, units, and a
voice readback.”

### 2:25-2:50 Provider Split

**Say:**

“The provider split is simple: Vapi is for phone agents. InsForge is for the
website, backend, deterministic tools, and records. Nebius is the GPU reasoning
lane for the live call. Safety authority still comes from InsForge SDS/protocol
records. If Nebius or the network fails, a clearly labeled deterministic fallback
can keep the demo moving, but it is not the primary path.”

### 2:50-3:00 Close

**Say:**

“The point is resilient field communication: when app data fails, the worker can
still call, describe the situation, get grounded next steps, and produce a
compact downstream triage record.”

## Alternate Caller Lines

Use these if you need multiple takes.

### Biohazard

“Data is down. I am in PPE. There is a biohazard spill near the old incubator,
and I need the next safe step.”

### Disaster Triage

“Disaster triage note. Loud machinery, possible fuel smell, two workers nearby,
phone in pocket, GPS accuracy is eight meters.”

### Old Hardware

“The Bluetooth data logger will not pair. The battery is fresh, the phone is
within one meter, and I cannot open the app because I am gloved.”

### Sensor-Only

“My barometer dropped four hectopascals in two hours, GPS is unreliable, and
wind noise is high.”

### Shorthand / Lab Jargon

“Polymerase chain reaction failed. No template control amplified, and the sample
is contamination suspect.”

## Commands To Have Ready

```bash
make prefield-check
make hosted-demo
make shorthand-stress
make readiness
```

## Best Take Reference

Local reference recording for the submitted/demo take:

```text
/Users/byron/Movies/2026-06-19 15-15-53.mov
```

Keep this file local or in private editing storage. Do not commit raw call
recordings, transcripts, phone numbers, exact private locations, or recording
URLs.

## What Not To Say

- Do not say the system replaces SDS, emergency services, or a site supervisor.
- Do not say the phone precisely counts or identifies people from audio.
- Do not say Nebius is the source of protocol or SDS truth.
- Do not imply a deterministic fallback is Nebius output; call it a fallback
  only if it is used.
- Do not show raw phone numbers, API keys, transcripts, or exact private
  locations.
