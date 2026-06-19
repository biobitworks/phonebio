.PHONY: install dev test test-python test-node expose tunnel push wire wire-dry-run vapi-preflight vapi-verify-call vapi-wait-call public-probe hosted-probe hosted-demo smoke readiness prefield-check shorthand-stress tts-stress matrix-stress demo-stress recording-preflight fetch-recording send-demo-links llm-probe nebius-probe nebius-models demo-call insforge-export

install:
	python3 -m pip install -r requirements.txt

dev:
	bash scripts/dev.sh

test:
	python3 -m pytest
	npm test

test-python:
	python3 -m pytest

test-node:
	npm test

expose:
	bash scripts/expose.sh

tunnel:
	bash scripts/tunnel.sh

push:
	python3 vapi/push.py

wire:
	python3 vapi/wire.py create-assistant --assign-phone

wire-dry-run:
	@python3 vapi/wire.py create-assistant --assign-phone --dry-run

vapi-preflight:
	@python3 vapi/wire.py preflight

vapi-verify-call:
	@python3 vapi/wire.py verify-call

vapi-wait-call:
	@python3 vapi/wire.py wait-call

public-probe:
	@python3 scripts/public_probe.py

hosted-probe:
	@python3 scripts/hosted_function_probe.py

hosted-demo:
	@python3 scripts/hosted_demo.py

smoke:
	python3 scripts/smoke.py

readiness:
	@python3 scripts/readiness.py

prefield-check:
	@python3 scripts/prefield_check.py

shorthand-stress:
	@python3 scripts/shorthand_stress.py

tts-stress:
	@python3 scripts/tts_stress.py

matrix-stress: tts-stress

demo-stress:
	@python3 scripts/demo_stress.py

recording-preflight:
	@python3 scripts/recording_preflight.py --repair

fetch-recording:
	@python3 scripts/fetch_recording.py

send-demo-links:
	@python3 scripts/send_demo_links.py

llm-probe:
	@python3 scripts/llm_probe.py

nebius-probe:
	@python3 scripts/nebius_probe.py

nebius-models:
	@python3 scripts/nebius_probe.py --list-models

demo-call:
	@python3 scripts/demo_call.py

insforge-export:
	@python3 scripts/insforge_export.py

recording:
	python3 scripts/fetch_recording.py

voice-stress:
	python3 scripts/voice_stress.py

demo-matrix:
	python3 scripts/demo_matrix.py
