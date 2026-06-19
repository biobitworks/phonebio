# Legacy Equipment Database Plan

PhoneBio should prepare old-equipment references before field deployment. The
call-time assistant should not browse the web for manuals during a safety or
disaster scenario.

## Candidate Sources

| Source | Use | Notes |
|--------|-----|-------|
| iFixit Laboratory Equipment | Repair guides and device pages for lab equipment | Has an API and public repair-guide structure. Good first source for structured ingest. |
| iFixit Medical Device | Older/clinical equipment repair manuals and guides | Useful for disaster relief and biomedical-adjacent field gear. Check scope/safety boundaries. |
| WHO Maintenance Manual for Laboratory Equipment | General maintenance and safety reference | Good baseline for common lab equipment categories and maintenance concepts. |
| NIH Office of NIH History manual collection | Historical manuals, operating instructions, technical bulletins | Strong source for older equipment families. Requires custody/license review per asset. |
| Internet Archive | Public/manual scans and historical documents | Useful fallback for old gear; requires careful source/license metadata. |
| LabWrench / MedWrench | Manuals/forums for lab and medical equipment | Useful for discovery; some downloads/account access may block automated ingest. |
| Local institutional manual collections | Known equipment in actual labs/field kits | Best operational source when we know the exact model. |

## Ingest Shape

Each equipment record should include:

- manufacturer;
- model and aliases;
- year or approximate era;
- equipment class;
- power requirements;
- consumables;
- common failure symptoms;
- safe stop conditions;
- field-safe checks;
- do-not-open conditions;
- manual/source IDs;
- hash/provenance;
- copyright/license/custody status.

## Call-Time Rule

At call time, PhoneBio should only use reviewed local/InsForge equipment records.
If no record matches, it should say:

“No local hardware guide matched. Power down if unsafe, preserve the sample
state, and call the equipment owner or site supervisor.”

## Priority Equipment Classes

1. Centrifuges and rotors.
2. pH meters and conductivity meters.
3. Micropipettes and bottle-top dispensers.
4. Incubators and dry blocks.
5. Refrigerators/freezers/cold-chain loggers.
6. Spectrophotometers/colorimeters.
7. Autoclaves/sterilizers.
8. Pumps, vacuum manifolds, and field filtration rigs.
9. Bluetooth/GNSS/data loggers.
10. Portable power supplies and chargers.

## Next Build Step

Create a `legacy_equipment` table/artifact from reviewed sources, then map each
record to `troubleshoot_hardware` so the voice agent can answer old-equipment
questions without live data service.
