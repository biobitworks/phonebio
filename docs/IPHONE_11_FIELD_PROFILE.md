# iPhone 11 Field Profile

This profile is for the current demo phone.

## Available / Useful

| Capability | Use In PhoneBio |
|---|---|
| Microphone | Voice call, loudness, noisy-room cue, possible overlap cue. |
| Speaker / earpiece / headset mic | Voice-first interface; headset/earbud is best for stage. |
| Accelerometer | Vibration, impact, fall-like cue, phone-in-pocket movement. |
| Three-axis gyroscope | Rotation, orientation, handling state. |
| Barometer | Pressure/elevation/weather trend; field context only. |
| Proximity sensor | Near face/pocket/covered-phone context. |
| Ambient light sensor | Pocket/dark/glare/face-down context. |
| GPS/GNSS | Coordinates and accuracy for relay facts. |
| Bluetooth LE | Nearby beacons/devices if app permissions and devices support it. |
| NFC | Intentional tag/equipment/sample scan. |
| U1 / Ultra Wideband | Spatial awareness with supported Apple/UWB devices; availability and APIs are constrained. |
| A13 Neural Engine | Candidate for future local/quantized inference path through a native app. |

## Not Available As Assumed Built-In Sensors

| Capability | Boundary |
|---|---|
| LiDAR scanner | iPhone 11 does not have rear LiDAR. LiDAR starts on later Pro-class devices and some iPad Pro models. |
| Humidity sensor | iPhone 11 does not expose a relative-humidity sensor to apps. Use external BLE/weather/station sensors if humidity matters. |
| General radar sensor | iPhone 11 does not expose a general radar sensor. UWB is spatial ranging with supported devices, not broad radar imaging. |
| Ambient temperature sensor | iPhone 11 does not expose calibrated ambient air temperature to apps. Battery/device temperature is not ambient field temperature. |

## Demo Interpretation

For the iPhone 11 demo, say:

```text
This phone has enough local sensors for low-bandwidth triage: motion, pressure,
location, light/proximity, microphone context, Bluetooth/NFC, and UWB with
supported devices. It does not need LiDAR or humidity to show the core flow.
```

## Best iPhone 11 Demo Flow

1. Use the real phone to call the Vapi number.
2. Use the public dashboard on the laptop or phone:
   `https://qfdp5nuv.insforge.site/dashboard.html`
3. Click `Stage speaker` to show noisy confirmation.
4. Click `Centrifuge spike` to show accelerometer-style equipment context.
5. Click `Pressure drop` to show barometer context.
6. Click `GPS degraded` for rainforest/canopy location uncertainty.
7. Click `Biohazard` for emergency priority.

## Sources

- iPhone 11 technical specifications: https://support.apple.com/en-us/111865
- iPhone 11 Pro technical specifications sensor list: https://support.apple.com/en-us/111879
- Apple Ultra Wideband availability: https://support.apple.com/en-us/109512
