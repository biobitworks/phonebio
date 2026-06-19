# Field Environment Modes

PhoneBio should ask for or infer the operating environment because the same
sensor reading has different meaning in a rainforest, desert, or field station.

## Common Baseline

For all remote field scenarios:

- Voice call is the primary interface.
- Screen/app interaction is optional.
- Camera use is optional and must not be required.
- GPS accuracy must be reported, not assumed.
- Emergency services may be delayed or unreachable.
- The agent should capture relay facts early: location, hazard, injuries,
  callback path, nearby people/devices, and immediate action taken.

## Amazon Rainforest / Dense Canopy

Expected constraints:

- GPS can be degraded under canopy.
- High humidity and rain can affect devices, paper labels, and equipment.
- Loud rain, insects, generators, boats, or radios can degrade voice quality.
- Sample contamination and cold-chain failure are plausible.
- Power and network may be intermittent.

Useful signals:

| Signal | Use |
|---|---|
| GPS accuracy | Treat poor accuracy as expected; ask for station/transect/landmark if available. |
| Barometer | Weather/pressure trend and elevation context; not a standalone hazard detector. |
| Microphone | Loud rain, generator, radio chatter, possible alarm/overlap. |
| Accelerometer/gyro | Walking, slipping/fall-like motion, equipment vibration, phone-in-pocket context. |
| Battery/thermal | Low power and device stress from wet/humid conditions. |
| BLE/UWB/NFC | Nearby tags, instruments, sample containers, or field-team devices. |

Default triage behavior:

- Ask for location confidence and nearest known station/transect marker.
- Confirm whether the caller is alone or with a field team.
- Keep replies short because audio may be noisy.
- Prefer compact packets and local triage when data service is weak.

## Desert / Arid Field Site

Expected constraints:

- Heat, glare, dust, and dehydration risk affect worker performance and devices.
- GPS is often better than dense canopy, but cell service may be absent.
- Phone overheating and battery drain are more likely.
- Wind can degrade microphone quality.
- Fire, fuel, generator, vehicle, and electrical hazards may be more prominent.

Useful signals:

| Signal | Use |
|---|---|
| GPS | Often useful for relay coordinates; still report accuracy. |
| Battery/thermal | Detect local device overheating and conserve processing. |
| Barometer | Weather/elevation/pressure trend; dust storm or weather context only when fused. |
| Microphone | Wind, vehicle/generator noise, alarm, shouting. |
| Accelerometer/gyro | Fall-like events, vehicle movement, equipment vibration. |
| Ambient light/proximity | Pocket/covered phone, glare/face-down context. |

Default triage behavior:

- Ask if the caller is in shade/safe distance when heat or fire cues appear.
- Conserve local compute when phone is hot or battery is low.
- Prioritize location relay because coordinates may be the strongest signal.

## Remote Field Station

Expected constraints:

- Old hardware, generators, cold storage, centrifuges, pumps, radios, and
  improvised power are common.
- Chemicals, biological samples, and contaminated PPE may be present.
- There may be a local incident lead even when external emergency response is
  delayed.

Useful signals:

| Signal | Use |
|---|---|
| Microphone | Alarms, generator/centrifuge/pump noise, multiple voices. |
| Accelerometer/gyro | Bench vibration, centrifuge imbalance, phone placed on equipment. |
| BLE/UWB/NFC | Nearby equipment tags or worker devices. |
| Barometer | Weather/ventilation/door pressure context; not equipment diagnosis alone. |
| GPS | Station coordinate and relay point. |
| Network state | Choose local cache, Vapi call, or delayed sync. |

Default triage behavior:

- Ask whether there is a site supervisor, incident lead, or another worker.
- For uncontrolled hardware: stop work, move away, shut down only if safe and
  trained, and do not troubleshoot during fire/exposure.
- For spill/exposure: prioritize safety sheet lookup, PPE boundary, isolation,
  and relay facts.

## Environment Mode Prompt

If the environment is unknown, ask:

```text
Are you in dense canopy, desert/open field, a field station, vehicle, boat, or
inside a lab-like room?
```

Then ask one safety question:

```text
Is there fire, smoke, fumes, injury, breathing trouble, or uncontrolled
equipment?
```

## Routing

| Environment | Default Route |
|---|---|
| Rainforest, weak GPS/data | local ExecuTorch gate -> Vapi voice -> InsForge record |
| Desert, heat/low battery | local gate with power conservation -> Vapi voice |
| Field station, hardware/chemical | Vapi tools + InsForge record; Nebius only for heavy downstream analysis |
| Emergency services unreachable | emergency priority voice path; capture relay facts; retry escalation |
