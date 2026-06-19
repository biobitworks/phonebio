# Stage Test Call Guide

Use this for the recorded demo when the room is noisy or the phone is not close
to the caller's mouth.

## Public Dashboard

Open this before recording:

```text
https://qfdp5nuv.insforge.site/dashboard.html
```

The hosted dashboard runs in static demo mode. It does not need local server
access, API keys, or mobile data from the field phone.

For the strict no-touch version, the dashboard is optional and must be prepared
before the call or controlled by someone other than the caller. The phone-call
demo must still work without dashboard clicks.

If phone sensor permissions are shown, grant them once before the recording and
state that this is part of pre-field setup. During the recorded incident, the
caller should not touch the phone.

## Phone Choice

Use your real phone for the main proof. The product claim is that a field worker
can call from their own device when app interaction is unavailable.

Use a second/test phone only as a controlled noise source or nearby-device
simulator. Do not make the second phone the main caller unless the real phone
cannot place a call.

## Audio Setup

The strict demo uses phone speaker only: no headset, no external mic, no phone
touches during the call. Speakerphone on stage can feed the assistant voice,
room audio, and audience noise back into the call.

If you must use speakerphone:

- Keep the phone within 12 inches of your mouth.
- Lower the phone volume enough to avoid echo.
- Pause after the assistant speaks before replying.
- Speak short chunks: one situation, one hazard, one requested action.
- Repeat critical units and hazards once.

## Demonstration Flow

1. Open the public dashboard before recording if using it as a visual aid.
2. Start the Vapi call before the no-touch section, or use voice assistant
   dialing if available.
3. Put the phone on speaker and do not touch it during the take.
4. Say: "Stage demo mode. Sensors were pre-authorized before the field run. I am on speaker only, I cannot touch the phone, mobile data is down, and the room is noisy."
5. If a separate operator controls the dashboard, click `Stage speaker`.
6. Expected dashboard state: `risk: medium`, `lane: noisy_confirmation`.
   The local quantized orchestrator panel should show `ask confirmation` and
   `ExecuTorch filter, then Vapi`.
7. Expected agent behavior: it asks one confirmation question before using the
   noisy context, such as: "Are you alone, with another worker, near a radio, or
   near powered equipment?"
8. Reply: "One other worker is nearby, and the centrifuge is running."
9. If a separate operator controls the dashboard, click `Biohazard`.
10. Expected dashboard state: `risk: high`, `lane: emergency_priority`.
   The local quantized orchestrator panel should show `short safety action` and
   `Vapi + InsForge priority`.
11. Say: "Now there is a biohazard spill cue. What is the immediate action?"

For sensor interpretation boundaries, use `docs/SENSOR_TRIAGE_MATRIX.md`.

## Emergency Services Unavailable Variation

Use this phrasing only for the demo scenario where the caller cannot immediately
place a separate emergency call:

```text
I cannot reach emergency services from here. There is a chemical spill and
possible hardware fire. I cannot use my hands. Help me triage what to do first.
```

Expected agent behavior:

- Tell the caller to get any nearby person to call emergency services if
  possible.
- If that is not possible, give immediate life-safety actions only.
- Ask for the minimum relay facts: location, hazard, injuries/exposure, fire or
  smoke, and callback/relay path.
- Ask what basic first-aid-kit supplies are available only after immediate
  hazard avoidance is addressed.
- Avoid detailed cleanup or repair instructions during immediate danger.

Safe demo response target:

```text
Move away and upwind if safe. Warn others. Do not touch the spill or equipment.
Do not re-enter. Is anyone injured or having breathing trouble?
```

First-aid kit demo line:

```text
I have a basic first-aid kit with gloves, gauze, bandages, tape, and saline, but
I cannot use my hands well. Tell me what to do first.
```

## Message To Say On Camera

"A normal call stays cheap. A noisy stage call asks for confirmation before it
trusts the audio. An emergency cue moves into priority handling. The phone
sensors and nearby-device signals do not identify people; they decide what the
agent should ask and how much processing to spend."

Optional quantized-orchestrator line:

"This panel simulates a small local quantized model on the phone. It does not
solve the lab problem; it triages sensor spikes, decides whether to stay local,
ask a confirmation question, or prioritize the Vapi and InsForge path."

Optional ExecuTorch line:

"The local runtime target is ExecuTorch: a tiny quantized `.pte` model can
classify low-level sensor features before we spend network or GPU resources."
