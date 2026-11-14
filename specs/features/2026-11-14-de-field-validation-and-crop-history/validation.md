# Validation: Field validation and crop history

## Checks

| Criterion | How it is verified | Evidence |
|---|---|---|
| 1. Fields valid and loaded | `make fields` and a load test; live check that 45 rows are in `fields` | output, row count |
| 2. Shares correct | Offline: synthetic rasters with known counts. Live (skips without clips): recompute the primary and 5 sample fields independently with a separate method and compare | pytest output, comparison table |
| 3. DS1's example | Offline test of `S C S C S C S C S C S` | pytest output |
| 4. Thresholds | Offline tests at exactly 60 % and 20 % | pytest output |
| 5. Rule order and boundaries | Offline tests at 7 of 10 and 8 of 11, and one field matching several rules | pytest output |
| 6. Provenance on every row | Pandera schema requires `rule_version`, resolution, version, limitation | schema tests |
| 7. Unknown codes | Offline test with an unexpected code | pytest output |
| 8. Load idempotent | Live: load twice, compare hashes (uses the Phase 2 live tests' pattern) | hash values in log |
| 9. `make check` portable | Run with S3 and ClickHouse settings absent | output |
| 10. Continuous-corn fields listed | Output table checked against the 5 expected ids | validation results |
| Hand-check | primary-001 against DS1's example; DS1 reviews flagged `mixed_uncertain`, `low_confidence` and unexpected-rotation fields | PR comment |

Merge when: every row is green, DS1 has reviewed the flagged fields and confirmed the rule ambiguities, the code review findings are fixed, and the tracker row is updated.

## Results (fill in after implementation)

- **Date completed:**
- **What was run:**
- **Passed:**
- **Failed or skipped:**
- **Evidence location:**
- **Roadmap exit check met:**
- **Roadmap tracker updated:**
