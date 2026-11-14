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
- **POWER first pull (2026-11-14), uploaded the same day to `raw/power/daily-point-api-v2.10.3/2026-11-14/` (read back and checked, 0 problems), ahead of DS2's review to save time:** Marsden site, 2003-01-01 to 2011-12-31, 7 variables, 380 KB, all 3,287 days present, 0 fill values. Header: API v2.10.3, sources MERRA2, SYN1DEG and POWER, time standard LST. The API returns the coordinates sent (rounded), not a grid-cell centre, and ALLSKY comes from a 1 degree grid, so DS2's "same cell" de-duplication for the full run needs a rule. Awaiting DS2's comparison with Table S1.
- **SSURGO first pull (2026-11-14), uploaded the same day to `raw/ssurgo/soil-data-access/2026-11-14/primary-001/` (read back and checked, 0 problems), ahead of DS2's review to save time:** `primary-001`, steps A to D, 4 files, 0.1 MB. DS2's main query (`STIntersection`) was accepted, no column was rejected, and area shares over the 10 map units sum to 1.000. Components sum to 100% in every map unit; 114 horizons on 30 components, depths ascending, no nulls. The field touches 10 map units, more than the sheet's typical 1-4 (largest: Canisteo 30%, Nicollet 29%). Survey version 2026-09-08 for both IA015 and IA169. Awaiting DS2's review.
- **CDL uploaded to S3 (2026-11-14):** 22 GeoTIFFs and 22 class tables, 39.6 MB, at `raw/cdl/annual-30m-website-export/2026-11-14/`, each read back and checked. DS1 reviewed the CDL upload and is satisfied (relayed by the DE, not in writing). Per-field clipping is a Phase 3 step that DS1 said she will do; the roadmap lists it as the DE's, so ownership should be confirmed.
- **Full runs uploaded (2026-11-14):** POWER 46 files (45 fields plus the Marsden site, 1991-2025, 67.8 MB), SSURGO all 45 fields (180 files, 1.2 MB, 176 new plus the 4 already in S3), HLS first pull (`primary-001`, 2023, 460 files, 3.2 MB). DS2 approved the POWER and SSURGO full runs (relayed). The HLS full run (45 fields, 2023-2025) waits for DS1's sign-off on the first pull.
- **Whole bucket check (2026-11-14, after all of the above):** `verify_all` over `raw/`: 738 data files (cdl 44, hls 460, marsden 7, power 47, ssurgo 180), 738 manifests, 117.4 MB, 0 problems.
- **POWER:** the 46 full-run files hold only 7 distinct combinations of series (3 each for temperature, precipitation and wind, 4 for solar radiation), and only 4 fill values in total; grouping is Phase 4 work, as DS2 agreed. The Marsden site has both the 2003-2011 first-pull file (the DS2 review copy) and the 1991-2025 file (use this one for indicators).
- **SSURGO:** step A's main query worked for all 45 fields, with no fallback needed. Map units per field range from 2 to 11 (median about 5); only 9 of 45 fields have 4 or fewer, against DS2's sheet expectation of 1 to 4. DS2 to confirm this is acceptable.
- **Dev sample built (2026-11-14):** `data/sample/primary-001/`, 48 files, 355 KB, tracked in git: 11 CDL windows, 32 HLS band files for 4 fully clear Landsat and 4 fully clear Sentinel-2 scenes, POWER for 2023, and the 4 SSURGO responses. `sample_manifest.json` records the S3 object each file came from. `tests/test_dev_sample.py` (7 tests) loads it with no S3 access, and checks that the CDL windows reproduce the committed crop sequence `SCSCSCSCSCS` and that the SSURGO area shares sum to 1.
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
