PYTHON ?= $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python3; fi)

.PHONY: install dev test test-python test-node expose tunnel push wire wire-dry-run vapi-preflight vapi-verify-call vapi-wait-call vapi-tools public-probe hosted-probe hosted-demo smoke readiness live-demo-guard prefield-check shorthand-stress tts-stress matrix-stress demo-stress recording-preflight fetch-recording send-demo-links llm-probe nebius-probe nebius-models demo-call test-number-call test-number-call-live insforge-export

install:
	$(PYTHON) -m pip install -r requirements.txt

dev:
	bash scripts/dev.sh

test:
	$(PYTHON) -m pytest
	npm test

test-python:
	$(PYTHON) -m pytest

test-node:
	npm test

expose:
	bash scripts/expose.sh

tunnel:
	bash scripts/tunnel.sh

push:
	$(PYTHON) vapi/push.py

wire:
	$(PYTHON) vapi/wire.py create-assistant --assign-phone

wire-dry-run:
	@$(PYTHON) vapi/wire.py create-assistant --assign-phone --dry-run

vapi-preflight:
	@$(PYTHON) vapi/wire.py preflight

vapi-verify-call:
	@$(PYTHON) vapi/wire.py verify-call

vapi-wait-call:
	@$(PYTHON) vapi/wire.py wait-call

vapi-tools:
	@$(PYTHON) scripts/upsert_vapi_tools.py

public-probe:
	@$(PYTHON) scripts/public_probe.py

hosted-probe:
	@$(PYTHON) scripts/hosted_function_probe.py

hosted-demo:
	@$(PYTHON) scripts/hosted_demo.py

smoke:
	$(PYTHON) scripts/smoke.py

readiness:
	@$(PYTHON) scripts/readiness.py

live-demo-guard:
	@$(PYTHON) scripts/live_demo_guard.py

prefield-check:
	@$(PYTHON) scripts/prefield_check.py

shorthand-stress:
	@$(PYTHON) scripts/shorthand_stress.py

tts-stress:
	@$(PYTHON) scripts/tts_stress.py

matrix-stress: tts-stress

demo-stress:
	@$(PYTHON) scripts/demo_stress.py

recording-preflight:
	@$(PYTHON) scripts/recording_preflight.py --repair

fetch-recording:
	@$(PYTHON) scripts/fetch_recording.py

send-demo-links:
	@$(PYTHON) scripts/send_demo_links.py

llm-probe:
	@$(PYTHON) scripts/llm_probe.py

nebius-probe:
	@$(PYTHON) scripts/nebius_probe.py

nebius-models:
	@$(PYTHON) scripts/nebius_probe.py --list-models

demo-call:
	@$(PYTHON) scripts/demo_call.py

test-number-call:
	@$(PYTHON) scripts/test_number_call_phonebio.py --variation all

test-number-call-live:
	@$(PYTHON) scripts/test_number_call_phonebio.py --place-call --variation siri

insforge-export:
	@$(PYTHON) scripts/insforge_export.py

recording:
	$(PYTHON) scripts/fetch_recording.py

voice-stress:
	$(PYTHON) scripts/voice_stress.py

demo-matrix:
	$(PYTHON) scripts/demo_matrix.py
