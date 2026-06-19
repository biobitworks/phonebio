# Deployment Runbook

PhoneBio needs a public HTTPS webhook before Vapi can call the local tool server during an inbound phone call.

## Option A: Direct App Tunnel

Best for a live hackathon demo from this laptop.

```bash
make dev
make tunnel
```

Copy the forwarded HTTPS URL and set:

```bash
export PUBLIC_BASE_URL="https://forwarded-url"
export VAPI_WEBHOOK_URL="${PUBLIC_BASE_URL}/webhook"
export VAPI_CUSTOM_LLM_URL="${PUBLIC_BASE_URL}/custom-llm"
make public-probe
make wire-dry-run
make wire
```

`make tunnel` exposes the full FastAPI app, so both `/webhook` and `/custom-llm/chat/completions` are reachable through the same public base URL.

## Option B: Vapi CLI Webhook Forwarder

Useful for webhook-event debugging only.

```bash
make dev
make expose
```

`make expose` uses:

```bash
vapi listen --forward-to localhost:8080/webhook
```

Per Vapi's current CLI documentation, `vapi listen` is a local webhook forwarder, not a public tunnel. It still needs a separate public tunnel to receive Vapi events, and it does not expose the full custom-LLM route directly.

## Option C: Container Host

The repo includes a `Dockerfile` and `Procfile`.

Required environment:

```bash
PORT=8080
VAPI_WEBHOOK_SECRET=<random secret if using Vapi Custom Credential>
LLM_PROVIDER_ORDER=local
OLLAMA_BASE_URL=http://host.docker.internal:11434/v1
```

No OpenAI key is used. InsForge credentials are optional and only needed once persistent storage/backend features are enabled.

Health check:

```bash
curl https://your-host/health
```

Webhook:

```bash
curl -X POST https://your-host/webhook \
  -H 'content-type: application/json' \
  -d '{"toolCalls":[{"id":"demo","name":"get_protocol","arguments":{"task":"water sample"}}]}'
```

## Webhook Authentication

If `VAPI_WEBHOOK_SECRET` is set to a non-placeholder value, `/webhook` and `/custom-llm/chat/completions` require either:

- `Authorization: Bearer <VAPI_WEBHOOK_SECRET>`
- `x-vapi-secret: <VAPI_WEBHOOK_SECRET>`

For Vapi, create a Custom Credential with a bearer token and attach it to the assistant server/custom-LLM configuration.

## Demo Readiness Checklist

- [ ] `make test` passes locally.
- [ ] `make smoke` passes locally.
- [ ] `make public-probe` reaches `/health`, `/webhook`, and `/llm/health` through the public URL.
- [ ] Public `/health` returns `{"status":"ok"}`.
- [ ] Public `/webhook` returns a Vapi-style `results` array.
- [ ] `make wire-dry-run` shows a real webhook URL.
- [ ] `make wire` creates/assigns the assistant.
- [ ] Inbound phone call reaches the PhoneBio assistant.
