# Plan: Fill data_sources and link every output to its source

- **Role:** de
- **Spec created:** 2026-11-15
- **Roadmap phase and task:** Phase 2 follow-up, DE: source provenance (PRD 6.1, FR-12, NFR-03)

## Goal
Make "where did this number come from" a join: one row per source with the PRD 6.1 fields, and a link from every indicator and every derived table to the sources behind it. Today `data_sources` is empty and the lineage names its sources as free text.

## Approach
- **One row per source pull** (decision 2026-11-15), eight rows: CDL, HLS Landsat, HLS Sentinel-2, the HLS no-data list, POWER, SSURGO and the two Marsden copies. File-level detail stays in the S3 manifests, which `verify_all` already checks.
- **Reshape the empty `data_sources`** with migration 006 (drop and recreate). Phase 2 designed it per file; it has no rows and BE does not read it. The migration runner learns to prefix `DROP TABLE IF EXISTS`, so the live tests can still work in scratch tables.
- **The DE compiles the PRD 6.1 text** (decision 2026-11-15) from the manifests, DS1's and DS2's source sheets, the lineage and the specs, and says so in a `compiled_from` column. DS1 and DS2 review it later; a correction is one line in `transform/sources/catalog.py`.
- What the manifests and S3 already say is read, not retyped: product, retrieval date, licence and evidence type from a manifest of each pull; file count and total size from an S3 listing.
- **`source_links`** (new): `indicator` rows built from the lineage's source text (DS2's content untouched) and `table` rows for crop history, HLS counts, climate, soil and Marsden.
- Dry run by default; `--load` writes.

## Task groups

### 1. Claim and branch
1. Add a tracker row for this follow-up as `In progress`. Branch from `origin/main`. Done.

### 2. Catalog and scan
1. `transform/sources/catalog.py`: the eight records' PRD 6.1 text, and the table-to-source links.
2. `transform/sources/scan.py`: per pull, the file count and size from an S3 listing and the product, retrieval date, licence and evidence type from one manifest; refuses a pull whose manifests disagree.

### 3. Schemas and migration
1. `schema/006_data_sources.sql`: drop and recreate `data_sources` per source; create `source_links`. Pandera schemas and registry entries; migration prefix support for `DROP TABLE IF EXISTS`.
2. Update the Phase 2 tests and fixtures that used the per-file design.

### 4. Runner
1. `python -m transform.sources.run [--load]`: scan, build, validate, link, load `data_sources` then `source_links`; refuses if the old table holds rows.

### 5. Validation and close
1. Golden tests, live check against S3, idempotent load; results, tracker, `/code-review`, PR.

## Files, tables and endpoints
- New: `transform/sources/{catalog,scan,run}.py`, `schema/006_data_sources.sql`, tests.
- Changed: `common/schemas.py`, `common/migrate.py` (prefix for DROP), tests and fixtures from Phase 2, `specs/roadmap.md` (own row).
- ClickHouse: `data_sources` (reshaped, 8 rows), `source_links` (new, about 40 rows).

## Dependencies and interfaces
- **BE and FE:** `data_sources` and `source_links` serve the evidence drawer and `GET /lineage/{id}`: indicator, then its sources with licence, version, retrieval date and limitations.
- **DS1 and DS2:** review the text compiled for their sources; their lineage content is unchanged. The link from indicator to source is by the exact `source_ids` text, so a changed source text in the lineage is refused until the catalog knows it.
- **This branch and PR #22:** both add a migration and registry entries; whichever merges second needs a short rebase.

## Data size
Eight and about forty rows.

## Risks and open questions
- The text is compiled, not authored by the owners. Anything in it the owners know better is theirs to correct.
- A source text in the lineage that the catalog does not know fails the build: new sources need a catalog entry.
- `version` in a manifest is the S3 layout folder name (for example `annual-30m-website-export`), not a product version; the catalog carries the human product version separately.
