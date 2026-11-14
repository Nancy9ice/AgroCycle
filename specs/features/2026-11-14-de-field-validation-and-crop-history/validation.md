# Validation: Field validation and crop history

## Checks

| Criterion | How it is verified | Evidence |
|---|---|---|
| 1. Fields valid and loaded | `make fields` and a load test; live check that 45 rows are in `fields` | output, row count |
| 2. Shares correct | Offline: synthetic rasters with known counts. Offline, on the committed dev sample: primary-001 for 11 years against a shapely pixel-centre count. Live (skips without clips): the same independent count for one field per class (rotation Story, rotation Boone, continuous corn, pasture/hay, mixed) | pytest output, comparison table |
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

## Results

- **Date completed:** 2026-11-14
- **What was run:** `ruff`, `common.schema_check`, the full `pytest` suite (358 passed, including the 7 live ClickHouse tests), a dry run on the real clips, the real load (`python -m transform.crop_history.run --load`), and the load a second time. Output CSVs recomputed after the review fixes are byte-identical to what was loaded.
- **Passed:** every check above. In ClickHouse: `fields` 45 rows, `crop_class_shares` 884, `crop_history` 495 (45 fields x 11 years), `crop_rotation` 45; the second load left row counts and content hashes unchanged. Classes: 27 rotation (primary-001 and 26 test), 11 continuous corn, 6 pasture/hay, 1 mixed. primary-001 is `S C S C S C S C S C S`, 10 of 10 alternations, as in DS1's worked example. Shares match an independent shapely pixel-centre count for primary-001 in all 11 years (committed dev sample) and for one field per class on the real clips. test-039, -040, -042, -043 and -044 load as `continuous_corn`, as decided; they are the only fields whose class differs from the Phase 0 label.
- **For DS1 (open, not blocking):** all 495 field-years are `ok` (none mixed/uncertain or low-confidence), so the 60 % and 20 % thresholds are untested on real data. One code is not in the rules: 27 (Rye), 1 class-share row, kept as `other_crop` and flagged. All 6 pasture/hay fields are grass-pasture (176); no field grows alfalfa or oats, so the alfalfa/oats gap in the pasture/hay rule affects none. Still to confirm: code 176 listed under two groups; 2008-2025 in the rules text vs 2015-2025 in the data; the rotation threshold is an absolute 7 alternations even when uncertain years shrink the counted transitions; 2024-2025 are resampled from 10 m.
- **Code review (`/code-review medium`, 10 findings):** fixed 8. A field with no clips, or fewer than 11 consecutive years, now fails naming the field (it was classified silently). A low-confidence year names no crop (`dominant_group = low_confidence`) instead of its top class. An empty polygon names the field and year. The runner catches I/O errors. `--load` validates all four frames before touching a table and checks afterwards that the four tables agree. The Phase 0 comparison skips notes it does not know. Not changed: the absolute 7-alternation threshold (the written rule, listed for DS1) and the four loads not being one atomic step (checked afterwards instead).
- **Failed or skipped:** 1 failure and 14 errors in `transform/marsden/tests/test_schemas.py` (not from this work; they need raw Marsden files). Two lint errors in `web/scripts/export_engine.py` are on `main` already. DS1 has not reviewed the output yet.
- **Evidence location:** `tests/test_crop_rules.py`, `tests/test_crop_history_build.py`, `tests/live/test_clickhouse_live.py`; CSVs in `data/out/crop_history/` (gitignored).
- **Roadmap exit check met:** yes for the DE part: the tables pass schema checks and are loaded in ClickHouse. Serving through the API is BE's.
- **Roadmap tracker updated:** 2026-11-14.
