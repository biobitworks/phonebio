# Requirements: PhoneBio

**Defined:** 2026-06-19
**Core Value:** A field worker can call in and get the next safe, protocol-grounded action from local knowledge when the network is unreliable and the camera is unavailable.

## v1 Requirements

### Voice Agent

- [ ] **VOICE-01**: Caller can reach a Vapi assistant assigned to the project phone number. **Status:** live assistant created and phone number assigned through Vapi API; pending inbound or outbound call verification. The hosted InsForge webhook is reachable; no OpenAI key or custom-LLM URL is required for the current `google` provider assistant.
- [x] **VOICE-02**: Assistant uses a field-biology system prompt that keeps responses short, asks one clarifying question at a time, and escalates safety uncertainty.
- [x] **VOICE-03**: Assistant can call custom tools through a server URL and receive structured results.

### Offline Knowledge

- [x] **KNOW-01**: Tool server can retrieve a local protocol by organism, task, or hazard keyword.
- [x] **KNOW-02**: Tool server can retrieve a local safety-material summary by substance or hazard.
- [x] **KNOW-03**: Tool server can return "not found" guidance without hallucinating a protocol.
- [x] **KNOW-04**: Every local answer includes source IDs or local record IDs for later audit.

### Hardware Support

- [x] **HARD-01**: Tool server can troubleshoot common field hardware issues from a natural-language symptom.
- [x] **HARD-02**: Troubleshooting answers include safe stop conditions and when to call a supervisor.

### Sensor Reasoning

- [x] **SENS-01**: Tool server can interpret caller-provided accelerometer or gyroscope readings for orientation, vibration, or handling checks.
- [x] **SENS-02**: Tool server can interpret caller-provided barometer readings for relative elevation or weather-change context.
- [x] **SENS-03**: Tool server can explain UWB and LiDAR availability limits and confidence bands without requiring camera use.
- [x] **SENS-04**: Sensor guidance distinguishes measured data, inferred state, and uncertainty.

### Deployment and Governance

- [x] **GOV-01**: Repo includes a Vapi assistant configuration template with no secrets.
- [x] **GOV-02**: Repo includes source-intake and deferred-writeback JSONL sidecars.
- [x] **GOV-03**: Repo includes local tests for webhook parsing and offline tool answers.
- [x] **GOV-04**: Public GitHub publication path excludes secrets, phone numbers, and private transcripts.

## v2 Requirements

### Native Phone App

- **APP-01**: Native mobile app streams permissioned sensor readings to the assistant workflow.
- **APP-02**: App stores signed offline observation packets for later sync.
- **APP-03**: App supports calibrated field-device profiles per phone model.

### Model and Backend Integrations

- **INT-01**: InsForge stores versioned protocol records, safety sheets, and call summaries after backend persistence is approved.
- **INT-02**: Ollarma routes local model tasks when local routing is healthy.
- **INT-03**: Nebius remains deferred outside the current funded/API path unless a separate approved credit source exists.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Camera image analysis | Objective assumes camera is unavailable. |
| Live web search during field calls | Limited internet and safety provenance constraints. |
| Certified SDS replacement | Local summaries need later validation against official SDS files. |
| Emergency dispatch automation | Requires legal, operational, and site-specific authority. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| VOICE-01 | Phase 2 | Partial - Vapi assistant created and selected phone number assignment verified; inbound/outbound call verification still required |
| VOICE-02 | Phase 1 | Pass - `make readiness` |
| VOICE-03 | Phase 1 | Pass - `make readiness` |
| KNOW-01 | Phase 1 | Pass - `make readiness` |
| KNOW-02 | Phase 1 | Pass - `make readiness` |
| KNOW-03 | Phase 1 | Pass - `make readiness` |
| KNOW-04 | Phase 1 | Pass - `make readiness` |
| HARD-01 | Phase 1 | Pass - `make readiness` |
| HARD-02 | Phase 1 | Pass - `make readiness` |
| SENS-01 | Phase 1 | Pass - `make readiness` |
| SENS-02 | Phase 1 | Pass - `make readiness` |
| SENS-03 | Phase 1 | Pass - `make readiness` |
| SENS-04 | Phase 1 | Pass - `make readiness` |
| GOV-01 | Phase 1 | Pass - `make readiness` |
| GOV-02 | Phase 1 | Pass - `make readiness` |
| GOV-03 | Phase 1 | Pass - `make readiness` |
| GOV-04 | Phase 2 | Pass - `make readiness` |

**Coverage:**
- v1 requirements: 17 total
- Mapped to phases: 17
- Unmapped: 0

---
*Requirements defined: 2026-06-19*
*Last updated: 2026-06-19 after readiness audit*
