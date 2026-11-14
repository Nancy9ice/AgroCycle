# Plan: Repo, infra and field GeoJSON setup

- **Role:** de
- **Spec created:** 2026-11-14
- **Roadmap phase and task:** Phase 0, DE: repo layout, env handling, S3 and ClickHouse access, field GeoJSON

## Goal
Give the team a runnable repo with working S3 and ClickHouse access, and a validated GeoJSON of the demo fields, so Phase 1 extraction and Phase 2 tables can start.

## Approach
- Use the existing S3 bucket and the ClickHouse credentials already issued. Create neither; document access only.
- Credentials live in a local env file that is never committed. `.env.example` lists variable names only.
- DE draws the demo fields (one primary, at least 30 test), defines the schema, validates them and commits the file.
- Draw as parcel-sized polygons (roughly field-sized, not county-sized) in Story and Boone, spread across soil types, with some out-of-domain fields.

## Files, tables and endpoints
- Folders (each with a `README.md` or `.gitkeep`): `ingest/`, `transform/`, `api/`, `engine/`, `web/`, `docs/`, `tests/`
- `pyproject.toml` (Python 3.11+, `uv`), `uv.lock`, `.env.example`, `Makefile` (`make check` stub)
- `common/config.py`: loads the env file, builds the S3 and ClickHouse clients
- `scripts/smoke_s3.py`, `scripts/smoke_clickhouse.py`
- `data/fields/fields.geojson`, `transform/field_schema.py` (Pandera + shapely checks), `tests/test_fields.py`
- County boundary reference (Story, Boone) for the within-county check, cached under `data/reference/`

## Steps (in order)
1. Set the tracker row to `In progress` (DE).
2. Create the folder layout, `pyproject.toml`, `.env.example` and `Makefile`; confirm `.gitignore` excludes the env file and data.
3. Write `common/config.py` and the two smoke scripts; run them against the real S3 bucket and ClickHouse.
4. Define the field schema; write the field validator and its tests.
5. Draw the polygons, validate them, and commit `fields.geojson`.
6. Wire `make check` to run the schema checks and `pytest`.
7. Record results in `validation.md`; update the tracker.

## Dependencies and interfaces with other roles
- **DS1:** checks the primary field's CDL maize–soybean history and reviews the out-of-domain picks.
- **BE, FE:** need `fields.geojson` and the `field_id` convention. BE needs the ClickHouse variable names.
- **Phase 2 (DE):** reuses `common/config.py` and `make check`.

## Data size and subsets
Tiny: one GeoJSON of ~31–51 polygons (1 primary, ≥30 test), plus the two county polygons.

## Risks and open questions
- Bucket name, region and ClickHouse host/port/TLS are not in the repo; DE supplies them locally.
- Drawing ~31 polygons by hand is the slowest step; ship the schema and validator first so others can start on them.
- The CDL history of the primary field is only confirmed once DS1 checks it; pick a candidate first.
- ClickHouse may be a hosted service; confirm that creating a scratch table is allowed before the smoke test.
