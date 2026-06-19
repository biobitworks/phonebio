# InsForge Backend Candidate

PhoneBio v1 runs file-local. Use InsForge only if the hackathon demo needs hosted persistence or a lightweight admin surface.

## Candidate Tables

### `protocols`

| Column | Type | Notes |
|--------|------|-------|
| `id` | text primary key | Local source ID, e.g. `water_quality_grab_sample`. |
| `title` | text | Human-readable title. |
| `domain` | text | Biology domain. |
| `keywords` | jsonb | Search terms. |
| `hazards` | jsonb | Safety tags. |
| `read_aloud_summary` | text | Short voice summary. |
| `body_markdown` | text | Full protocol text. |
| `source_hash` | text | SHA-256 of source record. |

### `safety_sheets`

| Column | Type | Notes |
|--------|------|-------|
| `id` | text primary key | Local SDS summary ID. |
| `name` | text | Substance name. |
| `synonyms` | jsonb | Lookup aliases. |
| `hazards` | jsonb | Hazard statements. |
| `ppe` | jsonb | PPE summary. |
| `first_aid` | jsonb | First-action guidance. |
| `disclaimer` | text | Must state this is not the authoritative SDS. |
| `source_hash` | text | SHA-256 of source record. |

### `hardware_guides`

| Column | Type | Notes |
|--------|------|-------|
| `id` | text primary key | Guide ID. |
| `device` | text | Device class. |
| `symptom` | text | Symptom summary. |
| `keywords` | jsonb | Search terms. |
| `steps` | jsonb | Ordered troubleshooting checks. |
| `escalate_if` | text | Stop condition. |

### `sensor_profiles`

| Column | Type | Notes |
|--------|------|-------|
| `id` | text primary key | `accelerometer`, `gyroscope`, `barometer`, `uwb`, `lidar`, etc. |
| `measures` | text | Measurement description. |
| `accuracy` | jsonb | Best/typical/worst/confidence. |
| `error_sources` | jsonb | Sources of variation. |
| `calibration` | text | Voice-guided calibration check. |
| `voice_guidance` | text | Read-aloud instruction. |

### `call_receipts`

| Column | Type | Notes |
|--------|------|-------|
| `id` | text primary key | Local generated receipt ID. |
| `call_id_hash` | text | Hash only; no raw phone number. |
| `tool_name` | text | Tool invoked. |
| `source_ids` | jsonb | Local source IDs returned. |
| `created_at` | timestamptz | Receipt timestamp. |
| `redacted_summary` | text | No private field location or phone number. |

## Boundaries

- Do not store raw phone numbers.
- Do not store raw transcripts by default.
- Do not mark InsForge rows as authoritative writeback into any portfolio system.
- Keep local file content as v1 source of truth until an explicit migration is approved.

