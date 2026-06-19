# Deployment Runbook

PhoneBio needs a public HTTPS webhook before Vapi can call the local tool server during an inbound phone call.

## Option A: Vapi CLI Tunnel

Best for a live hackathon demo from this laptop.

```bash
make dev
make expose
```

Copy the forwarded HTTPS URL and set:

```bash
export VAPI_WEBHOOK_URL="https://forwarded-url/webhook"
make wire-dry-run
make wire
```

## Option B: Container Host

The repo includes a `Dockerfile` and `Procfile`.

Required environment:

```bash
PORT=8080
VAPI_WEBHOOK_SECRET=<random secret if using Vapi Custom Credential>
LLM_PROVIDER_ORDER=local,nebius,openai
OLLAMA_BASE_URL=http://host.docker.internal:11434/v1
```

`NEBIUS_API_KEY` is optional after credits are available.

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

If `VAPI_WEBHOOK_SECRET` is set to a non-placeholder value, `/webhook` requires either:

- `Authorization: Bearer <VAPI_WEBHOOK_SECRET>`
- `x-vapi-secret: <VAPI_WEBHOOK_SECRET>`

For Vapi, create a Custom Credential with a bearer token and attach it to the assistant server configuration.

## Demo Readiness Checklist

- [ ] `make test` passes locally.
- [ ] `make smoke` passes locally.
- [ ] Public `/health` returns `{"status":"ok"}`.
- [ ] Public `/webhook` returns a Vapi-style `results` array.
- [ ] `make wire-dry-run` shows a real webhook URL.
- [ ] `make wire` creates/assigns the assistant.
- [ ] Inbound phone call reaches the PhoneBio assistant.
