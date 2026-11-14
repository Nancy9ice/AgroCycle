# Validation: ClickHouse skeleton and lineage

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
|---|---|---|
| 1. Migration creates tables, is rerunnable | Live: run `common.migrate` twice in a scratch database; compare `system.tables`. Offline: SQL names every column the schemas list | pytest output, live log |
| 2. Bad enum or null key rejected | Offline test with invalid frames | pytest output |
| 3. Idempotent `REPLACE PARTITION` load | Live: load the same frame twice, compare table hashes (sum of `cityHash64` per row, ignoring `load_id`, so row order does not matter) and key counts. Offline: fake client records staging, assert, swap, drop in order | hash values in log |
| 4. Failed assertion leaves the live table unchanged | Offline and live: row count and hash before and after a rejected load | pytest output |
| 5. Lineage-less indicator row is flagged | Offline assertion test; live check against a scratch indicator table | pytest output |
| 6. `make check` passes without credentials | Run with ClickHouse variables unset in a clean shell | `make check` output |
| 7. Live tests clean up | The fixture asserts the scratch database is gone after each test | pytest output |
| 8. Reload of one source leaves others unchanged | Live: load CDL and POWER rows, reload CDL smaller, count both | pytest output |
| Lint and existing tests still pass | `make check` | output |
| Hand-check | Read `schema/001_core.sql` against DS2's `LINEAGE_FIELDS` and the PRD §6.1 list; DS2 reviews the lineage columns | PR comment |

Merge when: every row above is green, DS2 has confirmed the lineage columns, the code review findings are fixed, and the tracker row is updated.

## Results (fill in after implementation)

- **Date completed:**
- **What was run:**
- **Passed:**
- **Failed or skipped:**
- **Evidence location:**
- **Roadmap exit check met:**
- **Roadmap tracker updated:**
