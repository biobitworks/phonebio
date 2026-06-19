# Provider Strategy

PhoneBio v1 uses each external service for the narrow job it is best suited
for, with cost and safety boundaries kept explicit.

## v1 Routing

| Provider | v1 role | Credit policy | Safety boundary |
|----------|---------|---------------|-----------------|
| Vapi | Live phone number, voice session, assistant orchestration, call evidence. | Spend Vapi credits only on live demo calls and final verification. | Vapi can route tools but is not the source of protocol/SDS truth. |
| InsForge | Hosted Vapi webhook and deterministic local-record tool dispatch. | Use existing hosted function; no extra spend unless redeploying or adding persistence. | Protocol, SDS, hardware, sensor, and shorthand answers stay source-backed. |
| Nebius Token Factory | Optional model capacity for non-critical summarization, model/tool-calling experiments, and later evaluation. | Use only with hackathon/free credits and explicit `NEBIUS_API_KEY`; probe before routing real tasks. | Never make Nebius authoritative for SDS/protocol lookup in v1. |
| Ollama | Local/offline fallback for custom-LLM experiments. | Free local compute; use when local model quality is sufficient. | Optional brain only; deterministic `/webhook` tools remain source of truth. |

## Default Live Demo Path

```text
caller -> Vapi phone number -> PhoneBio assistant -> hosted InsForge webhook -> local/DB-backed tool records
```

This path does not use OpenAI and does not require Nebius.

## Nebius Activation

Use Nebius only when free credits/API access are active:

```bash
export NEBIUS_API_KEY
export LLM_PROVIDER_ORDER=nebius,local
make nebius-models
make nebius-probe
```

Current verified Token Factory endpoint:

```text
https://api.tokenfactory.nebius.com/v1
```

The current valid probe model is:

```text
Qwen/Qwen3-30B-A3B-Instruct-2507
```

If `.env` contains an older model name, `make nebius-probe` can fall back for
the probe, but update the configured model before routing application traffic.

## Task Distribution

Use Vapi credits for:

- inbound call testing;
- one final demo/verification call;
- optional outbound call only if `VAPI_TEST_NUMBER` is set and approved.

Detailed Vapi resource use is in `docs/VAPI_RESOURCE_STRATEGY.md`.

Use InsForge for:

- hosted webhook execution;
- deterministic protocol/SDS/hardware/sensor/shorthand tools;
- future versioned persistence only after review.

Use Nebius for:

- non-sensitive call summary drafts;
- model/tool-calling comparison;
- future RAG or agent experiments from the cookbook;
- not for emergency, SDS, or protocol authority.

Use Ollama for:

- local no-cost fallback;
- offline custom-LLM experiments;
- regression probes that should not spend API credits.
