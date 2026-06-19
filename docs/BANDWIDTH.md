# Information bandwidth vs. where processing occurs

**Principle:** the higher a signal's *raw* bandwidth, the closer to the **edge** it must be processed. Only **low-bandwidth derived signals** (labels, events, coordinates) are cheap enough to travel over a weak field link to the **cloud**. This is what makes "local quantized model at the edge + heavy GPU in the cloud" the right split.

| Sensor / signal | Raw bandwidth | What's actually sent | Process at | Why |
|---|---|---|---|---|
| Microphone (audio) | ≈768 kbps (48 kHz·16-bit) | loudness/VAD/event labels (bytes) | **EDGE** | raw audio won't stream on a weak link; derive on-device |
| LiDAR / camera *(camera off)* | MB/s | a distance / shape flag | **EDGE only** | far too heavy to send |
| Accelerometer | ≈3 KB/s (100–500 Hz·3-ax) | fall/impact events | **EDGE** | continuous; only the event matters |
| Gyroscope | ≈3 KB/s | fused orientation | **EDGE** | fuse locally, emit a value |
| Magnetometer / heading | ≈0.5 KB/s | a bearing (degrees) | **EDGE → cloud** | tiny once derived |
| Barometer | tens of B/s | altitude delta / blast flag | **EDGE → cloud** | already low |
| UWB / BLE ranging | small | distance / presence | **EDGE fuse** | derive proximity |
| GPS | ≈20 B/s | lat/lon + accuracy | **CLOUD-ok** | tiny; geotag/relay |
| Triage label / shorthand record | bytes | the record itself | **CLOUD / SMS** | fits a 160-char SMS even with no data |

## Where each tier runs (matches the dashboard tags)
- **EDGE (on-device / in-browser):** audio→loudness/events, accel/gyro→fall, sensor fusion, the quantized triage model. High-bandwidth **in**, low-bandwidth **out**.
- **Vapi:** the **voice channel** — call audio rides the carrier *voice* path (works with no data), not the data link.
- **Nebius (cloud GPU):** the reasoning brain + heavy refine (big ASR, diarization, translation) — operates on the **low-bandwidth derived signals** + the call.
- **InsForge:** stores the low-bandwidth derived records (DB + edge functions + dashboard hosting).

**Takeaway for the demo:** the dashboard's per-sensor data line is colored by where it's processed — orange = **EDGE** (bandwidth too high to ship raw), blue = **cloud-ok** (already tiny). That's the architecture, visible at a glance.
