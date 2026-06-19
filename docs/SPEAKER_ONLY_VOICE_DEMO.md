# Speaker-Only Voice Demo

This is the strict end-to-end mode for the recorded demonstration.

## Constraint

During the live call:

- no touching the phone
- no headset or external microphone
- no app taps
- no sensor permission prompts
- no typing
- no camera
- no phone dashboard interaction

The phone is on speaker. All interaction with PhoneBio happens by voice.

## Setup Before Recording

Choose one:

1. Start the Vapi call before recording, place the phone on speaker, and do not
   touch it during the take.
2. Use a platform voice assistant to place the call if available:

```text
Hey Siri, call PhoneBio.
```

Then say:

```text
PhoneBio, I cannot use my hands. This is a speaker-only field demo.
```

The public dashboard may be opened on a laptop before recording as a visual aid:

```text
https://qfdp5nuv.insforge.site/dashboard.html
```

If used, start `Run live simulation` before the speaker-only section or have a
separate operator control the laptop. Do not require the caller to touch the
phone.

For OBS and audio capture, use:

```text
docs/OBS_AND_AUDIO_CAPTURE.md
```

Start `make vapi-wait-call` before the phone call if you want redacted evidence
that Vapi captured the call and retained transcript/audio artifacts.

## One-Time Pre-Authorization

If sensor access is part of the story, do this once before recording:

1. Open the sensor/dashboard page on the phone:
   `https://qfdp5nuv.insforge.site/dashboard.html`.
2. In Safari, use Share -> Add to Home Screen, then name it `PhoneBio`.
3. Open the new `PhoneBio` Home Screen icon once.
4. Grant any browser or app permissions while touching the phone is still
   allowed.
5. Confirm the page is already running or the static dashboard is already
   visible.
6. Lock the demo rule: once recording starts, the caller does not touch the
   phone.

Phrase it this way:

```text
Before going into the field, the worker pre-authorizes the phone sensors once.
During the incident, they do not need to touch the phone; the call remains the
interface.
```

## Sensor Website Boundary

Do not rely on opening a sensor website hands-free during the strict demo.
On iPhone/Safari, a voice assistant may be able to open a URL, but first-time
permission prompts for microphone, motion, location, or other sensors generally
require prior user consent and may require a screen tap.

Allowed demo options:

- pre-open the sensor page and grant permissions before the no-touch recording
  starts
- have a separate operator control the laptop/dashboard
- use the public static dashboard simulation
- keep the live call fully voice-only and describe sensor packets as future
  pre-authorized app data

The strict speaker-only claim is strongest when the call itself does not depend
on a browser permission prompt.

## Permission Persistence Boundary

Adding the web app to the Home Screen makes it easier to launch, but it does not
guarantee every sensor permission persists forever on iOS. Treat permissions as
pre-field setup state:

- Verify microphone/location/motion behavior before the take.
- Leave the web app open if sensor state matters.
- Do not depend on a new permission prompt during the incident.
- If iOS asks again, skip sensor collection and continue the Vapi voice call.

## Audio Rules

Speakerphone can echo and feed the assistant voice back into the call. To reduce
failure:

- keep the phone close enough for the built-in microphone to hear the caller
- lower volume enough to avoid echo
- pause after the assistant finishes
- speak in short lines
- repeat critical hazards and units once
- say "repeat" if the assistant misheard

## Script

Caller:

```text
PhoneBio, I am in a remote field station. I cannot use my hands. I am on
speaker only. Mobile data is unreliable, but this call works.
```

Expected agent:

```text
Understood. Are you in dense canopy, desert/open field, a field station,
vehicle, boat, or lab-like room?
```

Caller:

```text
Field station near rainforest canopy. There is a chemical spill and possible
hardware fire. I cannot reach emergency services right now.
```

Expected agent target:

```text
Get anyone nearby to call emergency services if possible. Move away and upwind
if safe. Warn others. Do not touch the spill or equipment. Is anyone injured or
having breathing trouble?
```

Caller:

```text
No injury confirmed. I have a basic first-aid kit, but I cannot use my hands.
There is loud machinery and the phone is on the bench.
```

Expected agent target:

```text
Do not re-enter or troubleshoot. Keep distance. Tell me location, chemical name
if known, fire or smoke status, and whether another person can relay help.
```

## What This Demonstrates

- Vapi handles the phone conversation.
- InsForge serves the deterministic tools and public demo surface.
- The local quantized/ExecuTorch path is represented as a low-bandwidth triage
  gate, but the live call does not depend on app permissions.
- The agent does not replace emergency services; it gives immediate protective
  steps and captures relay facts when emergency contact is unavailable.

## Failure Handling

If the assistant cannot hear clearly, say:

```text
Repeat. Speaker-only demo. I cannot touch the phone.
```

If the assistant asks for an app, screen, photo, or tap, say:

```text
No screen or touch is available. Continue by voice only.
```
