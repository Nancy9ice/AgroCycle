# Requirements: ClickHouse skeleton and lineage

## Covers
- **PRD requirements:** NFR-01 (reproducibility: idempotent loads), provenance and lineage (PRD §6.1), evidence-type labels (§6.2).
- **Roadmap exit check satisfied (DE part):** "tables exist; `make check` runs". The API mock profile is BE's; FE unblocking depends on it.

## Scope decisions (2026-11-14)
- In: core tables, staging + `REPLACE PARTITION` loader, Pandera module, post-load assertions, `make check` wiring.
- Out: seeding any table (fields, manifests, lineage rows); indicator tables (Phase 4); crop-history tables (Phase 3); FastAPI stub (BE).
- `indicator_lineage` adopts DS2's 15 columns as its contract.
- DDL is versioned, numbered SQL files applied by a rerunnable script.
- Validation is offline tests plus live checks that skip without credentials.

## Inputs
- ClickHouse connection from `common/config.py` (`agrocycle` database).
- DS2's lineage row shape, `transform/indicators/runner.py::lineage_rows`.
- Field properties from `data/fields/fields.geojson`, manifest fields from `ingest/manifest.py`.

## Outputs

| Table | Key / order by | Partition by | Purpose |
|---|---|---|---|
| `data_sources` | `source_id, version, retrieval_date, s3_key` | `source_id` | One row per raw file, from its Phase 1 manifest: URL, version, retrieval date, SHA-256, size, licence, S3 key, `load_id` |
| `indicator_lineage` | `indicator_id, code_version` | `code_version` | DS2's 15 columns + `load_id`; `evidence_type` is the Enum; `source_ids`, `variables` stay JSON strings |
| `fields` | `field_id` | none (small) | `field_id`, `role`, `boundary_source`, `county`, provenance, geometry as WKT, `load_id` |
| `schema_migrations` | `version` | none | Applied SQL file names and time |

- **A partition is the unit a reload replaces.** `REPLACE PARTITION` swaps whole partitions, so a frame must hold every row of each partition it touches: all files of one source, all rows of one `code_version`, all fields. Other partitions are left alone. (Year partitioning was dropped: reloading CDL would have wiped POWER.)
- Evidence-type `Enum8`: observed, derived, classified, survey, model_reanalysis, experimental, published, assumption.
- Every table has `load_id String` linking to the run manifest.
- Exact column types are fixed in `schema/001_core.sql` and mirrored in `common/schemas.py`.

## Acceptance criteria
1. `python -m common.migrate` creates all four tables on an empty database and does nothing on a second run.
2. A frame with an evidence type outside the Enum, or a null key column, is rejected by the Pandera schema before any insert.
3. The loader inserts into a staging table and swaps with `REPLACE PARTITION`; loading the same frame twice leaves identical table hashes and no duplicate keys.
4. A failing assertion aborts the load before the swap and leaves the live table unchanged.
5. The assertions flag a deliberately inserted indicator row with no lineage row.
6. `make check` runs the schema checks offline and passes without ClickHouse credentials.
7. Live tests run only with credentials, in a throwaway scratch database that is dropped afterwards, and leave nothing behind.
8. Reloading one source's `data_sources` rows leaves every other source's rows unchanged.

## Evidence labels, scale and limitations to preserve
- Lineage rows keep DS2's `evidence_type`, `scale` and `limitation` verbatim; the loader never fills a missing one with a default.
- `fields.boundary_source` stays `demo` or `real`; geometry is demonstration geometry, not farm boundaries.
- Limits: these are empty containers. A passing check proves structure and idempotency, not that any data is correct.

## Out of scope
Seeding or loading data, indicator and crop-history tables, API stubs, materialized views, `AggregatingMergeTree`, deployment, and ClickHouse provisioning.
