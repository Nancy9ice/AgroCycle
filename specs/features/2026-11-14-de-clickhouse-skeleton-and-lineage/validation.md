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
| 9. Empty or multi-partition frame rejected | Offline fake; live: a two-source frame is rejected and the table hash is unchanged | `test_a_frame_spanning_...`, `test_an_empty_frame_...` |
| 10. Date-only `retrieval_date` | Offline schema test with a time of day | `test_a_time_of_day_in_retrieval_date_is_rejected` |
| Lint and existing tests still pass | `make check` | output |
| Hand-check | Read `schema/001_core.sql` against DS2's `LINEAGE_FIELDS` and the PRD §6.1 list; DS2 reviews the lineage columns | PR comment |

Merge when: every row above is green, DS2 has confirmed the lineage columns, the code review findings are fixed, and the tracker row is updated.

## Results

- **Date completed:** 2026-11-14
- **What was run:** `ruff check .`, `python -m common.schema_check`, the full `pytest` suite, and the 7 live tests against the real ClickHouse server (about 60 s) (live tests build `scratch_<id>_` tables and drop them). Before the live tests were reworked the first run found a real bug: the loader read partition ids from `system.parts`, which this user may not select from; it now uses `_partition_id`.
- **Passed:** lint; SQL and schemas agree (3 tables); 309 tests including 7 live: migration creates the tables and is rerunnable, loading each frame twice gives identical content, reloading one source leaves the others, a rejected load leaves the live table unchanged, a bad key and a lineage-less indicator are flagged. DS2's runner rows and the 45 demo fields fit the schemas. After the run: no `scratch_` table left; the real database holds `data_sources`, `fields`, `indicator_lineage` and `schema_migrations`, all empty except `schema_migrations` (1 row).
- **Failed or skipped:** the full suite shows 1 failure and 14 errors in `transform/marsden/tests/test_schemas.py`. They are not from this work (same result with the changes stashed): they need the raw Marsden files, which are gitignored and absent from a fresh checkout, and the tests do not skip. Owner: DS2. The live tests were skipped for everyone without ClickHouse settings, by design. Not verified: behaviour with two simultaneous loads of one table.
- **Code review (`/code-review medium`, 10 findings):** fixed 8. A frame spanning several partitions, or an empty frame, is now rejected (several swaps are not atomic; an empty frame silently loaded nothing). Each load has its own staging table (`<table>__staging_<load_id>`), so two loads cannot collide. `retrieval_date` must be a date with no time of day, so Pandera and the Date column agree on the key. Live tests skip on any connection failure, not only missing settings. `split_statements` handles `;` inside strings and trailing comments. A migration prefix refuses anything but `CREATE TABLE IF NOT EXISTS`, so it cannot reach real tables. `git_sha` carries `-dirty` for an unclean tree. Tables of indicator values can set `lineage_column` so the orphan check runs inside `load`. **Not changed:** `input_sha256` hashes the frame's CSV text, so it is stable within one environment only (documented); `schema_check` does not see columns added by a later `ALTER` migration (limit noted for the first such file).
- **Evidence location:** `tests/live/test_clickhouse_live.py`, `tests/test_core_*.py`; hashes are printed by `pytest -s`. The old tables' DDL is in `docs/schema/dropped-tables-2026-11-14.sql`.
- **Roadmap exit check met:** the DE part, yes: tables exist and `make check` runs. The API returning a mock profile is BE's task.
- **Roadmap tracker updated:** 2026-11-14.
