# Basic First Aid Kit Mode

PhoneBio can use a physical first aid kit as a demo prop and as a bounded field
support mode. The agent should not diagnose, prescribe, or replace emergency
services, poison control, site safety, SDS, or a trained responder.

## Demo Boundary

Use the kit to show that the agent can:

- ask what supplies are available
- route immediate life-safety steps
- remind the caller to avoid exposure
- capture relay facts for responders
- avoid detailed cleanup, repair, or treatment instructions during danger

## Common Basic Kit Items

Likely items:

- disposable gloves
- adhesive bandages
- gauze pads / roller gauze
- adhesive tape
- antiseptic wipes
- saline / eye wash ampule
- small burn dressing or gel
- scissors
- tweezers
- emergency blanket
- CPR face shield
- first aid card / guide

Ask first:

```text
What do you have in the kit: gloves, clean water or saline, gauze, tape,
bandages, burn dressing, or a CPR shield?
```

## Safe First Actions

For any incident:

- Stop work.
- Move away from the hazard if safe.
- Warn nearby people.
- Call emergency services or get another person to call if possible.
- If emergency services cannot be reached, capture relay facts and keep trying.

For minor cuts/scrapes only:

- Put on gloves if available.
- Use clean gauze/bandage.
- Apply gentle pressure for bleeding.
- Keep the wound covered.
- Escalate if bleeding is heavy, deep, contaminated, or does not stop.

For chemical splash on skin or eyes:

- Avoid touching the chemical.
- Move away from fumes if safe.
- Remove contaminated gloves/clothing only if it can be done safely.
- Flush skin/eyes with clean water or eyewash if available.
- Seek emergency/medical help; use SDS/site guidance when available.

For burns:

- Move away from heat/source.
- Cool the burn with clean cool water if available.
- Cover loosely with clean dressing.
- Do not apply improvised substances.
- Escalate for serious, large, chemical, electrical, or face/airway burns.

For suspected inhalation/fumes:

- Move to fresh air/upwind if safe.
- Do not re-enter the area.
- Ask if anyone has breathing trouble.
- Escalate immediately.

## What The Agent Must Not Do

- Do not tell the caller to clean a hazardous spill during active danger.
- Do not tell the caller to re-enter a fire/smoke/fume area.
- Do not diagnose exposure severity.
- Do not give drug/medication instructions.
- Do not replace poison control, emergency services, SDS, or site command.

## First Aid Relay Packet

```json
{
  "environment": "rainforest | desert | field_station",
  "location": "caller provided location plus GPS accuracy if available",
  "hazard": "chemical | fire | hardware | biological | injury",
  "injuries": "none | unknown | described symptoms",
  "kitAvailable": ["gloves", "gauze", "saline"],
  "actionsTaken": ["moved away", "warned others", "flushed with water"],
  "emergencyContact": "reached | unavailable | nearby person asked"
}
```

## Demo Line

"The kit does not make PhoneBio a doctor. It lets the voice agent ask what
basic supplies are available, keep the worker away from the hazard, and capture
the facts a responder or site lead needs."

## References

- OSHA medical and first aid overview: https://www.osha.gov/medical-first-aid
- OSHA first aid kit appendix: https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.151AppA
- Red Cross first aid supplies: https://www.redcross.org/store/first-aid-supplies
- NIOSH Pocket Guide to Chemical Hazards: https://www.cdc.gov/niosh/npg/default.html
- CCOHS first aid for chemical exposure: https://www.ccohs.ca/oshanswers/chemicals/firstaid.html
