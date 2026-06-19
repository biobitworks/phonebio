# Vapi Runbook

**Goal:** Create the PhoneBio assistant, attach the webhook, assign the existing Vapi phone number, and make a test call without committing secrets or phone numbers.

## Prerequisites

- Vapi private/API key in the shell as `VAPI_API_KEY` or `VAPI_PRIVATE_KEY`.
- Existing Vapi phone number ID in `VAPI_PHONE_NUMBER_ID`.
- Public webhook URL in `VAPI_WEBHOOK_URL` or `PUBLIC_BASE_URL`.
- Public custom-LLM base URL in `VAPI_CUSTOM_LLM_URL`, or derive it from `PUBLIC_BASE_URL` as `/custom-llm`.
- Optional outbound test destination in `VAPI_TEST_NUMBER`.
- Optional bearer secret in `VAPI_WEBHOOK_SECRET` for both `/webhook` and `/custom-llm/chat/completions`.

## Credential Timing

The Vapi API bundle is needed only after a public webhook URL exists. At that point, provide the Vapi API key, phone number ID, webhook URL, custom-LLM URL, and optional webhook secret.

InsForge is not needed until persistent hosted storage is selected. OpenAI is not used. Nebius is not part of the current funded/API path.

## Local Webhook

```bash
make dev
make tunnel
```

Use the public HTTPS base URL for:

```bash
export PUBLIC_BASE_URL="https://your-public-url"
export VAPI_WEBHOOK_URL="${PUBLIC_BASE_URL}/webhook"
export VAPI_CUSTOM_LLM_URL="${PUBLIC_BASE_URL}/custom-llm"
make public-probe
```

`make expose` remains available for Vapi CLI webhook-forwarder debugging:

```bash
vapi listen --forward-to localhost:8080/webhook
```

Vapi's current CLI docs describe `vapi listen` as a local forwarder only, not a public tunnel. For the PhoneBio custom-LLM path, use `make tunnel` or a hosted deployment that exposes the full app.

`make tunnel` tries `ngrok`, `cloudflared`, `lt`, then `npx --yes localtunnel` so a hackathon laptop with npm can still create a no-cost public URL without a global tunnel install.

## Dry Run

```bash
make wire-dry-run
```

This prints:

- assistant payload with `assistant.server.url`
- phone-number assignment payload with `assistantId`
- redacted readiness booleans

Placeholder URLs such as `your-tunnel-or-deploy.example.com` are treated as not ready.

## Redacted Vapi Auth and Phone Check

```bash
make vapi-preflight
python3 vapi/wire.py list-phone-numbers
```

This makes read-only Vapi checks and prints readiness state, URL host/path, count, IDs, provider, and assignment presence without raw phone numbers or API keys. A `401 Unauthorized` means the local Vapi key is missing, expired, or not the correct private/API key.

`make vapi-preflight` exits nonzero until all live prerequisites are true: valid Vapi auth, usable phone-number selection, non-placeholder webhook URL, and non-placeholder custom-LLM URL.

## Live Create and Assign

```bash
export VAPI_API_KEY
export VAPI_PHONE_NUMBER_ID
export VAPI_WEBHOOK_URL="https://your-forwarded-url/webhook"
export VAPI_CUSTOM_LLM_URL="https://your-forwarded-url/custom-llm"

make wire
```

This calls:

- `POST https://api.vapi.ai/assistant`
- `PATCH https://api.vapi.ai/phone-number/:id`

If `VAPI_PHONE_NUMBER_ID` is absent and exactly one Vapi phone number exists, the CLI can auto-discover that ID. If multiple numbers exist, set `VAPI_PHONE_NUMBER_ID` explicitly.

If an assistant already exists:

```bash
export VAPI_ASSISTANT_ID="..."
python3 vapi/wire.py assign-phone
```

## Optional Outbound Test

```bash
export VAPI_TEST_NUMBER="+1..."
python3 vapi/wire.py outbound-call --dry-run
python3 vapi/wire.py outbound-call
```

The outbound payload uses `assistantId`, `phoneNumberId`, and `customer.number`.

## Call Script for Hackathon Demo

Local rehearsal:

```bash
make demo-call
```

1. Call the Vapi phone number.
2. Say: "I am collecting a surface water grab sample and the bottle has an air bubble. What do I do?"
3. Confirm the assistant calls `get_protocol`.
4. Say: "I spilled formaldehyde on a glove."
5. Confirm the assistant calls `get_safety_sheet` and escalates safety uncertainty.
6. Say: "The centrifuge is vibrating after balancing."
7. Confirm the assistant calls `troubleshoot_hardware`.
8. Say: "My barometer dropped 4 hPa in two hours."
9. Confirm the assistant calls `interpret_sensor_report` and explains confidence.

## Safety Boundary

The assistant gives local protocol and safety-summary guidance. It does not replace the manufacturer's current SDS, site safety officer, poison control, emergency services, or field supervisor.
