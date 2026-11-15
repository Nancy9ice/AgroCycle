# Validation: P1 data layers (DE)

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
|---|---|---|
| 1. Decision recorded per layer | Read the tracker row and the sign-off note before each load | Tracker rows, `docs/source_requirements/de_p1_layers_draft.md` sign-off table |
| 2. No sign-off means nothing loaded | List `raw/<source>/` in S3 and count rows in the table for that layer | Listing and count in the results below |
| 3. Dropped layers recorded | Tracker rows for PRISM, SMAP/GPM and erosion | Tracker |
| 4. Size budget | Dry-run size report before `--execute`; S3 listing total after | Dry-run output, listing |
| 5. Manifests and checksums | `verify_all` over each `raw/<source>/` | 0 problems |
| 6. Pandera schemas | Offline tests with good and bad fixtures; run on the real data before load | `pytest` output |
| 7. Idempotent load | Load twice, compare table hashes | Hash comparison |
| 8. Recount | Count rows in the raw files independently and compare with the table | Recount script output |
| 9. Sources | Query: no loaded layer without a `data_sources` row | Query output |
| 10. No credentials committed | Search the diff and manifests for keys | Search output |
| Whole task | `make check`, then `/code-review` on the branch before the PR | Command output |

## Results (fill in after implementation)

### NASS QuickStats, in progress 2026-11-15 (not loaded; DS2 sign-off pending)
- **Scope decision (relayed by Nancy, 2026-11-15):** keep all four commodities and every available year in 2003-2025. DS2's own confirmation is still open.
- **Dry run against the live API:** 31 files, 0.6 MB (budget 5 MB), all file checks pass, nothing uploaded. 2 requests are empty by design (hay AREA PLANTED, which NASS does not publish; the API answers `invalid query`) and are listed in `empty_requests.json`.
- **Clean step:** 633 rows (same as the raw), 631 reported and 2 withheld (Boone hay excl. alfalfa, area harvested and production, 2013), kept as null. Pandera schema passes; the SQL and schema agree (`schema_check`).
- **Independent cross-check:** production against yield x area harvested for 171 county/crop/year combinations: ratio 0.987 to 1.007, none outside 2 % (rounding).
- **Tests:** `tests/test_nass.py` (12) and `tests/test_nass_clean.py`; full suite passed before the clean step was added.
- **Uploaded 2026-11-15 on Nancy's explicit go:** 31 files plus 31 manifests (0.6 MB) under `raw/nass/api_GET/2026-11-15/`; `verify_all` 0 problems. A search of all 62 objects found the API key in none. The upload went ahead before DS2's own sign-off (the scope was relayed by Nancy), so DS2 confirmation is still open.
- **Loaded into ClickHouse 2026-11-15 on Nancy's go:** migration 007 applied, `county_stats` 633 rows (Story 304, Boone 329). Recount: 633 in the table = 633 in the frame = 633 raw rows. A second load gave an identical table hash (`table_hash` before and after equal) and one `load_id`. No withheld row holds a value; no reported row is null. The load's recorded git SHA ends in `-dirty` because `uv run` had rewritten `uv.lock`, not because of a code change.
- **Provenance loaded 2026-11-15 on Nancy's go:** `data_sources` 9 rows and `source_links` 38 with `nass_quickstats` (31 files, 606,215 bytes) and `county_stats` linked to it; the dry run before it matched.
- **Not yet done:** DS2 confirmation, `/code-review`.

### NAIP 2025, 2026-11-15 (raw files uploaded; no table yet; DS1/FE use not confirmed)
- **Coverage checked:** Planetary Computer `naip` has Iowa tiles for 2015 to 2025 (odd years) over Story and Boone; 2025 is 0.6 m, four bands.
- **Dry run:** 45 chips, 84.6 MB (budget 100 MB), median 2.0 MB, largest 3.7 MB; all checks pass (4 uint8 bands, CRS, covers the field box plus buffer, no empty or edge pixels). A first run failed two chips (test-032, test-041, 136 and 156 m short) because the mosaic of a field across two tiles used the wrong transform; fixed, and a regression test covers it (`tests/test_naip.py`, 7 tests; I did not run it against the old code). The repaired test-032 chip was inspected by eye: seamless, field and waterway visible.
- **Uploaded on Nancy's explicit go:** 45 images + 45 manifests under `raw/naip/naip-2025/2026-11-15/`; `verify_all` 0 problems; none of the 45 manifests contains a download token.
- **Flight dates:** 6 dates between 2025-08-05 and 2025-09-26, recorded per chip. Late-summer snapshot, not crop ground truth.
- **`naip_tiles` loaded 2026-11-15 on Nancy's go:** migration 009 applied, 48 rows (45 fields; test-032, -041, -044 have two tiles each), flight dates 2025-08-05 to 2025-09-26. A second load gave an identical table hash; one load_id; the 48 rows and 84.6 MB match the manifests. Built from the S3 manifests only, nothing re-measured; resolution (0.6 m) is the catalogue's 2025 value.
- **NAIP provenance loaded:** `data_sources` is now 10 rows (`naip_2025`: 45 files, 84,612,647 bytes) and `source_links` 39 (`naip_tiles` linked to it). The loads recorded a `-dirty` git SHA because `uv run` had rewritten `uv.lock`, not because of a code change.
- **Open:** licence text unconfirmed; DS1 sign-off and a named consumer (DS1 boundary check or FE basemap/toggle); nothing reads `county_stats` or `naip_tiles` yet; `/code-review`.


- **Date completed:**
- **What was run:**
- **Passed:**
- **Failed or skipped:**
- **Evidence location:**
- **Roadmap exit check met:**
- **Roadmap tracker updated:**
