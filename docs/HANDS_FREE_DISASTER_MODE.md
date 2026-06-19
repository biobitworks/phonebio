# Hands-Free Disaster Mode

PhoneBio v1 must work when the user cannot touch a screen, while still using a
screen/app when it is safe and available. It must also work when only a cellular
voice call gets through and mobile data/app sync fails. This covers PPE,
wet/contaminated gloves, sterile work, field darkness, limited connectivity, old
hardware, and disaster relief data collection.

## Product Rule

The voice call is the baseline interface. App/screen interaction is an optional
enhancement, not an assumption. The assistant must not require:

- app taps;
- typing;
- camera use;
- reading long text from a screen;
- uploading files during the live call;
- switching apps while holding equipment or wearing PPE.
- mobile data, maps, uploads, or app sync during the critical exchange.

If app/sensor payloads exist, they are optional background context. The caller
must still be able to complete the workflow by voice.

When screen interaction is safe, it can be used for:

- reviewing longer protocols after the immediate voice answer;
- confirming structured triage fields;
- displaying maps/GPS accuracy;
- pairing UWB/BLE devices;
- exporting downstream disaster-triage records.

When touch is unsafe but the phone or wearable can sense motion, optional
gestures may be used for low-friction control:

- double tap or shake: mark current time/event;
- long stillness after movement: ask whether the worker is stopped or needs
  help;
- drop/fall-like spike: ask a safety check;
- repeated pocket taps: repeat last instruction.

Gestures are shortcuts, not requirements. Confirm safety-critical actions by
voice when possible.

## Call Behavior

- Ask one question at a time.
- Use short confirmations: “Recorded,” “Hold,” “Stop work,” “Next check.”
- Read back critical fields before action: site, hazard, device, sensor,
  material, amount, exposure route, and unit.
- For disaster triage, classify the downstream record as:
  `life_safety`, `hazmat`, `medical`, `infrastructure`, `sample_integrity`,
  `equipment_failure`, `location_update`, or `unknown`.
- When the caller is under stress/noise, switch to minimal prompts:
  “Say hazard,” “Say location,” “Say injury yes or no,” “Say device.”
- Never make the caller manipulate a contaminated phone unless the next step is
  explicitly decontamination or emergency communication.

## Data Record

Each hands-free interaction should produce a compact downstream triage record:

- timestamp;
- caller role if known;
- location/GPS/barometer context if supplied;
- hazard/material;
- people/injury status if volunteered;
- equipment/device;
- sensor readings and units;
- action taken;
- escalation target;
- confidence: measured, inferred, or unknown;
- source/tool ids.

Raw audio and personal data should not be retained by default. Store compact
derived records unless an operator explicitly approves a reviewed retention path.

## Sensor Role

Sensors provide low-level context, especially when imaging is not allowed:

- microphone: loud environment, likely overlap, machinery noise;
- accelerometer/gyroscope: vibration, drop, orientation, pocket motion, gesture;
- GPS/barometer: location and altitude/weather context;
- UWB/BLE: nearby tagged devices or anchors;
- magnetometer: bearing and orientation;
- LiDAR/ToF: optional camera-free depth on supported devices.

Sensor context guides questions and triage category. It does not prove speaker
identity, exact headcount, or calibrated environmental measurements by itself.
