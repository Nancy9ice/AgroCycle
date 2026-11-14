.PHONY: setup check lint test

setup:
	uv sync

# Schema checks, post-load assertions (added in Phase 2) and tests.
check: lint test

lint:
	uv run ruff check .

test:
	uv run pytest
