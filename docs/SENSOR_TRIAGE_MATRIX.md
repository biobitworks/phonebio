# Sensor Triage Matrix

PhoneBio should treat phone and nearby-device sensors as low-level context
signals. They can route attention and processing, but they do not prove identity,
exact headcount, chemical identity, or final incident classification without
caller confirmation or calibrated external instruments.

Environment mode matters. The same signal should be interpreted differently in
dense rainforest canopy, desert/open field, or a remote field station. See
`docs/FIELD_ENVIRONMENT_MODES.md`.

Device mode matters too. The current demo phone is an iPhone 11; see
`docs/IPHONE_11_FIELD_PROFILE.md` for what is and is not available.

## Triage Rule

Use each sensor as one vote in a fused context matrix:

```text
raw sensor -> low-level feature -> confidence/boundary -> triage lane
```

Triage lanes:

- `normal_call`
- `sensor_context`
- `noisy_confirmation`
- `emergency_priority`

## Matrix

| Signal | What It Can Help Detect | Strongest Use | Limits | Triage Effect |
|---|---|---|---|---|
| Microphone loudness | Loud machinery, alarm, shout, impact sound, possible fire alarm | Noisy call handling and emergency cues | Cannot identify speaker or hazard alone | `noisy_confirmation` or `emergency_priority` |
| Voice activity / overlap | Possible second speaker, radio chatter, assistant echo | Ask caller if another worker/radio/equipment is nearby | Not exact headcount or identity | `noisy_confirmation` |
| Local speech keywords | "fire", "spill", "exposure", "can't breathe", "stop work" | Immediate safety triage | ASR errors; confirm critical terms | `emergency_priority` |
| Accelerometer | Vibration, impact, fall-like event, machinery shake, pocket movement | Equipment malfunction and worker-motion context | Phone placement dominates readings; cannot identify source by itself | `sensor_context` or `emergency_priority` |
| Gyroscope / rotation vector | Sudden rotation, phone orientation, device handling | Pocket/hand/bench/equipment placement inference | Not calibrated equipment measurement | `sensor_context` |
| Magnetometer / compass | Heading, magnetic disturbance near motors/equipment | Orientation and possible nearby powered equipment cue | Not a reliable object-specific magnetic moment detector | `sensor_context` |
| Barometer | Pressure trend, elevation change, weather/ventilation/door pressure changes | Context for environment, altitude, severe weather, enclosed-space changes | Not a standalone fire detector; fire needs heat/smoke/gas/caller cues | `sensor_context`; can support `emergency_priority` when fused |
| Relative humidity | Humidity trend, rain/wet environment, dew point when paired with ambient temperature | Rainforest, cold-chain, sample handling, condensation risk, worker/equipment context | Android supports `TYPE_RELATIVE_HUMIDITY` when hardware exists; not guaranteed on every phone and not generally exposed as an iPhone app sensor | `sensor_context`; can support field-environment risk when fused |
| GPS / GNSS | Location, speed, outdoor movement, degraded location accuracy | Relay facts and incident location | Poor indoors; accuracy must be reported | `sensor_context` or emergency relay |
| BLE | Nearby phones, tags, radios, instruments if broadcasting | Device proximity cue | Permission/platform limits; not person identity | `noisy_confirmation` |
| UWB | Fine-range nearby compatible devices/tags | Relative proximity and location in supported systems | Requires compatible devices and permissions | `sensor_context` |
| LiDAR / depth | Nearby surfaces, room geometry, distance-to-object, obstruction, rough workspace layout | Hands-free spatial context and obstacle/equipment proximity on supported devices | Device-specific; may violate no-imaging rules at some sites; not chemical/fire classification | `sensor_context`; can support safety routing when allowed |
| Radar-like gesture/proximity | Micro-gestures, near-device motion, approach/leave cues on rare supported phones or external hardware | Hands-free control and nearby-motion cue without camera | Not broadly available; not identity/headcount; treat as optional | `sensor_context` or `noisy_confirmation` |
| NFC | Intentional tap/tag scan | Equipment or sample tag confirmation | Requires deliberate close contact | `sensor_context` |
| Proximity sensor | Near face/pocket/covered screen | Hands-free mode and placement | Device-dependent browser/app access | `sensor_context` |
| Ambient light | Pocket, dark room, face-down, flashlight change | Phone placement and visibility context | Not a hazard detector | `sensor_context` |
| Battery / thermal | Phone overheating, low battery, power constraints | Degraded-mode planning | Not environmental heat proof | local resource throttling |
| Network state | Voice-only, low data, offline, weak signal | Choose call-first and compact packets | Does not measure site safety | route local/Vapi/InsForge/Nebius |
| External gas/smoke sensor | Smoke, CO, VOC, oxygen deficiency, gas alarm | Strong emergency signal if calibrated | Requires external calibrated hardware | `emergency_priority` |
| External temperature / thermal | Heat/fire proximity, cold stress | Stronger fire/environment cue than phone barometer | Phone battery temp is not ambient temp | `emergency_priority` when high |
| Wearable heart rate / fall | Physiological stress, fall cue | Worker safety escalation | Consent and device availability required | `emergency_priority` when severe |

## Fire / Chemical Spill Fusion

Fire confidence should come from multiple cues:

- caller says fire, smoke, heat, alarm, or flame
- microphone detects alarm/loud event
- accelerometer detects impact or rushed movement
- barometer shows sudden pressure/ventilation anomaly
- relative humidity changes support weather/steam/condensation context when the
  device has a humidity sensor, but do not classify fire alone
- external smoke/gas/temperature sensor reports alarm
- LiDAR/depth reports obstruction or unsafe proximity only if spatial sensing is
  allowed at the site
- GPS/location identifies a high-risk area

Chemical spill confidence should come from:

- caller-reported chemical name or container label
- local safety sheet match
- odor/fume/exposure symptoms reported by caller
- external gas/VOC sensor if available
- humidity and ambient temperature if relevant to fumes, condensation, sample
  integrity, or rainforest/desert field context
- PPE/skin/contact context
- location and ventilation context

## Barometer Boundary

Barometric pressure is useful but should be bounded:

- Good for pressure trend, altitude/elevation, weather, and enclosed-space
  pressure/ventilation anomalies.
- Potentially useful as one fused clue for blast, door opening, HVAC change, or
  severe environmental shift.
- Not sufficient to classify fire, chemical spill, number of people, or speaker
  count.

## Emergency Priority Rule

Escalate to `emergency_priority` when any of these are present:

- fire, smoke, explosion, gas, uncontrolled chemical release
- breathing difficulty, collapse, burn, major exposure, serious injury
- uncontrolled rotating/electrical/pressurized hardware
- caller cannot reach emergency services and needs immediate life-safety steps

Immediate response language:

```text
Call emergency services or get someone nearby to call if possible.
If you cannot reach them, stop work, move away/upwind if safe, warn others,
avoid fumes/contact, do not re-enter, and give me location, hazard, injuries,
and callback/relay details.
```

## References

- Apple Core Motion: https://developer.apple.com/documentation/coremotion/
- Android sensors overview: https://developer.android.com/develop/sensors-and-location/sensors/sensors_overview
- OSHA emergency action plans: https://www.osha.gov/etools/evacuation-plans-procedures/eap
- NIOSH Pocket Guide to Chemical Hazards: https://www.cdc.gov/niosh/npg/default.html
- EPA hazardous release reporting: https://www.epa.gov/emergency-response/emergency-response-and-recognizing-hazardous-substance-releases
