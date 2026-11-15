# Validation: Validate and load the Marsden records

## Checks

| Criterion | How it is verified | Evidence |
|---|---|---|
| 1. Outputs validate | Offline: his schemas and the DE's on synthetic frames, including a unit error, a wrong sum and an unknown rotation. Live: his real outputs | pytest output |
| 2. PRD targets | Offline: the 12 exact targets as golden values on a frame built from his numbers. Live: rerun his script and read the loaded summary rows | pytest output, query |
| 3. The gap stays visible | Offline and live: the UNRECONCILED and INFO rows load with their notes; a test fails if the status is changed | pytest output |
| 4. Lossless conversion | Offline: every cell of both wide frames appears once in the long frame; `applied = manufactured + manure` | pytest output |
| 5. Lineage link | Offline: an indicator without a lineage row is refused; the mapped rows validate against the lineage schema. Live: DS2's 21 rows have the same hash before and after | pytest output, hashes |
| 6. Input checksums | Live (skips without S3): the five SHA-256 values equal the S3 manifests | output |
| 7. Idempotent, portable | Live: load twice, compare hashes; `make check` with raw files and S3 absent | hash values, output |
| Hand-check | DS2 is told the lineage mapping and the run id convention; his reproduction is not changed | message |

Merge when: every row is green, the code review findings are fixed, and the tracker row is updated.

## Results

- **Date:** 2026-11-15. **Status: done.**
- **What was run:** `ruff` (clean for this work), `common.schema_check` (13 tables agree), the full `pytest` suite (555 passed, 1 xfailed, including 13 live ClickHouse tests in scratch tables), DS2's script rerun from the raw files, a dry run with the S3 checksum check, the real load, and a second and third load to prove it idempotent (the third with the final code, after the code review).
- **Passed (real data):**
  - The five raw input files used by DS2's run have the SHA-256 recorded by the Phase 1 upload in S3. His outputs pass his Pandera schemas and the DE's.
  - `marsden_management` 120 rows (108 by rotation-year, 12 summary): nine-year applied N 74.5, 56.556 and 40.806 and herbicide 1.925, 0.261 and 0.195, equal to the PRD targets under his rule (within half of the last digit); every row has `applied_n = manufactured_n + manure_n`; every row has a lineage row.
  - `marsden_reconciliation` 20 rows: 17 MATCH, 1 WITHIN_SEM, 1 INFO and **1 UNRECONCILED**. The 12 PRD checks are all MATCH. The gap (2-yr manufactured N, 74.5 from Table S3 against 80 in the paper's text, traced to 2011) is stored with his note and was not corrected.
  - `indicator_lineage`: +4 rows (25 in all) under their own code version, so DS2's 21 rows are untouched.
  - Loads are idempotent: identical content hashes on every rerun (management 5668926378767306400, reconciliation 16415580116144608353).
- **Not done / to know:**
  - The first real load attempt was refused by the migration runner's checksum guard: the pronoun cleanup had edited a comment inside the applied migration `003_indicators.sql`. The file was restored to its applied content and nothing had been written. One comment in that file therefore still says "her CSVs" about DS2; it cannot change without changing the stored checksum.
  - Not changed, by decision: the 14 schema tests of DS2 that error without the raw files.
  - DS2 is told, by message, the lineage mapping (his runner's convention, `scale` `site`, `variables` stored as a one-item list, code version and run id from his run manifest).
- **Code review (`/code-review medium`, 10 findings):** 9 fixed and tested, 1 answered. `--load` now always compares the input checksums with S3 (it only did so with `--check-s3`). A changed DS2 script would have left two versions of an indicator's lineage side by side; the loader now refuses until the old version's partition is dropped. The whole load, and building the frames, report failures cleanly instead of as tracebacks, and say that the tables printed as loaded stay in place. The run id is parsed from the timestamp, not by string replacement (`Z`, fractions and offsets give the same id). Duplicate keys fail as a schema error, not an opaque `ValueError`. A blank number in the reconciliation is a clear finding (only `note` is read as text). The enum reader in `schema_check` now takes only quoted labels followed by `=`. The convoluted live test is simplified. Answered, not a code change: the pronoun edits are not guesses, they follow what the DE stated about DS1 and DS2.
- **Evidence location:** `tests/test_marsden_load.py`, `tests/live/test_clickhouse_live.py`; DS2's outputs in `data/out/marsden/` (gitignored, regenerated).
- **Roadmap exit check met:** yes (DE part: the records are validated and loaded; the reproduction and its test on the PRD numbers are DS2's, Phase 6 DS2, already Done). **Tracker updated:** 2026-11-15, row set to `Done`.
