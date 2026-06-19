# PhoneBio

PhoneBio is a hackathon voice-agent prototype for a field biology worker with limited internet access. The worker can call a Vapi phone number and ask for protocols, safety material, hardware troubleshooting, or sensor-based reasoning without requiring camera access.

## v1 Shape

- Vapi answers inbound calls and uses custom tools.
- A local FastAPI webhook serves tool results from repository data only.
- A dependency-free Node webhook remains available as a fallback.
- Phone sensor support is treated as narrated or app-provided readings: accelerometer, gyroscope, barometer, UWB, and LiDAR where available.
- Camera-dependent workflows are out of scope for v1.

## Local Run

Primary FastAPI runtime:

```bash
python3 -m pip install -r requirements.txt
make test
make dev
```

Node fallback:

```bash
npm test
npm start
```

Expose the webhook for Vapi testing:

```bash
make expose
```

Configure the Vapi assistant using `vapi/assistant.field-biology-worker.json` as the dashboard/API reference. Set the assistant server URL to the forwarded webhook URL.

Dry-run Vapi wiring:

```bash
make wire-dry-run
```

Live Vapi wiring needs `VAPI_API_KEY` or `VAPI_PRIVATE_KEY`, `VAPI_PHONE_NUMBER_ID`, and `VAPI_WEBHOOK_URL` or `PUBLIC_BASE_URL`. See `docs/VAPI_RUNBOOK.md`.

## Tool Names

- `get_protocol`
- `get_safety_sheet`
- `troubleshoot_hardware`
- `interpret_sensor_report`
- `compress_observation`

## Runtime Boundary

The webhook does not call the internet. Vapi is the only API needed for the live phone agent; InsForge is deferred until persistent storage/backend features are needed. No OpenAI API key is used.

Ollarma status on 2026-06-19: reachable but degraded with `SELECTION_STALE`; Watchtower bridge aggregator unreachable. See `docs/OLLARMA_CLAUDE_HANDOFF.md`.

Optional custom LLM endpoint:

- `GET /llm/health`
- `POST /custom-llm/chat/completions`

This route uses local Ollama only.
