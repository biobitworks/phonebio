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
make readiness
make dev
```

Node fallback:

```bash
npm test
npm start
```

Expose the full app for live Vapi testing:

```bash
make tunnel
export PUBLIC_BASE_URL="https://your-public-url"
make public-probe
```

`make expose` starts Vapi CLI webhook forwarding only. The current checked-in
assistant uses the hosted InsForge webhook and Vapi's `google` model provider,
so a custom-LLM URL is not required for the live hackathon path.

Configure the Vapi assistant using `vapi/assistant.field-biology-worker.json` as the dashboard/API reference. Set the assistant server URL to the forwarded webhook URL.

Dry-run Vapi wiring:

```bash
make wire-dry-run
make hosted-probe
make vapi-preflight
make vapi-verify-call
make vapi-wait-call
python3 vapi/wire.py list-phone-numbers
```

Local v1 readiness status:

```bash
make readiness
```

This reports all locally provable requirements and leaves live Vapi phone assignment blocked until credentials and public URLs are supplied.

Local Ollama custom-LLM tool-call probe:

```bash
make llm-probe
```

This verifies the configured local model emits a Vapi-compatible tool call and that model reasoning fields are scrubbed before returning to Vapi.

Optional Nebius Token Factory probe, after hackathon/free credits are active:

```bash
export NEBIUS_API_KEY="..."
export LLM_PROVIDER_ORDER=nebius,local
make nebius-models
make nebius-probe
```

This follows the cookbook `NEBIUS_API_KEY` setup and uses Nebius's
OpenAI-compatible chat-completions endpoint. It is not required for the live
Vapi + InsForge demo.

Provider/credit routing is documented in `docs/PROVIDER_STRATEGY.md`.
Vapi dashboard resource usage is documented in `docs/VAPI_RESOURCE_STRATEGY.md`.

Local hackathon call-script replay:

```bash
make demo-call
make hosted-demo
```

This replays the protocol, safety, hardware, sensor, and shorthand turns from the Vapi demo script against the local webhook tools and hosted InsForge function.

InsForge backend preview:

```bash
python3 scripts/insforge_export.py --summary
make insforge-export > /tmp/phonebio-insforge-seed.jsonl
```

The migration in `migrations/` and seed export are for reviewed persistence only; v1 still runs file-local.

Live Vapi wiring needs `VAPI_API_KEY` or `VAPI_PRIVATE_KEY`, `VAPI_PHONE_NUMBER_ID`, and `VAPI_WEBHOOK_URL` or `PUBLIC_BASE_URL`. See `docs/VAPI_RUNBOOK.md`.

## Tool Names

- `get_protocol`
- `get_safety_sheet`
- `troubleshoot_hardware`
- `interpret_sensor_report`
- `compress_observation`

## Runtime Boundary

The local webhook does not call the internet. The live hackathon path uses Vapi
for the phone agent and the hosted InsForge function for tool dispatch. No
OpenAI API key is used. InsForge credentials are needed only to redeploy or
change the hosted function or to add persistence.

Ollarma status on 2026-06-19: reachable but degraded with `SELECTION_STALE`; Watchtower bridge aggregator unreachable. See `docs/OLLARMA_CLAUDE_HANDOFF.md`.

Optional custom LLM endpoint:

- `GET /llm/health`
- `POST /custom-llm/chat/completions`

This route uses local Ollama only. The default local model is `qwen3:1.7b` because it emits tool calls in the local probe; no cloud LLM key is used.
