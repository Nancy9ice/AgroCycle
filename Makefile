.PHONY: setup check lint test fields web-setup web-check

setup:
	uv sync

# Lint, field-file validation and tests. Post-load assertions are added in Phase 2.
check: lint fields test

lint:
	uv run ruff check .

fields:
	uv run python -m transform.field_schema

test:
	uv run pytest

web-setup:
	cd web && npm install

# Lint, typecheck, format check and production build of the frontend.
web-check:
	cd web && npm run check
