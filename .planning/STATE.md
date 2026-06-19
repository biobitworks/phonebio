# PhoneBio State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-06-19)

**Core value:** A field worker can call in and get the next safe, protocol-grounded action from local knowledge when the network is unreliable and the camera is unavailable.
**Current focus:** Phase 2 - Vapi Phone Number Wiring and Public Repo

## Current Status

- GSD initialization artifacts created locally.
- v1 implementation scaffold targets Vapi custom tools over HTTP.
- Public GitHub repo is live at `https://github.com/biobitworks/phonebio`.
- Vapi dry-run and live wiring exist in `vapi/wire.py`; the PhoneBio assistant was created through the Vapi API and the selected phone number assignment was verified by `make vapi-preflight` with the returned assistant ID. The checked-in assistant points at the hosted InsForge webhook.
- Ollarma is reachable at `127.0.0.1:8484` but degraded with `SELECTION_STALE`; Watchtower bridge aggregator at `127.0.0.1:8002` is unreachable.

## Next Step

Verify a real inbound call to the assigned Vapi phone number with `make vapi-verify-call`, or set `VAPI_TEST_NUMBER` and run `python3 vapi/wire.py outbound-call --dry-run` followed by the live outbound test if approved.
