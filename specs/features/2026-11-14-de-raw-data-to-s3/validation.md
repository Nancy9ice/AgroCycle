# Validation: Raw data into S3

Merge when every row below passes, a DS has reviewed each first pull, and the results section is filled in.

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
|---|---|---|
| 1. Manifest and checksum match | A script lists `raw/`, reads each object back, hashes it and compares with its manifest | Script output |
| 2. No overwrite | `pytest tests/test_s3_store.py`: a second upload to the same key is refused (fake S3 client) | Pytest output |
| 3. Files open, bbox, CRS, dates match | `ingest/checks.py` run on every file, plus `pytest tests/test_checks.py` for pass and fail cases | Check output per source |
| 4. Subset and budget | The `subset.json` in each manifest and total size per source against its cap | Size table in this file |
| 5. CDL clips | 22 clips listed with manifests and notes | S3 listing output |
| 6. HLS counts and gaps | Output files contain valid-observation counts and gap fields named in the sheet | Check output |
| 7. Dev sample | `pytest` loads `data/sample/` | Pytest output |
| 8. DS review of first pulls | DS1 for CDL and HLS, DS2 for POWER, SSURGO and Marsden, each recorded below | Written sign-off, or relayed and marked as such |
| 9. No secrets or large data | `git ls-files`, `git grep` for key-like strings, size check | Command output |
| 10. `make check` | Run on the branch | Terminal log |

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
