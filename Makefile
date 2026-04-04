PYTHONPATH ?= src

.PHONY: check lint typecheck test compile

check: compile lint typecheck test

compile:
	python3 -m compileall -q src tests

lint:
	ruff check . --no-cache

typecheck:
	mypy src

test:
	PYTHONPATH=$(PYTHONPATH) pytest -q -p no:cacheprovider
