# Validation: Clean POWER and SSURGO, load the indicators

## Checks

| Criterion | How it is verified | Evidence |
|---|---|---|
| 1. POWER fill and gaps | Offline: the primary-001 sample and synthetic frames with a `-999` and a missing date. Live (skips without S3): 12,784 dates per variable for every point; the report names exactly the known fill values | pytest output, gap report |
| 2. Hard and soft checks | Offline tests for each rule at its boundary; a hard failure stops the run | pytest output |
| 3. Cells | Offline: identical series group, different series do not. Live: every field and `marsden-site` has one cell; the cell count matches the 7 distinct series sets found in Phase 1 | output |
| 4. SSURGO checks | Offline with the sample and synthetic bad frames (descending depths, `comppct_r` 120, shares summing to 0.8) | pytest output, findings report |
| 5. Schemas agree | `make schema-check`, Pandera rejection tests | output |
| 6. DS2's CSVs load | Offline: her runner's real lineage rows and synthetic indicator frames; an indicator without lineage is refused. Live: the three CSVs | pytest output, row counts |
| 7. Idempotent | Live: load twice, compare content hashes (the Phase 2 and 3 pattern) | hash values |
| 8. Parity and golden | Live: cleaned values equal `power_frame` for all points; the GDD golden season is re-run on the cleaned frame | pytest output |
| 9. `make check` portable | Run with S3 and ClickHouse settings absent | output |
| Hand-check | DS2 reviews the cleaned table against her indicators, the key of `field_indicators` and the unchanged column names | PR comment |

Merge when: every row is green, DS2 has confirmed the tables and the unchanged CSV contract, the code review findings are fixed, and the tracker row is updated.

## Results (fill in after implementation)

- **Date completed:**
- **What was run:**
- **Passed:**
- **Failed or skipped:**
- **Evidence location:**
- **Roadmap exit check met:**
- **Roadmap tracker updated:**
