# Roadmap: PhoneBio

## Milestone 1: Hackathon Voice Agent v1

### Phase 1: Offline Tool Server and Assistant Contract
**Goal:** Build a local Vapi webhook that answers field-biology tool calls from versioned local knowledge.
**Mode:** mvp
**Requirements:** VOICE-02, VOICE-03, KNOW-01, KNOW-02, KNOW-03, KNOW-04, HARD-01, HARD-02, SENS-01, SENS-02, SENS-03, SENS-04, GOV-01, GOV-02, GOV-03

**Success Criteria:**
1. `npm test` verifies Vapi tool-call parsing and offline responses.
2. `npm start` exposes `GET /health` and `POST /webhook`.
3. Assistant config names every v1 tool and avoids secrets.
4. Sensor guidance reports confidence and fallback behavior.

### Phase 2: Vapi Phone Number Wiring and Public Repo
**Goal:** Connect the assistant to the existing Vapi test number and publish a clean public GitHub repository.
**Mode:** mvp
**Requirements:** VOICE-01, GOV-04

**Success Criteria:**
1. Vapi dashboard or API has assistant assigned to the test number.
2. Webhook server is reachable through Vapi CLI forwarding or hosted endpoint.
3. Public repo contains only PhoneBio project files.
4. Secrets, private phone numbers, and transcripts are excluded.

### Phase 3: Optional Backend Expansion
**Goal:** Add InsForge persistence after the hackathon backend decision is ready; keep local Ollama as the only v1 LLM route.
**Mode:** mvp
**Requirements:** APP-01, APP-02, APP-03, INT-01, INT-02, INT-03

**Success Criteria:**
1. InsForge schema draft covers protocols, safety sheets, observations, and audit receipts.
2. Ollarma routing remains optional and does not block offline tool-server operation.
3. No OpenAI API key or paid cloud model fallback is required for v1.

## Coverage

| Requirement | Phase |
|-------------|-------|
| VOICE-01 | Phase 2 |
| VOICE-02 | Phase 1 |
| VOICE-03 | Phase 1 |
| KNOW-01 | Phase 1 |
| KNOW-02 | Phase 1 |
| KNOW-03 | Phase 1 |
| KNOW-04 | Phase 1 |
| HARD-01 | Phase 1 |
| HARD-02 | Phase 1 |
| SENS-01 | Phase 1 |
| SENS-02 | Phase 1 |
| SENS-03 | Phase 1 |
| SENS-04 | Phase 1 |
| GOV-01 | Phase 1 |
| GOV-02 | Phase 1 |
| GOV-03 | Phase 1 |
| GOV-04 | Phase 2 |
