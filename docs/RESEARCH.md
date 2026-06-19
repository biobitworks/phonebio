# PhoneBio Research Notes

**Date:** 2026-06-19

## Sources Checked

- Vapi quickstart introduction: `https://docs.vapi.ai/quickstart/introduction`
- Vapi phone quickstart: `https://docs.vapi.ai/quickstart/phone`
- Vapi custom tools: `https://docs.vapi.ai/tools/custom-tools`
- Vapi server URLs: `https://docs.vapi.ai/server-url`
- Vapi custom LLM provider shape: `https://docs.vapi.ai/customization/custom-llm/fine-tuned-openai-models`
- Gregg shorthand index: `https://greggshorthand.github.io/anindex.html`
- Nebius Token Factory cookbook: `https://github.com/nebius/token-factory-cookbook`
- Nebius Token Factory API intro: `https://docs.tokenfactory.nebius.com/api-reference/introduction`
- InsForge repository: `https://github.com/InsForge/InsForge`
- Apple Core Motion docs: `https://developer.apple.com/documentation/coremotion/`
- Apple Nearby Interaction docs: `https://developer.apple.com/documentation/nearbyinteraction`
- Apple ARKit scene depth docs: `https://developer.apple.com/documentation/arkit/arconfiguration/framesemantics-swift.struct/scenedepth`

## Design Implications

- Vapi can be tested quickly through dashboard-created assistants and phone numbers. Custom tools require a reachable server URL and return `results` keyed by tool-call ID.
- Server URLs are the right bridge for call transcripts, function calls, assistant requests, and end-of-call reports.
- Gregg shorthand suggests a voice UX pattern: capture compact phonetic/semantic observations, then ask clarifying questions only when omitted detail changes safety or protocol selection.
- Nebius was reviewed but is not part of the current funded/API path.
- Nebius Token Factory cookbook setup is now represented as an optional path:
  `NEBIUS_API_KEY` in `.env`, OpenAI-compatible chat-completions base URL, and
  `make nebius-probe` after free credits/API access are active.
- Provider/credit strategy is captured in `docs/PROVIDER_STRATEGY.md`: Vapi
  for phone/call evidence, InsForge for deterministic tools, Nebius for
  optional non-safety model capacity, and Ollama for local no-cost fallback.
- InsForge is the candidate backend if persistent auth, database, storage, functions, hosting, or model-gateway features are needed.
- Phone sensor access is platform-specific. Core Motion covers accelerometer, gyroscope, magnetometer, pedometer, and barometer when available. Nearby Interaction covers UWB distance/direction on supported devices. ARKit scene depth is LiDAR-device-gated and should be treated as unavailable unless the device reports support.
