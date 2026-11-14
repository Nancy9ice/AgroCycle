# Validation: Repo, infra and field GeoJSON setup

Merge when every row below passes and the results section is filled in.

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
|---|---|---|
| 1. `make check` runs | Run on the branch | Terminal log in this file |
| 2. S3 round-trip | `python scripts/smoke_s3.py`: SHA-256 of upload equals download | Script output |
| 3. ClickHouse works | `python scripts/smoke_clickhouse.py` | Script output |
| 4, 6, 7. Field file | `pytest tests/test_fields.py`: counts, roles, counties, properties, `demo` labels, out-of-domain present | Pytest output |
| 5. Invalid geometry rejected | Tests with a self-intersecting and an out-of-county polygon | Pytest output |
| 8. No secrets | `git status` and `git diff --stat` show no env file or data; `.env.example` has no values | Command output |

## Results (fill in after implementation)

- **Date completed:**
- **What was run:**
- **Passed:**
- **Failed or skipped:**
- **Evidence location:**
- **Roadmap exit check met:**
- **Roadmap tracker updated:**
