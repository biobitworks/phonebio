# PhoneBio State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-06-19)

**Core value:** A field worker can call in and get the next safe, protocol-grounded action from local knowledge when the network is unreliable and the camera is unavailable.
**Current focus:** Phase 2 - Vapi Phone Number Wiring and Public Repo

## Current Status

- GSD initialization artifacts created locally.
- v1 implementation scaffold targets Vapi custom tools over HTTP.
- Public GitHub repo is live at `https://github.com/biobitworks/phonebio`.
- Vapi dry-run wiring exists in `vapi/wire.py`; live Vapi creation/phone assignment is pending `VAPI_API_KEY` or `VAPI_PRIVATE_KEY`, `VAPI_PHONE_NUMBER_ID`, and a public webhook URL.
- Ollarma is reachable at `127.0.0.1:8484` but degraded with `SELECTION_STALE`; Watchtower bridge aggregator at `127.0.0.1:8002` is unreachable.

## Next Step

Set Vapi credentials and public webhook URL, then run `make wire` or assign the assistant in the dashboard.
