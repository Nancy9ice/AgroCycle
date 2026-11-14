# Validation: Raw data into S3

Merge when every row below passes, a DS has reviewed each first pull, and the results section is filled in.

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
|---|---|---|
| 1. Manifest and checksum match | `verify_all` lists `raw/`, reads each object back, hashes it and compares with its manifest | Script output |
| 2. No overwrite | `pytest tests/test_s3_store.py` (fake client) and `scripts/smoke_ingest.py` (real bucket) | Pytest and script output |
| 3. Files open, bbox, CRS, dates match | `ingest/checks.py` run on every file, plus `pytest tests/test_checks.py` | Check output per source |
| 4. Subset and budget | The `subset` in each manifest and total size per source against its cap | Size table in this file |
| 5. CDL clips | 44 files listed with manifests and notes | S3 listing output |
| 6. HLS counts and gaps | Output files contain valid-observation counts and gap fields named in the sheet | Check output |
| 7. POWER | Per cell: 12,784 dates for each of 7 variables, fill values as returned, header present, field-to-cell mapping in the manifest | Check output |
| 8. SSURGO and Marsden | Raw responses for steps A to D per field, query in the manifest; Marsden ZIP and 7 files, none HTML | Check output |
| 9. Dev sample | `pytest` loads `data/sample/` | Pytest output |
| 10. DS review of first pulls | DS2: POWER (Marsden site 2003-2011), SSURGO (`primary-001`), Marsden. DS1: CDL, HLS | Written sign-off, or relayed and marked as such |
| 11. No secrets or large data | `git ls-files`, `git grep` for key-like strings, size check | Command output |
| 12. `make check` | Run on the branch | Terminal log |

## Progress so far (2026-11-14)

- Tooling built and tested: 52 tests pass in `make check`.
- Real-bucket smoke test passed: missing key reported as 404, upload and read-back checksum, pre-check refusal, S3 conditional-write refusal, `verify_all` clean (output in `scripts/smoke_ingest.py`; two small test objects remain under `smoke/ingest-check/`).
- CDL dry run passed: 22 GeoTIFFs and 22 class tables, 39.6 MB, all in EPSG:5070 at 30 m and covering their counties' fields. Not uploaded.
- Source sheets reviewed. DS2 agreed to every point raised. DS1's open points are listed in `requirements.md`.

## Results (fill in after implementation)

- **Date completed:**
- **What was run:**
- **Passed:**
- **Failed or skipped:**
- **Sizes against budgets:**
- **DS reviews:** CDL ( ), HLS ( ), POWER ( ), SSURGO ( ), Marsden ( )
- **Evidence location:**
- **Roadmap exit check met:**
- **Roadmap tracker updated:**
