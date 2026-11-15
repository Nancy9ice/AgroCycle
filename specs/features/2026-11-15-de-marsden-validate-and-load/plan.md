# Plan: Validate and load the Marsden records

- **Role:** de
- **Spec created:** 2026-11-15
- **Roadmap phase and task:** Phase 6, DE: validate the Marsden supplementary records with Pandera and load them into ClickHouse

## Goal
Get DS2's reproduction of the Marsden management comparisons into ClickHouse, checked, with a lineage row behind every value and the one gap with the paper left visible. The reproduction and its numbers stay DS2's.

## Approach
- DS2's script is unchanged. The DE reruns it from the five raw files (verified against the checksums in S3), validates its outputs with her Pandera schemas and its own checks, then loads.
- **One long table** (decision 2026-11-15): her wide CSVs (27 rotation-years, 3 summary rows) become `marsden_management`, one row per rotation, period and metric (120 rows), each with its `indicator_id`, so the loader's lineage check works as it does for Phase 4.
- **Her 4 lineage rows** load into `indicator_lineage` as their own partition, mapped to its 15 columns by the convention her own runner uses for POWER (decision 2026-11-15). DS2's 21 rows are untouched.
- **The reconciliation record** (20 checks) loads as `marsden_reconciliation`, so the UNRECONCILED check stays visible in the app and is never "fixed".
- Dry run by default; `--load` writes.

## Task groups

### 1. Claim and branch
1. Set the Phase 6 DE row to `In progress`; correct its stale note (the raw files are already in S3). Branch from `origin/main`. Done.

### 2. Read and validate
1. `transform/marsden_load.py`: read `data/out/marsden/` (or rerun her script with `--reproduce`), validate with `transform.marsden.schemas.validate_outputs`, and compare her run manifest's input checksums with the S3 manifests.
2. Stop on any validation finding; never edit a value.

### 3. Convert and map
1. Wide to long: every cell of both CSVs appears exactly once, with its unit and `indicator_id`.
2. Lineage mapping: `label` from the id, `source_ids` and `variables` as JSON text, `aggregation_window` from `temporal_window`, `spatial_support` and `resolution` from `spatial_scale`, `interpretation` from `formula`, `scale` `site`, `code_version` and `run_id` from her run manifest.

### 4. Schema and tables
1. `schema/005_marsden.sql`: `marsden_management` and `marsden_reconciliation` (plain `MergeTree`, `load_id`, one partition each); Pandera schemas and registry entries; `marsden_management` sets `lineage_column`.

### 5. Runner
1. `python -m transform.marsden_load [--reproduce] [--load]`: lineage first, then the two tables.

### 6. Validation and close
1. Golden values, live reproduction, idempotent loads; results, tracker, `/code-review`, PR.

## Files, tables and endpoints
- New: `transform/marsden_load.py`, `schema/005_marsden.sql`, tests.
- Changed: `common/schemas.py`, `specs/roadmap.md` (own row).
- ClickHouse: `marsden_management`, `marsden_reconciliation` (new); `indicator_lineage` (+4 rows).

## Dependencies and interfaces
- **DS2:** her script, schemas and CSV names are the contract and are not changed. She is told the lineage mapping and the run id convention. Her schema tests still error without the raw files (14 in a fresh checkout); not fixed here, by decision.
- **BE and FE:** `GET /evidence/marsden` reads `marsden_management`, `marsden_reconciliation` and the lineage; the validation page can show the reconciliation.
- **Phase 14:** the validation summary cites the reconciliation record.

## Data size
Tiny: 120 and 20 rows; the five raw files are about 5 MB.

## Risks and open questions
- One check stays UNRECONCILED by design: 2-yr manufactured N is 74.5 from Table S3 and 80 in the paper's text; DS2 traced it to 2011 and the cause is unknown.
- The outputs are not in git (regenerated), so a load is only as reproducible as the script and inputs; the run manifest records both checksums and is kept in the lineage `code_version`.
- Applied N excludes biological N fixation, manure N is total N, one site, treatment-level values: these limits live in her lineage and must reach the app.
- `rotation` in the reconciliation record holds free text such as "3-yr & 4-yr", so it is a string there and an enum in `marsden_management`.
