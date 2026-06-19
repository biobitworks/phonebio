# Nebius Token Factory Integration

Nebius is not part of the current funded/API path. PhoneBio's active external APIs are Vapi now and InsForge later; the optional LLM endpoint is local Ollama only.

## Deferred Environment

```bash
# Do not set these for v1 unless a separate approved credit source exists.
# Nebius credential variables intentionally omitted from the v1 template.
```

Local Ollama is the only active LLM route in v1.

## Endpoint

PhoneBio exposes an optional local custom-LLM route:

```text
POST /custom-llm/chat/completions
```

Use this only for free-form reasoning/summarization. Deterministic protocol, SDS, hardware, sensor, and shorthand work stays on `/webhook`.

## Hackathon Policy

- Do not require Nebius for v1 demo.
- Treat Nebius as a deferred research note unless separately funded.
- Keep all safety-critical protocol lookup deterministic and source-backed.
- Record provider choice in call receipts before storing any summaries.
