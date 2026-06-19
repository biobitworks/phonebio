# Camera-Free Phone Sensor Capability Matrix

PhoneBio v1 does not read sensors directly. It accepts caller-described readings or future native-app payloads and explains confidence limits.

| Sensor | Field Use | Typical Availability | v1 Input Mode | Accuracy/Variation Notes | Fallback |
|--------|-----------|----------------------|---------------|--------------------------|----------|
| Accelerometer | Detect orientation, drops, rough handling, vibration | Broad smartphone support | Caller/app gives axes or qualitative motion | MEMS bias, mounting, pocket/hand position, sampling rate, and OS filtering vary by model. Use trends over single samples. | Ask worker to repeat a still/known-orientation check. |
| Gyroscope | Rotation, tilt changes, stabilization checks | Broad smartphone support | Caller/app gives rotation rate or guided movement result | Drift accumulates; fusion with accelerometer is better for attitude than raw gyro alone. | Use short guided motions and reset reference often. |
| Barometer | Relative elevation, sealed-container pressure change, weather context | Many but not all phones | Caller/app gives pressure or altitude delta | Relative changes are more useful than absolute altitude; weather and temperature require calibration. | Ask for nearby reference reading or use qualitative trend. |
| UWB | Distance/direction to tagged equipment or another device | Supported iPhones and selected Android devices/accessories | Caller/app reports distance/direction if supported | Requires compatible peer/accessory and session setup; line of sight and multipath matter. Treat as proximity zones, not survey-grade truth. | Fall back to BLE RSSI, audible prompts, or manual distance estimate. |
| LiDAR/depth | Non-camera depth/shape cues on supported devices | LiDAR-capable iPhone/iPad Pro class devices | Future native-app payload only | Apple ARKit scene depth requires LiDAR support; confidence maps and range limits matter. Because v1 avoids camera workflows, do not require it. | Use manual measurements, barometer, UWB, or inertial checks. |

## Confidence Language

- **Measured:** Direct value supplied by caller/app.
- **Inferred:** Derived from multiple readings or protocol context.
- **Unknown:** Device support, calibration, or environmental conditions are insufficient.

