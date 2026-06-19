# Nebius Token Factory Integration

PhoneBio is already shaped for Nebius because `fieldbio.llm` uses OpenAI-compatible chat completions.

## Environment

```bash
export NEBIUS_API_KEY
export NEBIUS_BASE_URL="https://api.tokenfactory.nebius.com/v1/"
export NEBIUS_MODEL="<chosen model>"
export LLM_PROVIDER_ORDER="local,nebius,openai"
```

Local Ollama remains first. Nebius is attempted only when `NEBIUS_API_KEY` is present.

## Endpoint

PhoneBio exposes an optional OpenAI-compatible route:

```text
POST /custom-llm/chat/completions
```

Use this only for free-form reasoning/summarization. Deterministic protocol, SDS, hardware, sensor, and shorthand work stays on `/webhook`.

## Hackathon Policy

- Do not require Nebius for v1 demo.
- Treat Nebius as a cloud upgrade once credits are available.
- Keep all safety-critical protocol lookup deterministic and source-backed.
- Record provider choice in call receipts before storing any summaries.

