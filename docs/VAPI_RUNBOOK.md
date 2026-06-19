# Vapi Runbook

**Goal:** Create the PhoneBio assistant, attach the webhook, assign the existing Vapi phone number, and make a test call without committing secrets or phone numbers.

See `docs/VAPI_RESOURCE_STRATEGY.md` for how PhoneBio uses Vapi Assistants,
Tools, Phone Numbers, Logs, Outbound, Files, Evals, and Squads across v1 and
later phases.

## Prerequisites

- Vapi private/API key in the shell as `VAPI_PRIVATE_KEY` or `VAPI_API_KEY`. Prefer `VAPI_PRIVATE_KEY`; if both are set, PhoneBio uses `VAPI_PRIVATE_KEY`.
- Existing Vapi phone number ID in `VAPI_PHONE_NUMBER_ID`.
- Public webhook URL in `VAPI_WEBHOOK_URL` or `PUBLIC_BASE_URL` when using a local tunnel or alternate deployment. The checked-in assistant already uses the hosted InsForge webhook.
- Public custom-LLM base URL in `VAPI_CUSTOM_LLM_URL` only when switching the assistant model provider to `custom-llm`. The current live path uses Vapi's `google` provider, so this is not required.
- Optional outbound test destination in `VAPI_TEST_NUMBER`.
- Optional bearer secret in `VAPI_WEBHOOK_SECRET` for both `/webhook` and `/custom-llm/chat/completions`.

## Credential Timing

The hosted InsForge webhook already exists, so the next required API bundle is Vapi only: a valid Vapi API/private key and the phone number ID or dashboard access to assign the assistant. If you replace the hosted webhook with a tunnel, also set `VAPI_WEBHOOK_URL`.

InsForge is already hosting the webhook. InsForge credentials are needed only
to redeploy the function or add persistence. OpenAI is not used. Nebius is
configured as an optional Token Factory provider and remains disabled until
`NEBIUS_API_KEY` plus approved free credits/API access are available.

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
make hosted-probe
```

This prints:

- assistant payload with `assistant.server.url`
- phone-number assignment payload with `assistantId`
- redacted readiness booleans

`make hosted-probe` sends a Vapi-style tool-call payload to the assistant server URL and verifies the hosted function returns object tool results, not stringified JSON.

Placeholder URLs such as `your-tunnel-or-deploy.example.com` are treated as not ready.

## Redacted Vapi Auth and Phone Check

```bash
make vapi-preflight
python3 vapi/wire.py list-phone-numbers
```

This makes read-only Vapi checks and prints readiness state, URL host/path, count, IDs, provider, and assignment presence without raw phone numbers or API keys. A `401 Unauthorized` means the local Vapi key is missing, expired, or not the correct private/API key.

The preflight output includes redacted key diagnostics:

- `apiKey.source` — which environment variable was used.
- `apiKey.shadowedSources` — set key variables ignored because a higher-priority source was present.
- `apiKey.startsWithSk` / `apiKey.looksLikeJwt` — shape hints only; the key value is never printed.

`make vapi-preflight` exits nonzero until all live prerequisites are true: valid Vapi auth, usable phone-number selection, non-placeholder webhook URL, and, only for `custom-llm` assistants, a non-placeholder custom-LLM URL.

For v1, PhoneBio uses six inline function declarations on the assistant, not
separate reusable Vapi Tool records: `get_protocol`, `get_safety_sheet`,
`troubleshoot_hardware`, `interpret_sensor_report`, `compress_observation`, and
`assess_environment_risk`. `make demo-stress` checks the live assistant for that
tool surface.

## Live Create and Assign

```bash
export VAPI_API_KEY
export VAPI_PHONE_NUMBER_ID
# Optional when using the checked-in hosted InsForge webhook:
# export VAPI_WEBHOOK_URL="https://your-forwarded-url/webhook"
# Required only if model.provider is changed to custom-llm:
# export VAPI_CUSTOM_LLM_URL="https://your-forwarded-url/custom-llm"

