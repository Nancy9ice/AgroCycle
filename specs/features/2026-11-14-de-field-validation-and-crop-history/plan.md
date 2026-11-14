# Plan: Field validation and crop history

- **Role:** de
- **Spec created:** 2026-11-14
- **Roadmap phase and task:** Phase 3, DE: field validation, CDL clip, crop history

## Goal
Load the 45 fields and their per-year crop history (2015-2025) into ClickHouse, computed from the CDL clips by DS1's rules v1.0, each row tagged with the rule version. DS1 reviews the output; BE serves it.

## Approach
- Reuse what exists: `transform/field_schema.py` already checks geometry (valid, non-empty, inside the county). This phase adds the flags and the load.
- Rules are pure functions, tested on DS1's own example first. Raster work is a thin layer around them.
- Reads the county clips from the Phase 1 pull folder (`CDL_DIR`, default `~/agrocycle_cdl`; the DE has it, teammates do not, so tests that need it skip). Counts pixels whose centres fall inside the polygon. Full recompute every run, loaded as one partition (about 5,000 rows), so reruns are atomic and identical.
- Loads go through `common.load` (Phase 2). Dry run by default, `--load` to write.

## Task groups

### 1. Claim and branch
1. Set the Phase 3 DE row to `In progress`. Branch from `origin/main` (PR #12 is merged). Done.

### 2. Rules as code
1. `transform/crop_history/rules.py`: class-code groups, dominant crop (60 %, low-confidence above 20 % no-data), sequence, rotation, continuous corn, pasture/hay, mixed, other; rule order from DS1's section 7.
2. Tests: DS1's primary-001 example, boundary cases at 60 %, 20 %, 7 of 10, 8 of 11, and the ambiguities listed below.

### 3. Zonal class counts
1. `transform/crop_history/zonal.py`: field polygon to the raster CRS, class counts per field and year, no-data count, product version and resolution recorded from the manifests.
2. Tests on small synthetic rasters with known counts, and on `data/sample/`.

### 4. Fields table
1. Build the `fields` frame from `fields.geojson` (role, boundary source, county, provenance, WKT), run `validate_fields`, load.

### 5. Tables, schemas and load
1. `schema/002_crop_history.sql`: `crop_class_shares`, `crop_history`, `crop_rotation` (plain `MergeTree`, `load_id`, one partition each).
2. Pandera schemas and registry entries in `common/schemas.py`, so `make check` keeps SQL and schemas in step.
3. `python -m transform.crop_history.run` (dry run) and `--load`; outputs also written to `data/out/crop_history/` (gitignored).

### 6. Validation and close
1. Recompute shares for the primary and 5 sample fields independently from the raw clips and compare; hand-check primary-001; list flagged fields for DS1.
2. Fill `validation.md`, update the tracker, run `/code-review`, open the PR.

## Files, tables and endpoints
- New: `transform/crop_history/{rules,zonal,run}.py`, `schema/002_crop_history.sql`, tests, `data/out/` (ignored).
- Changed: `common/schemas.py` (three tables, `fields` already there), `specs/roadmap.md` (own row).
- ClickHouse: `fields` (seeded), `crop_class_shares`, `crop_history`, `crop_rotation`, new.

## Dependencies and interfaces
- **DS1:** rules v1.0 (draft, not expert-reviewed). She confirms the ambiguities below and reviews flagged fields. She said she would clip CDL herself; the roadmap gives it to the DE, so the DE does it and tells her.
- **BE:** reads the three tables; names and columns are the contract. Announce when merged.
- **Phase 9 and 10 (DS2):** read `crop_rotation.field_class` and the per-year labels.
- **Phase 5:** the HLS-versus-CDL test reads `crop_history`.

## Data size
Clips already in S3 (about 40 MB for 2015-2025). Output about 5,000 rows.

## Risks and open questions
- Rules need DS1's confirmation on: code 176 appears in two groups (read as pasture/hay); alfalfa (36) and oats (28) are in no pasture/hay rule; the rules text says 2008-2025 but the data is 2015-2025 (the 11-year thresholds match 2015-2025); double-crop codes count as corn or soybean.
- 2024 and 2025 are resampled to 30 m from a native 10 m product, so share changes between 2023 and 2024 can be an artefact. Recorded per row; not corrected.
- Five test fields (test-039, -040, -042, -043, -044) become continuous corn. By decision they are kept and labelled by the rules, giving real out-of-domain cases.
- Pixel-centre counting on 20-40 ha fields gives a few hundred pixels per field, so edge pixels move shares by a point or two.
