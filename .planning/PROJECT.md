# PhoneBio

## What This Is

PhoneBio is an offline-first voice agent for field biology workers who have limited internet and cannot rely on a camera. A caller reaches a Vapi phone number and asks for protocols, safety material, hardware troubleshooting, or help interpreting phone sensor readings by description.

The v1 product is a hackathon-grade call assistant plus local tool server. It prioritizes reliable spoken retrieval and guided reasoning over broad web search or image analysis.

## Core Value

A field worker can call in and get the next safe, protocol-grounded action from local knowledge when the network is unreliable and the camera is unavailable.

## Requirements

### Validated

(None yet - ship to validate)

### Active

- [ ] Create a Vapi-compatible field biology voice assistant configuration.
- [ ] Serve Vapi custom tool calls from offline local protocols, safety sheets, and troubleshooting data.
- [ ] Support camera-free sensor workflows for accelerometer, gyroscope, barometer, UWB, and LiDAR readings when available.
- [ ] Document sensor variation, expected accuracy limits, and fallback behavior.
- [ ] Prepare local git/GitHub publication path without committing secrets or phone numbers.
- [ ] Keep Nebius, InsForge, and Ollarma integration points explicit but optional for v1.

### Out of Scope

- Camera capture or image-based identification - the premise assumes camera access is unavailable.
- Live regulatory SDS certification - v1 retrieves local safety summaries and must point to validated source sheets later.
- Fully autonomous emergency response - the assistant can recommend escalation but not replace site safety authority.
- Raw private caller transcripts in git - calls may contain sensitive field location or incident data.

## Context

- Vapi quickstart documentation describes phone-call assistants that can be created in the dashboard or SDK, assigned to phone numbers, and extended with custom tools via server URLs.
- Vapi custom tool responses return a `results` array keyed by `toolCallId`.
- Gregg shorthand is useful as a design metaphor for compact phonetic capture: store only the discriminating parts of field observations, prefer phrase forms, and ask clarifying questions when omitted detail affects safety.
- Nebius Token Factory is an OpenAI-compatible inference surface and has a public cookbook for agents, RAG, and function/tool calling examples.
- InsForge is an AI-native backend platform with Postgres, auth, storage, functions, hosting, and model gateway primitives. It is a candidate backend if the hackathon requires persistent users or hosted knowledge.
- Ollarma can later route local/offline inference, but the v1 webhook must work without it.

## Constraints

- **Connectivity**: Runtime answers must come from local repository data - field calls may have limited internet.
- **Safety**: Safety material must be conservative, cite local source IDs, and escalate when a request is outside known material.
- **Sensor access**: Browser access to UWB and LiDAR is limited; v1 treats readings as spoken/manual input or future native-app payloads.
- **Secrets**: Vapi, Nebius, and phone-number identifiers stay in environment variables or local ignored files.
- **Timeline**: Hackathon v1 favors a demonstrable inbound call workflow over complete mobile-native sensor capture.
- **Git**: `phonebio` currently lives inside the broader `/Users/byron/projects` worktree, so public-repo setup must avoid leaking unrelated portfolio state.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Vapi phone-call assistant first | The user already has a Vapi test number and wants call-in access. | - Pending |
| Offline local knowledge before RAG | The field worker may not have internet and safety answers need deterministic provenance. | - Pending |
| Camera-free sensor descriptions | The objective explicitly excludes camera use while preserving other phone sensors. | - Pending |
| Node webhook with no runtime dependencies | Fast to demo and easy to expose through Vapi CLI forwarding. | - Pending |
| Nebius/InsForge deferred | API credits and backend account decisions are not yet available. | - Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? Move to Out of Scope with reason.
2. Requirements validated? Move to Validated with phase reference.
3. New requirements emerged? Add to Active.
4. Decisions to log? Add to Key Decisions.
5. "What This Is" still accurate? Update if drifted.

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections.
2. Core Value check - still the right priority?
3. Audit Out of Scope - reasons still valid?
4. Update Context with current state.

---
*Last updated: 2026-06-19 after initialization*

