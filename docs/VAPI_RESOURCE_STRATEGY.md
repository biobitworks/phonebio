# Vapi Resource Strategy

PhoneBio v1 should use Vapi resources deliberately. Keep the live path small
enough to debug during the hackathon, and only add heavier Vapi surfaces when
they prove a specific requirement.

## Use Now

| Vapi surface | PhoneBio use | Status |
|--------------|--------------|--------|
| Assistants | The `PhoneBio Field Biology Worker` assistant owns the system prompt, model provider, tool declarations, and hosted InsForge server URL. | Active |
| Phone Numbers | The `phonebio` number routes inbound calls to the PhoneBio assistant. | Active |
| Tools | Five core Vapi function declarations call the hosted InsForge webhook for deterministic protocol, SDS, hardware, sensor, and shorthand/field-note context tools. | Active |
| Logs | Use after each call to inspect failures, latency, and tool-call behavior without committing transcripts. | Active operational surface |

## Use For Verification

| Vapi surface | PhoneBio use | Rule |
|--------------|--------------|------|
| Outbound calls | Optional verification if `VAPI_TEST_NUMBER` is set and approved. | Do not place outbound calls without explicit destination/approval. |
| Evals | Post-demo regression suite for the demo matrix turns. | Add after the first real call succeeds. |
| Metrics / Monitoring | Check call latency, errors, and credit burn. | Use during demo rehearsal and after changes. |

## Defer Unless Needed

| Vapi surface | Why deferred |
|--------------|--------------|
| Squads | v1 has one field-biology worker role. Add squads only if we split into safety officer, hardware tech, and protocol specialist agents. |
| Files | v1 source truth lives in repo content and InsForge-hosted function data. Use Vapi files only if Vapi retrieval materially improves voice latency or demo setup. |
| Structured Outputs | Useful for post-call receipts, but current deterministic tool JSON and JSONL sidecars already cover v1 evidence. |
| Boards | Operational dashboard convenience, not required for v1 correctness. |

## v1 Call Path

```text
Vapi Phone Number -> Vapi Assistant -> Vapi Tool Call -> InsForge Webhook -> deterministic PhoneBio records
```

## Credit Discipline

- Spend Vapi credits on inbound call verification and final demo calls.
- Use hosted InsForge probes for tool behavior before spending Vapi call credits.
- Use `make hosted-demo` before any real call.
- Use Nebius only for optional non-safety model experiments; do not route
  deterministic SDS/protocol answers through Nebius; Nebius selects tool calls,
  while InsForge remains the source-backed tool authority.

## Next Vapi Actions

1. Run `make hosted-demo`.
2. Start `make vapi-wait-call`.
3. Place an inbound call to the assigned phonebio number.
4. If the wait succeeds, set `PHONEBIO_CALL_VERIFIED=1`.
5. Run `make readiness`.
6. After the first successful call, add Vapi Evals for the demo matrix turns.
