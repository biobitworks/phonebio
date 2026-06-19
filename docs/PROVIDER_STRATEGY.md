# Provider Strategy

PhoneBio v1 uses each external service for the narrow job it is best suited
for, with cost and safety boundaries kept explicit.

## v1 Routing

| Provider | v1 role | Credit policy | Safety boundary |
|----------|---------|---------------|-----------------|
| Vapi | Phone agents: live phone number, voice session, assistant orchestration, call evidence. | Spend Vapi credits only on live demo calls and final verification. | Vapi can route tools but is not the source of protocol/SDS truth. |
| InsForge | Website, hosted Vapi webhook, custom-LLM proxy, deterministic local-record tool dispatch, and future persistence. | Use hosted website/functions as the main app/backend surface; redeploy only when needed. | Protocol, SDS, hardware, sensor, and shorthand answers stay source-backed. |
| Nebius Token Factory | Live GPU reasoning lane plus later summarization, multilingual extraction, tool-calling experiments, and evals. | Use the $100 Token Factory credit with `NEBIUS_API_KEY`; probe before routing real tasks. | Never make Nebius authoritative for SDS/protocol lookup in v1. |
| Local quantized models / Ollama | Phone/laptop/offline fallback for sensor labels and custom-LLM experiments. | Free local compute; use when local model quality and battery/latency are acceptable. | Optional acceleration only; deterministic `/webhook` tools remain source of truth. |

## Default Live Demo Path

```text
caller -> Vapi phone agent -> hosted InsForge website/functions -> deterministic records
                                -> InsForge custom-LLM proxy -> Nebius 70B reasoning
```

This path does not use OpenAI. For the live voice reasoning demo, Nebius is the
primary model path when `NEBIUS_API_KEY` is present. Deterministic InsForge
tools remain the authority for SDS/protocol facts.

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

The current live demo model is:

```text
meta-llama/Llama-3.3-70B-Instruct
```

If `.env` contains an older model name, `make nebius-probe` can fall back for
the probe, but update the hosted `NEBIUS_MODEL` before routing application
traffic.

## Fallback Policy

Do not bypass Nebius unconditionally. The `phonebio-llm` proxy should try the
real Nebius/OpenAI-compatible chat-completions request first. A deterministic
answer may be returned only when the Nebius key is absent, the upstream request
fails, or the network times out, and the response model must be labeled:

```text
phonebio-deterministic-fallback
```

This keeps the Nebius and InsForge story inspectable: GPU reasoning is real when
available, and safety facts still come from deterministic tool records.

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
- live call reasoning through the hosted InsForge custom-LLM proxy;
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
