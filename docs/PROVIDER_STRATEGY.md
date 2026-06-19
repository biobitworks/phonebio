# Provider Strategy

PhoneBio v1 uses each external service for the narrow job it is best suited
for, with cost and safety boundaries kept explicit.

## v1 Routing

| Provider | v1 role | Credit policy | Safety boundary |
|----------|---------|---------------|-----------------|
| Vapi | Phone agents: live phone number, voice session, assistant orchestration, call evidence. | Spend Vapi credits only on live demo calls and final verification. | Vapi can route tools but is not the source of protocol/SDS truth. |
| InsForge | Website, hosted Vapi webhook, deterministic local-record tool dispatch, and future persistence. | Use hosted website/functions as the main app/backend surface; redeploy only when needed. | Protocol, SDS, hardware, sensor, and shorthand answers stay source-backed. |
| Nebius Token Factory | GPU/model acceleration for non-critical summarization, multilingual extraction, tool-calling experiments, and evals. | Use the $100 Token Factory credit with `NEBIUS_API_KEY`; probe before routing real tasks. | Never make Nebius authoritative for SDS/protocol lookup in v1. |
| Local quantized models / Ollama | Phone/laptop/offline fallback for sensor labels and custom-LLM experiments. | Free local compute; use when local model quality and battery/latency are acceptable. | Optional acceleration only; deterministic `/webhook` tools remain source of truth. |

## Default Live Demo Path

```text
caller -> Vapi phone agent -> hosted InsForge website/functions -> deterministic records
                                -> optional Nebius GPU for non-safety model work
```

This path does not use OpenAI and does not require Nebius.

For hands-free/PPE/disaster use, Vapi remains the only required live user
interface. Apps and native sensors may provide optional background payloads, but
the caller must be able to complete the workflow by voice alone.

For degraded cell service, this means the worker's device may have voice only:
no mobile data, no app sync, and no web/API access. Vapi, InsForge, and Nebius
run server-side after the call reaches the assistant.

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

- phone agents;
- inbound call testing;
- one final demo/verification call;
- optional outbound call only if `VAPI_TEST_NUMBER` is set and approved.

Detailed Vapi resource use is in `docs/VAPI_RESOURCE_STRATEGY.md`.

Use InsForge for:

- website/app hosting;
- hosted webhook execution;
- deterministic protocol/SDS/hardware/sensor/shorthand tools;
- future hands-free disaster-triage receipts and compact derived records;
- server-side capture when field-device data service is unavailable;
- future versioned persistence only after review.

Use Nebius for:

- GPU acceleration;
- non-sensitive call summary drafts;
- model/tool-calling comparison;
- multilingual disaster-triage paraphrase and non-safety extraction experiments;
- fast GPU processing of sensor summaries, shorthand/phoneme candidates, and
  eval batches when the $100 Token Factory credit is available;
- future RAG or agent experiments from the cookbook;
- not for emergency, SDS, or protocol authority.

Use local quantized models / Ollama for:

- local no-cost fallback;
- offline custom-LLM experiments;
- phone/laptop-side voice activity, noise, gesture, pocket/activity, and
  lightweight multilingual keyword labels;
- regression probes that should not spend API credits.
