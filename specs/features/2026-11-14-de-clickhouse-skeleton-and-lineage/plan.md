# Plan: ClickHouse skeleton and lineage

- **Role:** de
- **Spec created:** 2026-11-14
- **Roadmap phase and task:** Phase 2, DE: ClickHouse skeleton + lineage

## Goal
Empty, correctly typed tables for provenance, plus the one load path and the checks every later DE load (Phases 3, 4, 6) reuses. Nothing is loaded yet except what the tests create and drop.

## Task groups

### 1. Claim and branch
1. Set the Phase 2 DE row to `In progress` in `specs/roadmap.md` (own row only).
2. Branch `feature/2026-11-14-de-clickhouse-skeleton-and-lineage` from `origin/main`. Done.

### 2. Schema as versioned SQL
1. `schema/001_core.sql`: `data_sources` (partition `source_id`), `indicator_lineage` (partition `code_version`), `fields` (one partition), each plain `MergeTree` with typed columns, `load_id`, and the evidence-type `Enum8`.
2. Runner `python -m common.migrate`: applies unapplied files in order, records them in `schema_migrations`, safe to rerun.
3. Column rules from tech-stack: `LowCardinality` for repeated strings, no `Nullable` unless the value is truly optional, `ORDER BY` on the natural key, coarse `PARTITION BY`.

### 3. Staging and REPLACE PARTITION loader
1. `common/load.py`: create `<table>__staging` with the same schema, batch insert, run the post-load assertions, then `ALTER TABLE ... REPLACE PARTITION ... FROM`, then drop staging.
2. A failed assertion stops before the swap and leaves the live table untouched.
3. Every load writes a `load_id` and returns a run record (git SHA, row count, input checksum) for the run manifest.

### 4. Pandera schemas and post-load assertions
1. `common/schemas.py`: one Pandera schema per table, with the evidence-type values as an allowed set.
2. `common/assertions.py`: row count equals the staged frame, no nulls in key columns, no duplicate keys, no indicator row without a matching `indicator_lineage` row.
3. Add `schema-check` to `make check` (offline, runs everywhere).

### 5. Tests and live checks
1. Offline `tests/`: SQL files parse and name every column the schemas expect, schemas accept valid and reject invalid frames (bad enum, null key), loader order of operations against a fake client.
2. Live `tests/live/`: skip unless ClickHouse variables are set and a database can be created. Work in a scratch database, load twice, compare table hashes, check partition isolation and assertions, drop the database.
3. Run `make check`; keep the live run's output.

### 6. Close
1. Fill the `validation.md` results.
2. Update the tracker row, with the interfaces below.
3. Run `/code-review` on the branch, then open the PR.

## Files, tables and endpoints
- New: `schema/001_core.sql`, `common/migrate.py`, `common/load.py`, `common/schemas.py`, `common/assertions.py`, tests.
- Changed: `Makefile` (`check`), `specs/roadmap.md` (own row).
- ClickHouse (database `agrocycle`): `data_sources`, `indicator_lineage`, `fields`, `schema_migrations`.

## Dependencies and interfaces
- **DS2:** `indicator_lineage` takes the 15 columns that `transform/indicators/runner.py` already writes, plus `load_id`. Any column change is announced to DS2.
- **BE:** table and column names are the contract for the API; stubs and mocks stay BE's. Announce once merged.
- **DS1, DS2, DE later:** Phases 3, 4 and 6 add their own tables as new numbered SQL files and call `common/load.py`.
- **ClickHouse access:** existing credentials in `.env`; nothing is provisioned.

## Data size
Metadata only (tens to hundreds of rows). No budget concern.

## Risks and open questions
- `REPLACE PARTITION` needs identical structure and partition key on staging and live tables; a loader test guards this.
- The hosted ClickHouse is shared. Live tests use a `scratch_<id>` database, dropped in a `finally`, and never touch the project tables.
- Whether the indicator tables (`field_indicators`, `soil_properties`) belong to Phase 2 or Phase 4 is settled as Phase 4, to avoid guessing their keys.
