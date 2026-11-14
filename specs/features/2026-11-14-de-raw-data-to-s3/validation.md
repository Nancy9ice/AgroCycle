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
- Marsden originals checked: all five of DS2's files match DS2's manifest, and DS2's 24 Marsden tests pass on them (1 expected failure, as documented by DS2). On a machine without the raw files those tests now skip with a reason instead of failing (`transform/marsden/tests/conftest.py`), because raw data is not in git and most of the team has no S3 access. `make check` without the data: 165 passed, 22 skipped.
- **Marsden uploaded to S3 (2026-11-14):** 7 files and 7 manifests, 5.2 MB. DS2's PDF, `s002`, `s004`, `s005`, `s007` and `MANIFEST.json` are at `raw/marsden/pone.0047149-supplement/2026-11-13/`; the Europe PMC ZIP is at `raw/marsden/europepmc-supplementary-zip/2026-11-14/`. Every file was read back and its SHA-256 checked; `verify_all` over `raw/marsden/`: 0 problems. DS2's review of this upload is still to be recorded.
- **POWER first pull (2026-11-14), not yet uploaded:** Marsden site, 2003-01-01 to 2011-12-31, 7 variables, 380 KB, all 3,287 days present, 0 fill values. Header: API v2.10.3, sources MERRA2, SYN1DEG and POWER, time standard LST. The API returns the coordinates sent (rounded), not a grid-cell centre, and ALLSKY comes from a 1 degree grid, so DS2's "same cell" de-duplication for the full run needs a rule. Awaiting DS2's comparison with Table S1.
- **SSURGO first pull (2026-11-14), not yet uploaded:** `primary-001`, steps A to D, 4 files, 0.1 MB. DS2's main query (`STIntersection`) was accepted, no column was rejected, and area shares over the 10 map units sum to 1.000. Components sum to 100% in every map unit; 114 horizons on 30 components, depths ascending, no nulls. The field touches 10 map units, more than the sheet's typical 1-4 (largest: Canisteo 30%, Nicollet 29%). Survey version 2026-09-08 for both IA015 and IA169. Awaiting DS2's review.
- Source sheets reviewed. DS2 and DS1 answered every point raised (relayed by the DE, not in writing). DS1's updated sheet is in the repo.

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
