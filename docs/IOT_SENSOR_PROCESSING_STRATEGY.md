# IoT Sensor Processing Strategy

PhoneBio treats the phone as the primary low-level IoT collector. The worker may
only have voice connectivity, may be wearing PPE, and may not be able to open an
app. Sensor processing therefore has to degrade across local, call-only, and
server-side modes.

## Processing Lanes

| Lane | Runs Where | Use When | Good For | Boundary |
|------|------------|----------|----------|----------|
| Raw sensor/event collection | Phone OS / native app / wearable | App is installed and permissions are granted | Accelerometer, gyro, barometer, GPS, mic level, UWB/BLE, gestures, pocket state | Optional. Cannot block the voice workflow. |
| Local quantized model | Phone or nearby laptop | Data works poorly, privacy matters, latency matters, model fits locally | Voice activity, noise class, gesture smoothing, simple hazard/triage labels, language hints | Must be small and fail-soft. Safety/protocol authority stays in reviewed records. |
| Vapi phone-agent lane | Cellular voice call | Mobile data fails but a call can connect | STT/TTS, turn-taking, spoken triage capture, tool routing | Spend call minutes carefully; keep prompts short. |
| InsForge website/backend lane | Hosted website, server/function, database | Call reaches server-side webhook or app/site is available | Website/app surface, protocol/SDS/hardware/sensor/shorthand lookup, receipts, compact downstream records | Source-backed truth layer. No hallucinated authority. |
| Nebius GPU lane | Token Factory / GPU inference | $100 credit is available and fast model reasoning is useful | Non-safety summarization, multilingual paraphrase, tool-selection experiments, batch evals, shorthand/phoneme candidate ranking | Not authoritative for SDS/protocols/emergency guidance. |
| Later sync lane | App/InsForge after connectivity returns | Mobile data returns | Upload signed packets, richer sensor payloads, maps, attachments, reconciliation | Post-call enrichment only; never required for immediate safety. |

## Degradation Order

1. If app data works: collect low-level sensor events and summarize locally.
2. If app data is unreliable: keep collecting locally if possible, but use voice
   for the critical path.
3. If only calls work: Vapi captures spoken fields; server-side InsForge tools
   answer from reviewed data.
4. If server model capacity is needed and credits permit: Nebius processes
   non-safety extraction, multilingual phrasing, and fast evaluation.
5. If the call drops: preserve the latest compact triage record server-side and
   resume by call/SMS/manual report when possible.

## Local Quantized Model Candidates

Local models should be optional modules, not v1 blockers. Useful candidates:

- tiny VAD/noise classifier for speech versus machinery/wind;
- gesture/activity classifier for pocket, walking, running, still, fall/drop,
  double tap, shake;
- small multilingual keyword detector for hazard/location/device terms;
- shorthand/syllable compressor for compact field notes;
- local summarizer only when device performance allows it.

The local model output should be reduced to derived labels and confidence, for
example:

```json
{
  "placement": "pocket",
  "activity": "walking",
  "noise": "machinery_loud",
  "gesture": "double_tap",
  "confidence": "medium",
  "raw_retained": false
}
```

## Data Contract

Low-level sensor records should be compact and replayable:

- `record_id`
- `timestamp`
- `device_context`: phone model if known, OS/app version if known
- `connectivity`: app_data, degraded_data, voice_only, offline
- `placement`: hand, pocket, pack, vehicle, equipment, table, headset, unknown
- `signals`: derived labels plus units when measured
- `confidence`
- `source`: caller_spoken, app_payload, local_model, server_model, reviewed_tool
- `action`: captured, escalated, stop_work, sync_later
- `retention`: derived_only by default

No raw audio, exact location, or personal data should be retained by default.

## v1 Choice

For v1, implement and verify the voice + deterministic InsForge path first.
Local quantized models and Nebius GPU processing are acceleration layers:
valuable, but not required for the call-only disaster workflow to function.
