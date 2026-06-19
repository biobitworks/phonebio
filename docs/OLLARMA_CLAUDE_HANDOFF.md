# Ollarma / Claude Code Handoff

**Date:** 2026-06-19
**Project:** PhoneBio
**Role:** PI / PM / Operator

## Current Objective

Bring PhoneBio to hackathon v1: a Vapi call-in field biology worker that retrieves local protocols, safety summaries, hardware troubleshooting, and camera-free phone sensor guidance.

## Current Repo State

- Public repo: `https://github.com/biobitworks/phonebio`
- Main branch contains GSD planning docs, FastAPI webhook, Node fallback webhook, tests, Vapi assistant template, local content, source intake sidecars, and runbooks.
- Primary runtime: `make dev` on port `8080`.
- Webhook endpoint: `POST /webhook`.
- Health endpoint: `GET /health`.

## Ollarma Bring-Up Checkpoint

1. `ollarma-fasttrack-context`: PASS. Governing docs read. Boundary: local-first, receipt-first, no silent escalation, no writeback.
2. `ollarma-bridge-status`: DEGRADED. Watchtower aggregator at `127.0.0.1:8002` is unreachable. Ollarma at `127.0.0.1:8484` is reachable but reports `SELECTION_STALE`; fallback model `qwen2.5:1.5b` is available. Swap posture is ready. Gateway is disabled by default.
3. `ollarma-preflight`: NOT RUN. Bring-up chain stops at degraded bridge status per skill contract.
4. `ollarma-swarm-smoke`: NOT RUN. Bring-up chain stops at degraded bridge status per skill contract.

Recommended safe remediation:

- `ollarma-selection-refresh --operator-acknowledged --execute`
- Restart or bring up Watchtower if the aggregator is required.

Do not run `ollarma-swarm-proof` without explicit operator acknowledgement and a fresh preflight PASS.

## Claude Code Handoff Prompt

```text
You are Claude Code working in /Users/byron/projects/active/phonebio.

Goal: harden PhoneBio hackathon v1 without changing the camera-free premise.

Read first:
- AGENTS.md
- .planning/PROJECT.md
- .planning/REQUIREMENTS.md
- .planning/ROADMAP.md
- docs/VAPI_RUNBOOK.md
- docs/SENSOR_CAPABILITY_MATRIX.md

Verify:
- make test
- make smoke
- python3 vapi/wire.py create-assistant --assign-phone --dry-run

Do not:
- commit secrets, phone numbers, raw transcripts, or private field locations
- require camera input
- call Vapi live unless VAPI_API_KEY/VAPI_PHONE_NUMBER_ID/VAPI_WEBHOOK_URL are explicitly present and the operator asks for it
- run Ollarma swarm proof without explicit operator acknowledgement

Next useful work:
1. Expand local protocol and SDS content with source IDs.
2. Add real Vapi webhook event fixture tests for `message.type == "tool-calls"`.
3. Add a hosted deployment option or InsForge schema only if needed for the hackathon demo.
```

