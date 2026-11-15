# Plan: P1 data layers (DE)

- **Role:** de
- **Spec created:** 2026-11-15
- **Roadmap phase and task:** Phase 12, DE: extract and clean the P1 layers

## Goal
Bring three P1 context layers (NASS QuickStats, AMS Market News, NAIP) into S3 and ClickHouse with manifests, schema checks and lineage, or mark each as dropped with a reason. **Scope narrowed 2026-11-15 (Nancy):** PRISM vs POWER and SMAP/GPM are dropped (low value for the farmer, SMAP/GPM too coarse for a field and P2 in the PRD table); erosion susceptibility is "not assessed". A DS can ask for PRISM back.

## Approach
- **The DE drafts the requirements sheets** (`docs/source_requirements/de_p1_layers_draft.md`) because DS1 and DS2 are busy. Each layer is built only after a DS approves it in chat; a relayed reply is labelled as relayed.
- **No sign-off means dry run only.** A size check is allowed. Nothing goes to S3 or ClickHouse for that layer, and the tracker says "no sign-off".
- **One layer at a time, smallest first:** NASS, AMS (coverage check first), NAIP (coverage check first; confirm with FE that Phase 13 will show it).
- Same pattern as P0: dry run by default, `--execute` only on Nancy's say-so (S3 cannot be undone), manifest per file, checksum verified after upload, Pandera before load, idempotent load, a `data_sources` row per layer.
- NAIP is stored as small per-field chips, not full tiles.

## Files, tables and endpoints
- New, built: `docs/source_requirements/de_p1_layers_draft.md`; `ingest/nass.py` and `transform/nass/` (clean, loader); `ingest/naip.py` and `transform/naip/` (index builder, loader); migrations `schema/007_county_stats.sql` and `schema/009_naip_tiles.sql`; Pandera schemas `COUNTY_STATS` and `NAIP_TILES` in `common/schemas.py`; offline tests (`tests/test_nass*.py`, `tests/test_naip*.py`).
- Not built yet: `ingest/ams.py`, `transform/ams/`, the `market_prices` migration and schema (AMS, blocked on an API key).
- Changed: `transform/sources/catalog.py` (records `nass_quickstats` and `naip_2025`, table links for `county_stats` and `naip_tiles`), `ingest/run.py` (`nass` and `naip` sources), `common/config.py` and `.env.example` (`NASS_API_KEY`), `tests/live/test_clickhouse_live.py` (the migration list now comes from the files; it was stale on `origin/main` too), `specs/roadmap.md` (tracker row and Phase 12 text).
- Migration numbers 007 and 009 sit beside `origin/main`'s 007 and 008 files; the repo already has two files numbered 006 and two numbered 007, and the migrator applies by file name.

## Steps (in order)
1. Claim the task in the tracker, branch from `origin/main`, write the spec and the draft sheets. **Done.**
2. Send the draft to DS1 and DS2 (Nancy relays). Record each reply. **Open:** NASS scope was relayed by Nancy; DS2's own confirmation and DS1's NAIP sign-off are still outstanding.
3. Per approved layer: coverage check (AMS, NAIP) or dry run, size against the budget, then `--execute` on Nancy's say-so. **NASS and NAIP done; AMS blocked** (see risks).
4. Clean, validate with Pandera, load, add the `data_sources` row. **NASS and NAIP done**; AMS not started.
5. Validation, results, tracker, `/code-review`, PR. **Code review done** (10 findings, 8 fixed, 2 left on purpose, see `validation.md`); `origin/main` merged in; PR after the final test run.

## Dependencies and interfaces with other roles
- **DS1/DS2:** sign-off per layer and the decisions in the sheet (commodities and years, report IDs, whether a single-date NAIP chip is useful). Phase 2 tables and `data_sources` are Done.
- **BE/FE (Phase 13)** read the new tables only after their layer is loaded; they are told per layer. `county_stats` and `naip_tiles` are loaded, but nothing reads them yet. The API's `/sources` endpoint already reads `data_sources`, so NASS and NAIP show there without code changes. The NAIP images are in S3, not ClickHouse, so BE has to serve them. Until a panel exists, the P1 panels stay "not available".

## Data size and subsets
Budgets are in the draft sheet: NASS under 5 MB, AMS under 20 MB, NAIP under 100 MB. Bbox or county requests only. A layer over budget is cut down or dropped, not pulled whole.

## Risks and open questions
- API keys (NASS, AMS) are needed and must stay out of the repo.
- **NAIP coverage is verified** (Iowa 2015 to 2025, odd years, over Story and Boone; 2025 is 0.6 m, four bands). Its licence text is not given by the catalogue and is unconfirmed.
- **AMS is blocked on an API key:** Nancy could not log in to My Market News to get one (the site also timed out for the DE). Found without a key: the Iowa Direct Hay Report (alfalfa hay, slug 2807) downloads as a public PDF, current edition only; no Iowa oats or red clover seed report has been found. AMS may end as "alfalfa hay snapshot only" or "dropped, no usable coverage".
- NAIP is a single late-summer date per tile (5 August to 26 September 2025), reference only, and nobody has yet committed to using it (DS1 boundary check, or FE basemap or toggle).
- If a DS wants PRISM or SMAP/GPM back, that is a spec change and a new sign-off.
- Sign-offs may not arrive in time. The fallback is a dropped row, not a guess.
