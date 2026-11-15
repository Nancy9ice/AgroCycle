# Validation: Analysis-ready HLS: mask, scaling and valid-pixel counts

## Checks

| Criterion | How it is verified | Evidence |
|---|---|---|
| 1. Mask rule | Offline: all 256 `Fmask` values against the rule, bit by bit | pytest output |
| 2. Fill, scale, polygon | Offline: synthetic stacks with known values; the committed primary-001 sample scenes | pytest output |
| 3. Counts add up | Offline property tests; Pandera rejects a frame where `valid + flagged + fill != total` | pytest output |
| 4. All 16,560 windows | Live (skips without the stacks): the row count and the `no_data` rows against `skipped_no_data.csv` | output |
| 5. Independent recount | Offline on the sample scenes; live for the primary and 5 sample fields, every window, by shapely centres and plain bitwise code | pytest output |
| 6. Idempotent load | Live: load twice, compare content hashes (the earlier phases' pattern) | hash values |
| 7. `make check` portable | Run with S3 and ClickHouse settings absent | output |
| Hand-check | DS1 opens 3 scenes (one clear, one cloudy, one no-data) beside their masks and agrees; DS1 confirms the corrected bit rule | PR comment |

Merge when: every row is green, DS1 has confirmed the mask rule and that her sheet is superseded, the code review findings are fixed, and the tracker row is updated.

## Results (fill in after implementation)

- **Date completed:**
- **What was run:**
- **Passed:**
- **Failed or skipped:**
- **Evidence location:**
- **Roadmap exit check met:**
- **Roadmap tracker updated:**
