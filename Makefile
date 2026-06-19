.PHONY: install dev test test-python test-node expose push smoke

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

smoke:
	python3 scripts/smoke.py
