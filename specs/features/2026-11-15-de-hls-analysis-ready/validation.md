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

## Results

- **Date:** 2026-11-15. **Status: the code, its tests and the table in ClickHouse are done; DS1's review is outstanding.**
- **What was run:** `ruff` (clean for this work), `common.schema_check` (7 tables agree), the full `pytest` suite (450 passed, 1 xfailed, including 8 live ClickHouse tests in scratch tables), the dry run on the real pull, a first real load (`python -m transform.hls.run --load`, migration 004 applied) and its repeat to prove it idempotent.
- **Passed (real data, 16,560 windows, 45 fields, 2023-04-01 to 2025-10-30):**
  - Every window is counted once. Total pixels in the field polygons 3,119,904: valid 1,471,085 (47 %), flagged 1,273,018, fill 375,801. In every row `fill + flagged + valid = total`.
  - Each field's polygon pixel count is identical in all its windows (smallest 62), and an independent recount (shapely pixel centres and plain bitwise code) agrees for every window of 6 fields (over 1,000 windows) and for the 8 committed primary-001 sample scenes.
  - The mask rule is tested for all 256 `Fmask` values; bits 0, 6 and 7 never mask; real values behave as intended (194, cloud plus aerosol, is masked; 64, 128 and 192, aerosol only, are kept).
  - With the final definition: **14,496 observed and 2,064 no_data**. The 1,962 windows Phase 1 listed are all `no_data` and keyed to the list; 102 further stored windows have data in the 500 m buffer but none over the field. Among the observed: 5,943 have no valid pixel (cloud), 7,804 have at least half valid pixels, and 167 have a swath edge through the field.
  - Live: the table loads twice with identical content hashes and keeps its Enum and dates; the local and S3 sources give identical rows (tested with a fake S3).
- **Not done / to do:**
  - (Resolved 2026-11-15.) The table first held the whole-window definition (14,598 observed, 1,962 no_data, and per-stack keys that did not exist for the 1,962). After the code review the DE reran `--load` and it was replaced. Now: 16,560 rows, **14,496 observed and 2,064 no_data**, no row breaks `fill + flagged + valid = total` or `no_data` iff every field pixel is fill, 1,962 rows keyed to `skipped_no_data.csv` and 14,598 to real stacks (including the 102 no_data windows that do have a stack), and a second run left an identical content hash.
  - **DS1 has not reviewed** three scenes against their masks, and has not been told that her sheet's masking and bit table are superseded.
  - Lint: 16 errors in other people's files fail `make check` on `main` already.
- **Code review (`/code-review medium`, 9 findings):** 7 fixed and tested, 2 not changed. Fixed: the field-level `no_data` (above, found on the real data); keys for windows that were never uploaded; S3 keys that are not field/day/file are skipped; an unreadable granule name is a clear error; a polygon with no pixel centre fails naming the field; listed windows are checked against the field file, the stacks and each other (a field with no stack, an unknown field, a window both stored and listed); the schema check now compares every Enum8 column with its schema, not only `evidence_type`; the masked-reflectance function and the counts are tested to agree. Not changed: caching the polygon mask per grid (the full run takes 2.3 minutes), and the hard-coded run date (one pull; one constant to change). The 004-versus-missing-003 numbering resolves when Phase 4 merges.
- **Evidence location:** `tests/test_hls_mask.py`, `tests/test_hls_counts.py`, `tests/live/test_clickhouse_live.py`; the CSV copy in `data/out/hls/` (gitignored).
- **Roadmap exit check met:** yes for the DE part: the denominators are loaded and checked. The features, and the keep-or-drop decision on HLS, are DS1's. **Tracker updated:** 2026-11-15.