make wire
```

After a successful live run, copy the returned assistant ID into the current shell
for verification:

```bash
export VAPI_ASSISTANT_ID="returned-assistant-id"
make vapi-preflight
```

`phoneSelection.expectedAssistantMatch: true` proves the selected Vapi phone
number is attached to that assistant.

If `expectedAssistantMatch` is `false` but `selectedAssistantId` shows the
newly returned assistant ID, the local `VAPI_ASSISTANT_ID` value is stale. The
phone assignment can still be valid; update the shell value or rely on
`make vapi-verify-call`, which defaults to the assistant currently attached to
the selected phone number.

## Real Call Verification

After calling the assigned Vapi phone number, verify that Vapi has a recent
call for the selected assistant and phone-number pair:

```bash
export VAPI_ASSISTANT_ID="returned-assistant-id"
make vapi-verify-call
export PHONEBIO_CALL_VERIFIED=1
make readiness
```

For live demo testing, start the polling verifier first, then place the inbound
call while it is running:

```bash
make vapi-wait-call
```

The default wait is 180 seconds with a 5 second polling interval. For a shorter
manual check:

```bash
python3 vapi/wire.py wait-call --timeout 30 --interval 3
```

If Vapi has a transient read timeout while polling, the command keeps waiting
and reports only the error type/count in the final redacted output.

This calls `GET https://api.vapi.ai/call` and prints redacted call records only:
call IDs, status/timestamps, assistant ID, phone-number ID, and booleans for
whether transcript/recording/analysis artifacts exist. It does not print raw
phone numbers, transcripts, recordings, or summaries.

For video production, treat `recordingPresent: true` as proof that Vapi has call
audio. Download/export the raw audio from Vapi only after the take and keep it
out of git; the local helper intentionally does not print recording URLs.

Only set `PHONEBIO_CALL_VERIFIED=1` after `make vapi-verify-call` exits
successfully for the intended assistant/phone pair.

For inspection without enforcing a match:

```bash
python3 vapi/wire.py list-calls --limit 10
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
make hosted-demo
make tts-stress
```

Public dashboard for the video:

```text
https://qfdp5nuv.insforge.site/dashboard.html
```

Use handset or earbud microphone for the primary proof. Speakerphone on stage is
useful only as a noisy-condition demonstration because it can feed room audio and
assistant speech back into the call. See `docs/STAGE_TEST_CALL_GUIDE.md`.

1. Call the Vapi phone number hands-free.
2. Say: "I am in PPE and cannot touch the phone. I am collecting a surface water grab sample and the bottle has an air bubble. What do I do?"
3. Confirm the assistant calls `get_protocol`.
4. Say: "I spilled formaldehyde on a glove."
5. Confirm the assistant calls `get_safety_sheet` and escalates safety uncertainty.
6. Say: "The centrifuge is vibrating after balancing."
7. Confirm the assistant calls `troubleshoot_hardware`.
8. Say: "My barometer dropped 4 hPa in two hours."
9. Confirm the assistant calls `interpret_sensor_report` and explains confidence.
10. Say: "Disaster triage note. Loud machinery, possible fuel smell, two workers nearby, GPS accuracy 8 meters."
11. Confirm the assistant asks one spoken follow-up and does not request app taps, photos, or screen interaction.
12. Say: "Mobile data is down. I can only keep this call open."
13. Confirm the assistant continues by voice, captures location/hazard/action fields, and does not ask for app sync or upload.

## Nearby People / Devices Test Script

Use this when ready to test the “ask me, do not infer” behavior:

1. Call the assigned Vapi phone number.
2. Say: "Stage demo mode. I am in PPE, data is down, the phone is in my pocket. I hear radio chatter and loud machinery, and there may be another worker nearby."
3. Expected assistant behavior: it asks one direct confirmation question before assuming the context, such as: "Are you alone, with another worker, near a radio, or near powered equipment?"
4. Reply: "One other worker is nearby, and the centrifuge is running."
5. Expected assistant behavior: it can now use that confirmed context and keep the boundary clear: possible overlap or equipment nearby, not identity or exact headcount from sensors alone.

## Stage Speakerphone / Processing Lane Test

Use this when the demo room audio is bleeding into the call:

1. Open `https://qfdp5nuv.insforge.site/dashboard.html`.
2. Place the Vapi call from your real phone.
3. Say: "Stage demo mode. I am not close to the microphone, and the room is noisy."
4. Click `Stage speaker` on the dashboard.
5. Expected dashboard behavior: `risk: medium`, `lane: noisy_confirmation`.
6. Expected assistant behavior: it asks for confirmation instead of assuming who
   is speaking or what device is nearby.
7. Click `Biohazard`.
8. Expected dashboard behavior: `risk: high`, `lane: emergency_priority`.

## Safety Boundary

The assistant gives local protocol and safety-summary guidance. It does not replace the manufacturer's current SDS, site safety officer, poison control, emergency services, or field supervisor.
