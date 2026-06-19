# PhoneBio — Strategy to v1 + credit distribution

_Updated 2026-06-19. Field-bio call-in agent: caller dials a Vapi number, gets
protocol / SDS / hardware / sensor help by voice, no camera, and no mobile data
requirement on the caller's side._

## 1. Credit distribution (put each workload on the right pool)

| Pool | Credit | Owns | Cost driver | Guardrail |
|------|--------|------|-------------|-----------|
| **Vapi** | hackathon free | Phone agents: inbound number, STT, TTS, turn-taking | **per call-minute** | Keep replies short (<35 words); **test off-phone**, not by calling |
| **InsForge** | hackathon free | Website/app hosting, DB/content/receipts, edge functions (tool webhook + brain proxy) | function invocations / hosting | The free workhorse — push website and deterministic logic here |
| **Nebius** | **$100 Token Factory credit** | GPU/model acceleration: reasoning, tool selection, evals, multilingual/shorthand experiments | **tokens** | Cheap MoE model, lean prompt/tools, cap `max_tokens`; dev on local Ollama |

**Principle:** Vapi owns phone agents. InsForge owns the website/backend and all
deterministic records. Nebius owns GPU/model acceleration. The scarce pool is
still model tokens, but the updated $100 Token Factory credit is enough for
broader tool-calling evals and multilingual/shorthand experiments if we keep
prompts lean and answers short.

**Cost-protection tactics**
- Develop/iterate against the InsForge functions + **local Ollama `qwen3:1.7b`** ($0), not live phone calls.
- Lean system prompt + tool schemas (resent every turn → Nebius tokens).
- `max_tokens` cap on the proxy; short voice answers.
- Fallback: if Nebius runs dry, the proxy can switch to local Ollama (offline) so the demo never hard-fails.

## 2. Vapi feature map (use as needed)

| Feature | Use? | When |
|---------|------|------|
| **Assistant** | ✅ now | Core — 1 assistant (PhoneBio Field Biology Worker) |
| **Tools** | ✅ now | Core — 5 function tools → InsForge webhook |
| **Phone numbers** | ✅ now | Inbound on phonebio line; test line as backup |
| **Evals / test suites** | ⏩ v1 hardening | Automated checks that the agent picks the right tool + gives safe answers. Run near demo (costs Vapi minutes). |
| **Files (Vapi KB)** | ⚪ optional | Only if we want unstructured-doc RAG (e.g., full SDS PDFs). Today retrieval is InsForge tools — more control. Defer. |
| **Squads** | ⚪ post-v1 | Multi-assistant routing/escalation (e.g., a safety-specialist member). One assistant + tools is enough for v1. |
| **Outbound** | ⚪ post-v1 | Callbacks / proactive safety alerts. Not needed for call-in v1; burns Vapi minutes. |

## 3. Strategy to v1

**v1 = one caller, one phone agent, correct grounded voice answers across the 5
tools, website/backend on InsForge, optional GPU acceleration on Nebius, no camera.**

- **Phase A — Build the spine. ✅ DONE.** Vapi assistant + InsForge DB/functions + Nebius brain. Both function paths verified (tool-calling via Nebius; tool execution reading the DB).
- **Phase B — Prove the live call. ← the v1 gate.** Place one real call to the assigned PhoneBio Vapi number. Watch `insforge logs function.logs` + Vapi call logs. Fix latency/format issues. This is the only unverified link.
- **Phase C — Harden for demo.** call_receipts logging (audit trail); tune the system prompt for voice brevity; confirm all 5 tools + the not-found/escalation safety messages over voice; set `max_tokens`.
- **Phase D — Demo-ready.** Judge runbook + the 3-pool story; local-Ollama fallback armed; test line as backup number; a few Vapi evals.

**Acceptance for v1:** a cold call asks "I spilled formaldehyde, what PPE?" and
hears the correct SDS-grounded answer; same for a protocol, a hardware fault,
and a sensor reading; an unknown request escalates ("stop, call your
supervisor") instead of hallucinating.

**Next action:** place the test call (Phase B). Then call_receipts + 2-3 evals.
