# PB-G3 — Tertiary goal: local sensors → people estimate → voice distinguishing

**Locked:** 2026-07-24T17:17:32Z  
**Priority:** tertiary  
**Owner:** `phonebio`

## Operator lock

PhoneBio was to use **local sensors** to determine **how many people**, to help with **voice distinguishing**, as a **tertiary** goal.

## Framing

| Layer | Role |
|---|---|
| Local sensors | Camera-free phone/edge signals (acoustic presence, BLE/UWB proximity, motion, …) |
| People estimate | Presence-class “how many people nearby” — not who they are |
| Voice distinguishing | Tertiary aid for diarization / separating voice leaves when multiple people may be present |

## Claim ceiling

- **Do** say: sensors help estimate presence / people-count to improve voice distinguishing.
- **Do not** say: exact headcount proven from sensors alone; biometric identity; camera people-counting.

Aligns with `content/presence_signals.json` privacy note and demo scripts that forbid exact identity/headcount claims.
