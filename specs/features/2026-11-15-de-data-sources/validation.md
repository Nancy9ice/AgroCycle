# Validation: Fill data_sources and link every output to its source

## Checks

| Criterion | How it is verified | Evidence |
|---|---|---|
| 1. PRD 6.1 fields present | Offline: every catalog record against the required field list; a test fails if one is empty | pytest output |
| 2. Matches S3 | Live (skips without S3): `file_count` and `total_bytes` against an independent recount of the objects; manifest fields against the manifests; no prefix under `raw/` left uncovered | pytest output, counts |
| 3. Every indicator linked | Offline: the lineage's three source texts map to one source each, an unknown text names the indicator and fails. Live: all 25 indicators have a link | pytest output, query |
| 4. Links valid | Offline: no link to a missing source or indicator; the table-to-source links as listed | pytest output |
| 5. Safe reshape | Offline: the runner refuses when the old table has rows; the migration prefix works for `DROP TABLE IF EXISTS` and refuses other statements | pytest output |
| 6. Idempotent, portable | Live: load twice, compare hashes; `make check` with S3 and ClickHouse settings absent | hash values, output |
| Hand-check | DS1 and DS2 read the text compiled for their sources and correct what is wrong | message, PR comment |

Merge when: every row is green, the code review findings are fixed, and the tracker row is updated.

## Results (fill in after implementation)

- **Date completed:**
- **What was run:**
- **Passed:**
- **Failed or skipped:**
- **Evidence location:**
- **Roadmap exit check met:**
- **Roadmap tracker updated:**
