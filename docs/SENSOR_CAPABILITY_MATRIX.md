# Camera-Free Phone Sensor Capability Matrix

PhoneBio v1 does not read sensors directly. It accepts caller-described readings
or future native-app payloads and explains confidence limits. `compress_observation`
can preserve supplied geolocation, barometer, compass/magnetometer, placement,
connectivity, and sensor-summary fields as structured context.

| Sensor | Field Use | Typical Availability | v1 Input Mode | Accuracy/Variation Notes | Fallback |
|--------|-----------|----------------------|---------------|--------------------------|----------|
| Accelerometer | Detect orientation, drops, rough handling, vibration | Broad smartphone support | Caller/app gives axes or qualitative motion | MEMS bias, mounting, pocket/hand position, sampling rate, and OS filtering vary by model. Use trends over single samples. | Ask worker to repeat a still/known-orientation check. |
| Gyroscope | Rotation, tilt changes, stabilization checks | Broad smartphone support | Caller/app gives rotation rate or guided movement result | Drift accumulates; fusion with accelerometer is better for attitude than raw gyro alone. | Use short guided motions and reset reference often. |
| Magnetometer / compass | Heading, local magnetic field vector | Broad smartphone support | Caller/app gives heading or field vector | Measures local magnetic field, not object magnetic moment without a calibrated external method. Metal, magnets, vehicles, and electronics can dominate. | Step away from metal, recalibrate, or record bearing as unknown. |
| Barometer | Relative elevation, sealed-container pressure change, weather context | Many but not all phones | Caller/app gives pressure or altitude delta | Relative changes are more useful than absolute altitude; weather and temperature require calibration. | Ask for nearby reference reading or use qualitative trend. |
| Microphone / acoustic level | Loud environment, voice activity, possible multiple speakers, machinery noise | Broad smartphone support | Caller/app gives dB/SPL estimate, VAD/diarization result, or qualitative audio context | Single-phone audio can flag loud noise and likely overlapping voices, but cannot reliably identify or locate speakers without a reviewed audio pipeline and/or multiple devices. | Ask the worker to step away from machinery, repeat the reading, or switch to push-to-talk. |
| UWB | Distance/direction to tagged equipment or another device | Supported iPhones and selected Android devices/accessories | Caller/app reports distance/direction if supported | Requires compatible peer/accessory and session setup; line of sight and multipath matter. Treat as proximity zones, not survey-grade truth. | Fall back to BLE RSSI, audible prompts, or manual distance estimate. |
| LiDAR/depth | Non-camera depth/shape cues on supported devices | LiDAR-capable iPhone/iPad Pro class devices | Future native-app payload only | Apple ARKit scene depth requires LiDAR support; confidence maps and range limits matter. Because v1 avoids camera workflows, do not require it. | Use manual measurements, barometer, UWB, or inertial checks. |

## Confidence Language

- **Measured:** Direct value supplied by caller/app.
- **Inferred:** Derived from multiple readings or protocol context.
- **Unknown:** Device support, calibration, or environmental conditions are insufficient.

## Speaker Context Boundary

Use microphone/audio context for noise level, voice activity, and possible
overlap. Use UWB only for compatible nearby devices/tags. Do not infer exact
speaker count, identity, or position from barometer, GPS, accelerometer, or UWB
alone.

Barometric pressure variation from normal speech is not a usable signal for
speaker count or loudness. Use the microphone/audio pipeline for loudness,
voice activity, overlap, and diarization; use the barometer for slower
weather/elevation/pressure trends.

## Documentation Context

When supplied by the caller or app, PhoneBio can record:

- latitude/longitude and accuracy radius;
- altitude and barometric pressure;
- compass heading and local magnetic field vector;
- phone placement: hand, pocket, pack, vehicle, equipment, table, headset;
- connectivity: normal data, degraded data, voice only, offline;
- derived sensor labels such as loud machinery, possible overlap, vibration, or
  double tap.
