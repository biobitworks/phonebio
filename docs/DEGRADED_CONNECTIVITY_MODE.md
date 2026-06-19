# Degraded Connectivity Mode

PhoneBio assumes the field device may have broken or low-bandwidth data service
while ordinary cellular voice still works. This is common in remote fieldwork,
disaster relief, congested cell towers, battery-saver mode, foreign roaming, and
old hardware deployments.

## Product Rule

The field device must not need mobile data during the critical interaction.
Voice call access is sufficient for v1.

Do not require the caller to:

- open maps;
- upload photos or files;
- wait for app sync;
- browse protocols;
- authenticate in a web app;
- use APIs from the field device.

Server-side services may still use Vapi, InsForge, and Nebius if the call reaches
the assistant. The degraded-connectivity constraint applies to the worker’s
device in the field.

Sensor data may still be collected locally by the phone, wearable, or a nearby
device. If no data connection exists, those records should be summarized locally
when possible and synced later. The critical path remains the voice call.

## Voice Capture Pattern

When data service is degraded, the assistant should capture minimal spoken
fields in this order:

1. Life safety: injury, fire, spill, exposure, trapped person, unstable
   structure.
2. Location: spoken landmark, GPS if available, barometer/altitude trend if
   useful, confidence radius if known.
3. Hazard/material: chemical, biological, fuel, smoke, unknown substance.
4. Device/sample: old hardware, sample ID, protocol, custody concern.
5. Sensor context: noise, vibration, pocket gesture, UWB/BLE tag, pressure,
   motion, compass bearing.
6. Action taken: stopped work, isolated area, preserved sample, powered down,
   escalated.

The output should be a compact downstream triage record that can sync later.

## Downstream Sync

If InsForge persistence is approved, store compact derived records server-side
during the call. If the field app later regains data service, it may upload
sensor payloads or reconcile local packets, but this cannot block the voice
workflow.

Raw audio, exact location, and personal data are sensitive. Store hashes,
derived labels, and minimum necessary triage fields unless explicit retention is
approved.

## Fallbacks

- If Vapi call connects but tool latency is high, answer with the safest local
  escalation rule and continue collecting critical fields.
- If data is unavailable on the caller side, ask for spoken readings instead of
  app payloads.
- If local quantized sensor models are available, accept their derived labels
  such as `loud machinery`, `walking`, `pocket`, `drop`, or `double tap`, but do
  not require them.
- If GPS does not load, ask for landmark, address fragment, road, plot marker,
  UWB/BLE tag, or last known route.
- If the call drops, the latest compact record should still show last known
  hazard, location, and action.
