# Nebius Token Factory Integration

Nebius is active for the live GPU reasoning lane when hackathon/free credits and
`NEBIUS_API_KEY` are configured. PhoneBio's active live services are Vapi for
phone orchestration, InsForge for the hosted webhook and custom-LLM proxy, and
Nebius Token Factory for the model call behind that proxy. The deterministic
protocol, SDS, hardware, sensor, and shorthand tool layer does not call Nebius.

## Cookbook-Aligned Environment

```bash
cp .env.example .env
NEBIUS_API_KEY=your_api_key_here
NEBIUS_BASE_URL=https://api.tokenfactory.nebius.com/v1
NEBIUS_MODEL=meta-llama/Llama-3.3-70B-Instruct
LLM_PROVIDER_ORDER=nebius,local
```

This mirrors the Nebius Token Factory cookbook's local `.env` pattern while
keeping secrets local or hosted in InsForge, not committed.

## Probe

```bash
make nebius-probe
```

To list available model IDs without sending a chat completion:

```bash
make nebius-models
```

The probe sends a tiny non-sensitive chat-completions request to:

```text
POST https://api.tokenfactory.nebius.com/v1/chat/completions
```

It prints only redacted API-key state, base URL host, model, HTTP status,
latency, whether a response was present, and whether a stale configured model
was replaced by an available model for the probe.

If a configured model is unavailable, first check:

```bash
python3 scripts/nebius_probe.py --list-models
```

## Hosted Custom-LLM Endpoint

PhoneBio exposes an optional Vapi-compatible custom-LLM route:

```text
POST https://qfdp5nuv.function2.insforge.app/phonebio-llm/chat/completions
```

If `NEBIUS_API_KEY` is set in the hosted function environment, this endpoint
routes live Vapi model turns through Nebius. Deterministic protocol, SDS,
hardware, sensor, and shorthand work stays on the hosted Vapi webhook.

Fallback is failure-only: the proxy tries Nebius first, and if the key/network
path fails it may return a clearly labeled deterministic response with model
`phonebio-deterministic-fallback`.

## Hackathon Policy

- Use Nebius only after free credits/API access are approved.
- No OpenAI key is used; Nebius uses its own `NEBIUS_API_KEY`.
- Keep all safety-critical protocol lookup deterministic and source-backed.
- Record provider choice in call receipts before storing any summaries.

## Cookbook References

- `nebius/token-factory-cookbook` uses `NEBIUS_API_KEY` in `.env`.
- The cookbook includes OpenAI-compatible API examples, agent examples, RAG
  examples, and simple function/tool-calling examples. PhoneBio adopts the
  API-key/env and chat-completions pattern, not the notebook workflow.
