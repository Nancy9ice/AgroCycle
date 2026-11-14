# Validation: Repo, infra and field GeoJSON setup

Merge when every row below passes and the results section is filled in.

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
|---|---|---|
| 1. `make check` runs | Run on the branch | Terminal log in this file |
| 2. S3 round-trip | `python -m scripts.smoke_s3`: SHA-256 of upload equals download | Script output |
| 3. ClickHouse works | `python -m scripts.smoke_clickhouse` | Script output |
| 4, 6, 7. Field file | `pytest tests/test_fields.py` and `python -m transform.field_schema`: counts, roles, counties, properties, `demo` labels, out-of-domain present, `cover_detail` rules | Pytest and validator output |
| 5. Invalid geometry rejected | Tests with a self-intersecting, an out-of-county, an empty and an oversized polygon | Pytest output |
| 8. No secrets | `git ls-files`, `git grep` for key-like strings and server addresses, size check | Command output |
| Field crop history matches the claim | `python -m scripts.verify_fields` recomputes each field's yearly dominant crop from the CDL rasters (needs the clips outside git) and compares with `field_selection_notes.csv`; `tests/test_field_notes.py` checks the notes against the field file and class rules offline | Script output; pytest output |
| CDL loader handles mixed grids | `tests/test_select_fields.py`: 30 m and 10 m years, differing extents, misaligned grids | Pytest output |

## Results

- **Date completed:** 2026-11-14
- **What was run:** `make check`; both smoke scripts; `python -m transform.field_schema`; the raster re-check of all 45 fields; a scan of tracked files for secrets and large files.
- **Passed:**
  - `make check`: ruff clean, the field validator passes, and 18 tests pass (field validator cases, `cover_detail` rules, offline checks of the selection notes, and the CDL loader on synthetic rasters).
  - S3: upload and download SHA-256 match (`fd8ac804...c656d`). The IAM user cannot delete objects, so the script overwrites one fixed key, `smoke/smoke_test.txt`, and one earlier test object remains under `smoke/`.
  - ClickHouse 24.8.14.39, database `agrocycle`: create, insert, query and drop work. Grants include `SELECT`, `INSERT`, `ALTER`, `CREATE`, `DROP` on `agrocycle.*`, but no `S3` grant.
  - Field file: 45 fields valid, 1 primary and 44 test, Story 23 and Boone 22, 18 out-of-domain (6 each of continuous corn, pasture/hay, mixed). All `boundary_source` is `demo`. All 6 pasture/hay fields have `cover_detail`, all `grass-pasture`.
  - Raster re-check: 0 mismatches between the saved polygons' crop sequence and the selection notes. The lowest dominant-crop share in any field and year is 0.908 (rule: at least 0.90).
  - Secrets: only `.env.example` is tracked, no key-like strings or server addresses in tracked files, no tracked file over 1 MB, and `.env` is ignored.
- **Failed or skipped:**
  - The ClickHouse smoke test failed once with a dropped connection during `CREATE TABLE` (first run, port 8123), then passed on three immediate reruns. The cause is unknown.
  - Clean-clone run: a teammate has since run the repo and reported that it works, including the S3 and ClickHouse smoke tests with their own credentials (relayed by the DE). The commit they ran and their system were not recorded, so it is not reproduced evidence here.
  - 2024 and 2025 use the resampled 30 m CDL. Every web export gave 30 m or a broken download link (HTTP 400); native 10 m exists only as 9.0 GB and 9.8 GB national files. DS1 agreed to stay on 30 m. The mixed 30 m and 10 m path in `select_fields.py` is tested on synthetic rasters only, never on real 10 m data.
  - No uniform alfalfa, other hay, oats or clover blocks exist at the 90% rule, so the separate crop categories only show up as grass-pasture. See "Data limitations" in `requirements.md`.
  - Soil spread was checked only as a count of distinct series (10 among the 27 in-domain fields), taken at each field's centre point, not over the whole polygon.
  - DS1 has not yet reviewed the regenerated set (she reviewed the earlier version and answered the open questions). She has said the working class rules are fine (DE's rules, as relayed by the DE); the formal Phase 3 rule is still hers to write.
- **Evidence location:** `data/fields/fields.geojson`, `data/fields/field_selection_notes.csv`, `tests/`, terminal output in the session.
- **Roadmap exit check met:** yes, with caveats. The primary field and test-set polygons are committed as GeoJSON with provenance, and the README has setup steps. One teammate has confirmed the repo runs (see above).
- **Roadmap tracker updated:** yes, 2026-11-14 (row stays In progress until DS1's re-review of the regenerated set and the merge)
