.PHONY: install dev test test-python test-node expose push wire wire-dry-run smoke readiness llm-probe demo-call insforge-export

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

push:
	python3 vapi/push.py

wire:
	python3 vapi/wire.py create-assistant --assign-phone

wire-dry-run:
	@python3 vapi/wire.py create-assistant --assign-phone --dry-run

smoke:
	python3 scripts/smoke.py

readiness:
	@python3 scripts/readiness.py

llm-probe:
	@python3 scripts/llm_probe.py

demo-call:
	@python3 scripts/demo_call.py

insforge-export:
	@python3 scripts/insforge_export.py
