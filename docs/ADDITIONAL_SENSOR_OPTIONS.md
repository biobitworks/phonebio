# Additional Sensor Options

PhoneBio can use more than accelerometer, gyro, barometer, magnetometer,
microphone, UWB, LiDAR, and GPS. The key rule is the same: sensors provide
context unless the device and method are calibrated and documented.

## Built-In Phone Signals

| Signal | Use | Notes |
|--------|-----|-------|
| Proximity sensor | Detect pocket/face/covered phone state | Useful for hands-free mode and audio quality context. Not a distance sensor for field objects. |
| Ambient light | Darkness, covered pocket/pack, rough indoor/outdoor context | Can help infer whether the phone is pocketed or in a dark room. Not a calibrated lux meter unless app/device supports it. |
| Battery and thermal state | Worker/device survivability, cold-chain/device stress, shutdown risk | Good for disaster mode: low battery + voice-only service changes interaction strategy. |
| Cell signal / network type | Voice-only, degraded data, roaming, tower congestion | Captures why app sync/maps may fail. Should be stored as coarse status, not exact carrier metadata. |
| Wi-Fi scan context | Indoor/field-station proximity, known access point nearby | Privacy-sensitive; store derived labels only. |
| Bluetooth/BLE scan context | Nearby tags, data loggers, beacons, wearable sensors | Strong for old equipment and field kits; avoid storing personal device identifiers by default. |
| NFC | Tap-to-identify sample boxes, equipment, tags | Good pre-field setup feature if tags exist. Requires deliberate close-range tap. |
| Pedometer/activity | Walking/running/stopped/fall-like event | Useful with pocket mode and disaster triage. Not proof of injury. |
| Screen/lock/orientation state | Whether the user can interact with the device | Helps decide voice-only versus screen-assisted mode. |

## External Field Sensors

| Sensor | Use | Notes |
|--------|-----|-------|
| BLE temperature/humidity logger | Cold chain, incubator/freezer context, field weather | High value; common with old/cheap data loggers. |
| CO2/VOC/gas sensor | Ventilation, fuel/solvent/gas context | Treat as screening unless calibrated and cross-checked. |
| Radiation dosimeter | Disaster/field safety | Requires calibrated device and site-specific authority. |
| pH / conductivity / dissolved oxygen | Water quality and field chemistry | Good for protocol support; record calibration state and units. |
| Turbidity/colorimeter | Water/sample condition | Needs device-specific calibration and method. |
| Scale/balance | Sample mass, reagent mass | Record model/calibration; do not infer from phone sensors. |
| Thermal probe | Incubator, freezer, sample, ambient conditions | Better than phone battery/thermal state for real temperature. |
| Weather station / anemometer | Wind, pressure, rainfall, temperature | Useful for disaster and field safety; capture source and units. |
| LoRa / mesh / satellite beacon | Offline packets, location pings, worker status | Useful when cellular data fails; separate from Vapi voice path. |

## Documentation Contract

Every sensor record should include:

- sensor/source type;
- unit;
- reading;
- timestamp;
- phone placement or sensor placement;
- calibration state if known;
- confidence;
- whether it was caller-spoken, app-supplied, local-model-derived, or
  server-inferred;
- retention level: derived-only by default.

## v1 Boundary

For today’s demo, keep the sensor story simple:

“PhoneBio accepts spoken or app-supplied low-level sensor context. It can record
GPS, pressure, compass, pocket state, audio overlap, vibration, and gestures now.
External sensors and local quantized models are the next layer.”
