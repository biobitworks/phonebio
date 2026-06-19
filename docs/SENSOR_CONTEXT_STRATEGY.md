# Sensor Context Strategy

PhoneBio can use non-camera sensor readings as low-level context when imaging is
not allowed. Sensor data should shape questions and confidence, not become an
unverified claim of identity or calibrated measurement.

This matters most in PPE and disaster-relief settings: the worker may or may not
be able to tap an app, remove gloves, read a screen, or take a picture. Sensor
context must be optional background evidence, while the voice call remains
sufficient.

## Context Signals

| Signal | Sensor Source | Useful For | Boundary |
|--------|---------------|------------|----------|
| Speaker/audio context | Microphone level, voice activity, optional diarization | Detect loud environment, likely multiple voices, interruptions, machinery noise during troubleshooting | A single phone usually cannot reliably count or locate speakers. Speaker identity is out of scope. |
| Vibration/noise context | Accelerometer, gyroscope, microphone level | Centrifuge imbalance, pump rattle, dropped logger, vehicle vibration, unsafe machinery | Trend evidence only unless calibrated against a known sensor/device. |
| Gesture/pocket context | Accelerometer, gyroscope, proximity/screen state, optional wearable/app events | Hands-free commands, “mark this,” repeat, emergency flag, walking/running/stopped/drop context | Phone placement changes meaning. Pocket motion is context, not calibrated measurement. |
| Nearby equipment/people proxy | UWB, BLE/RSSI fallback | Distance/direction to tagged logger, trap, sample cache, second phone, or anchor | UWB locates compatible devices/tags, not untagged people. Foliage and bodies degrade range. |
| Location context | GPS/GNSS, barometer | Field site, altitude delta, route context, weather risk | GPS vertical error is weak; barometer is relative and weather-sensitive. |
| Orientation/context | Accelerometer, gyroscope, magnetometer | Leveling equipment, transect bearing, slope/aspect, “phone on machine” checks | Require repeated readings and calibration prompts. |

## Voice-Agent Behavior

- Ask for sensor name, units, phone model, and whether the reading was repeated.
- Ask where the phone is when motion matters: hand, pocket, pack, strapped to
  equipment, vehicle, table, or headset.
- Prefer repeated trends over one-off readings.
- Preserve uncertainty in the answer: measured, inferred, or unknown.
- Use sensor context to choose the next troubleshooting question.
- Never infer identity, exact number of people, or precise speaker location from
  barometer, GPS, accelerometer, or UWB alone.
- Use microphone/diarization only as an acoustic-context signal unless the user
  explicitly enables a reviewed audio pipeline.
- Do not ask the caller to touch the phone when PPE, contamination, sterile
  handling, or active disaster work makes touch unsafe.
- Allow gestures only as optional shortcuts. Voice must remain the fallback for
  repeat, mark, stop, emergency flag, and confirmation.

## Implementation Notes

The current tool surface is `interpret_sensor_report`. It already supports
accelerometer, gyroscope, magnetometer, barometer, UWB, LiDAR/ToF, and GPS from
`content/sensors/sensors.json`. Acoustic context and gesture/pocket context are
sensor profiles so the assistant can answer questions about loud environments,
multiple voices, machine noise, phone placement, and hands-free event marking
without camera input.

Most IoT value comes from low-level derived labels, not raw streams: pocket,
walking, running, stopped, fall/drop, loud machinery, likely voice overlap, UWB
near tag, GPS degraded, barometer falling, or device vibration. Local quantized
models can produce those labels when available; InsForge/Vapi can continue by
voice when data service fails; Nebius can process non-safety batches quickly
when credits are available.
