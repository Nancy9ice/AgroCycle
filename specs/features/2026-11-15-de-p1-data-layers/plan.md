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
- New: `docs/source_requirements/de_p1_layers_draft.md`; per layer `ingest/<layer>.py` and `transform/<layer>/`; migration `schema/007_p1_layers.sql` with only the tables of approved layers (`county_stats`, `market_prices`, `naip_tiles`); Pandera schemas in `common/schemas.py`; offline tests.
- Changed: `transform/sources/catalog.py` (a record per approved layer), `specs/roadmap.md` (tracker row).

## Steps (in order)
1. Claim the task in the tracker, branch from `origin/main`, write the spec and the draft sheets. Done in this change.
2. Send the draft to DS1 and DS2 (Nancy relays). Record each reply.
3. Per approved layer: coverage check (AMS, NAIP) or dry run, size against the budget, then `--execute` on Nancy's say-so.
4. Clean, validate with Pandera, load, add the `data_sources` row.
5. Validation, results, tracker, `/code-review`, PR.

## Dependencies and interfaces with other roles
- **DS1/DS2:** sign-off per layer and the decisions in the sheet (commodities and years, report IDs, whether a single-date NAIP chip is useful). Phase 2 tables and `data_sources` are Done.
- **BE/FE (Phase 13)** read the new tables only after their layer is loaded; they are told per layer. Until then the P1 panels stay "not available".

## Data size and subsets
Budgets are in the draft sheet: NASS under 5 MB, AMS under 20 MB, NAIP under 100 MB. Bbox or county requests only. A layer over budget is cut down or dropped, not pulled whole.

## Risks and open questions
- API keys (NASS, AMS) are needed and must stay out of the repo.
- AMS and NAIP coverage are unverified; either may come out as "dropped, no usable coverage".
- If a DS wants PRISM or SMAP/GPM back, that is a spec change and a new sign-off.
- Sign-offs may not arrive in time. The fallback is a dropped row, not a guess.
