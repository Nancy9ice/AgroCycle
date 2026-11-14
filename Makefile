.PHONY: setup check lint test fields schema-check migrate web-setup web-check

setup:
	uv sync

# Lint, field-file validation, SQL-versus-schema check and tests. The tests include the live ClickHouse
# checks (idempotent loads, post-load assertions), which skip when ClickHouse settings are missing.
check: lint fields schema-check test

lint:
	uv run ruff check .

fields:
	uv run python -m transform.field_schema

test:
	uv run pytest

# SQL files and Pandera schemas must describe the same columns (no database needed).
schema-check:
	uv run python -m common.schema_check

# Apply any new schema/*.sql to the configured ClickHouse database (safe to rerun).
migrate:
	uv run python -m common.migrate

web-setup:
	cd web && npm install

# Lint, typecheck, format check and production build of the frontend.
web-check:
	cd web && npm run check
