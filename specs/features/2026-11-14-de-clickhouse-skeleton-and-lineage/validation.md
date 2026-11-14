# Validation: ClickHouse skeleton and lineage

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
|---|---|---|
| 1. Migration creates tables, is rerunnable | Live: run `common.migrate` twice on scratch tables; compare `system.tables`. Offline: SQL names every column the schemas list | pytest output, live log |
| 2. Bad enum or null key rejected | Offline test with invalid frames | pytest output |
| 3. Idempotent `REPLACE PARTITION` load | Live: load the same frame twice, compare table hashes (sum of `cityHash64` per row, ignoring `load_id`, so row order does not matter) and key counts. Offline: fake client records staging, assert, swap, drop in order | hash values in log |
| 4. Failed assertion leaves the live table unchanged | Offline and live: row count and hash before and after a rejected load | pytest output |
| 5. Lineage-less indicator row is flagged | Offline assertion test; live check against a scratch indicator table | pytest output |
| 6. `make check` passes without credentials | Run with ClickHouse variables unset in a clean shell | `make check` output |
| 7. Live tests clean up | The fixture asserts no `scratch_` table is left; real tables checked before and after | pytest output |
| 8. Reload of one source leaves others unchanged | Live: load CDL and POWER rows, reload CDL smaller, count both | pytest output |
| Lint and existing tests still pass | `make check` | output |
| Hand-check | Read `schema/001_core.sql` against DS2's `LINEAGE_FIELDS` and the PRD §6.1 list; DS2 reviews the lineage columns | PR comment |

Merge when: every row above is green, DS2 has confirmed the lineage columns, the code review findings are fixed, and the tracker row is updated.

## Results

- **Date completed:** 2026-11-14 (code review pending)
- **What was run:** `ruff check .`, `python -m common.schema_check`, the full `pytest` suite, and the 6 live tests against the real ClickHouse server, which ran in about 50 s (live tests build `scratch_<id>_` tables and drop them). Before the live tests were reworked the first run found a real bug: the loader read partition ids from `system.parts`, which this user may not select from; it now uses `_partition_id`.
- **Passed:** lint; SQL and schemas agree (3 tables); 301 tests including 6 live: migration creates the tables and is rerunnable, loading each frame twice gives identical content, reloading one source leaves the others, a rejected load leaves the live table unchanged, a bad key and a lineage-less indicator are flagged. DS2's runner rows and the 45 demo fields fit the schemas. After the run: no `scratch_` table left; the real database holds `data_sources`, `fields`, `indicator_lineage` and `schema_migrations`, all empty except `schema_migrations` (1 row).
- **Failed or skipped:** the full suite shows 1 failure and 14 errors in `transform/marsden/tests/test_schemas.py`. They are not from this work (same result with the changes stashed): they need the raw Marsden files, which are gitignored and absent from a fresh checkout, and the tests do not skip. Owner: DS2. The live tests were skipped for everyone without ClickHouse settings, by design. Not verified: behaviour with two simultaneous loads of one table.
- **Evidence location:** `tests/live/test_clickhouse_live.py`, `tests/test_core_*.py`; hashes are printed by `pytest -s`. The old tables' DDL is in `docs/schema/dropped-tables-2026-11-14.sql`.
- **Roadmap exit check met:** the DE part, yes: tables exist and `make check` runs. The API returning a mock profile is BE's task.
- **Roadmap tracker updated:** 2026-11-14.
