# Vapi Runbook

**Goal:** Create the PhoneBio assistant, attach the webhook, assign the existing Vapi phone number, and make a test call without committing secrets or phone numbers.

## Prerequisites

- Vapi private/API key in the shell as `VAPI_API_KEY` or `VAPI_PRIVATE_KEY`.
- Existing Vapi phone number ID in `VAPI_PHONE_NUMBER_ID`.
- Public webhook URL in `VAPI_WEBHOOK_URL` or `PUBLIC_BASE_URL`.
- Optional outbound test destination in `VAPI_TEST_NUMBER`.

## Local Webhook

```bash
make dev
make expose
```

`make expose` uses the Vapi CLI forwarding path:

```bash
vapi listen --forward-to localhost:8080/webhook
```

Use the forwarded URL as `VAPI_WEBHOOK_URL`.

## Dry Run

```bash
make wire-dry-run
```

This prints:

- assistant payload with `assistant.server.url`
- phone-number assignment payload with `assistantId`
- redacted readiness booleans

## Live Create and Assign

```bash
export VAPI_API_KEY
export VAPI_PHONE_NUMBER_ID
export VAPI_WEBHOOK_URL="https://your-forwarded-url/webhook"

make wire
```

This calls:

- `POST https://api.vapi.ai/assistant`
- `PATCH https://api.vapi.ai/phone-number/:id`

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
