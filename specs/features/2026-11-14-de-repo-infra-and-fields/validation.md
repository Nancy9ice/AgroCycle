# Validation: Repo, infra and field GeoJSON setup

Merge when every row below passes and the results section is filled in.

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
|---|---|---|
| 1. `make check` runs | Run on the branch | Terminal log in this file |
| 2. S3 round-trip | `python -m scripts.smoke_s3`: SHA-256 of upload equals download | Script output |
| 3. ClickHouse works | `python -m scripts.smoke_clickhouse` | Script output |
| 4, 6, 7. Field file | `pytest tests/test_fields.py` and `python -m transform.field_schema`: counts, roles, counties, properties, `demo` labels, out-of-domain present | Pytest and validator output |
| 5. Invalid geometry rejected | Tests with a self-intersecting, an out-of-county, an empty and an oversized polygon | Pytest output |
| 8. No secrets | `git ls-files`, `git grep` for key-like strings and server addresses, size check | Command output |
| Field crop history matches the claim | `python -m scripts.verify_fields` recomputes each field's yearly dominant crop from the CDL rasters (needs the clips outside git) and compares with `field_selection_notes.csv`; `tests/test_field_notes.py` checks the notes against the field file and class rules offline | Script output; pytest output |

## Results

- **Date completed:** 2026-11-14
- **What was run:** `make check`; both smoke scripts; `python -m transform.field_schema`; an independent raster re-check of all 45 fields; a scan of tracked files for secrets and large files.
- **Passed:**
  - `make check`: ruff clean, the field validator passes, and the tests pass (valid set, bow-tie, wrong county, empty geometry, missing property, bad enum and duplicate ID, set rules, oversized parcel, committed field file, and four offline checks of the selection notes).
  - S3: upload and download SHA-256 match (`fd8ac804...c656d`). The IAM user cannot delete objects, so the script overwrites one fixed key, `smoke/smoke_test.txt`, and one earlier test object remains under `smoke/`.
  - ClickHouse 24.8.14.39, database `agrocycle`: create, insert, query and drop work. Grants include `SELECT`, `INSERT`, `ALTER`, `CREATE`, `DROP` on `agrocycle.*`, but no `S3` grant.
  - Field file: 45 fields valid, 1 primary and 44 test, Story 23 and Boone 22, 18 out-of-domain (6 each of continuous corn, pasture/hay, mixed). All `boundary_source` is `demo`. Areas 5.8 to 43.6 ha.
  - Independent re-check: 0 mismatches between the saved polygons' crop sequence and the selection notes. The lowest dominant-crop share in any field and year is 0.913 (rule: at least 0.90).
  - Secrets: only `.env.example` is tracked, no key-like strings or server addresses in tracked files, no tracked file over 1 MB, and `.env` is ignored.
- **Failed or skipped:**
  - The ClickHouse smoke test failed once with a dropped connection during `CREATE TABLE` (first run, port 8123), then passed on three immediate reruns. The cause is unknown.
  - A fresh clone run by a teammate was not done (smoke tests only, as agreed). `make check` was run only in this working copy.
  - Soil spread was checked only as a count of distinct series (12 among the 27 in-domain fields). It is from the point at each field centre, not the whole polygon.
  - DS1 has not yet reviewed the primary field's CDL history or the class labels. The in-domain rule used is DE's working rule, not DS1's Phase 3 rule.
  - CDL clips for 2024 and 2025 were resampled to 30 m by the export. Not an issue for choosing fields, but the Phase 3 crop history must record the real resolution.
- **Evidence location:** `data/fields/fields.geojson`, `data/fields/field_selection_notes.csv`, `tests/test_fields.py`, terminal output in the session.
- **Roadmap exit check met:** yes, with caveats. The primary field and test-set polygons are committed as GeoJSON with provenance, and the README has setup steps. "Everyone can run the repo" has not been confirmed by anyone else.
- **Roadmap tracker updated:** yes, 2026-11-14
