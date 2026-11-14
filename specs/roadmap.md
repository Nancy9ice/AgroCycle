# AgroCycle — Roadmap

High-level implementation order in very small phases for the 2-day hackathon. MVP = P0 + P1. P0 is built first, then P1.

Roles: **DE** data engineer · **DS1** / **DS2** data scientists · **BE** backend · **FE** frontend · **F** farmer.
**Ownership split:** **DE** owns extraction and basic transformation, delivering analysis-ready data (download, clip to field bboxes, reproject, standardise units and formats, apply the given quality masks, convert fill values to null, validate schemas, and load clean tables). **DS1/DS2** own everything scientific built on top of that: feature engineering (indices, indicators, bare-field windows, crop-sequence features), the Marsden reproduction, applicability rules, the decision engine, and validation. **BE** wraps the engine in the API. Because the team is unfamiliar with these datasets, the DS write a short **source requirements sheet** (what to fetch and which masks and rules to apply) before the DE extracts, and walk the DE through each source's quirks.
Each phase has a small deliverable and an exit check. If a phase slips, cut from the end of the P1 list, never from P0.

Time blocks are indicative (≈2–3 h each). Tracks run in parallel; dependencies are noted.

## Progress tracker

**Update this table after every phase task, before starting the next one** (see `specs/development-rules.md`). Status values: `Not started`, `In progress`, `Blocked`, `Done`, `Dropped`. When a phase has several role tasks, add one row per task under the phase (e.g. "1 — DE: extraction"), and give each its own status. Link the feature spec folder from `specs/features/`.

| Phase | Name | Status | Role | Feature spec | Updated | Notes |
|---|---|---|---|---|---|---|
| 0 — DE: repo, infra, fields | Align and set up | Done | DE | [2026-11-14-de-repo-infra-and-fields](features/2026-11-14-de-repo-infra-and-fields/) | 2026-11-14 | Exit check met: 45 demo fields (27 rotation incl. the primary, 18 out-of-domain) in `data/fields/fields.geojson`, S3 and ClickHouse (`agrocycle`) smoke tests pass, a teammate ran the repo and it works, DS1 reviewed the fields and is fine with them. BE/FE API contract is not covered here. Limits to note for Phase 3 and 9: no fields already growing alfalfa/oats/clover; financial returns not modelled (see requirements.md) |
| 1 - DS1: requirements sheets | Raw data into S3 | Done | DS1 | specs/features/2026-11-14-ds1-hls-cdl-requirements/ | 2026-11-14 | HLS and CDL source requirements sheet updated (see ds1_source_requirements.md) |
| 1 — DE: raw data into S3 | Raw data into S3 | In progress | DE | [2026-11-14-de-raw-data-to-s3](features/2026-11-14-de-raw-data-to-s3/) | 2026-11-14 | In S3 and verified: CDL, Marsden, POWER (46 points), SSURGO (45 fields), HLS first pull. HLS full run (45 fields, 2023-2025, stacked files) is running. Dev sample built in data/sample/ |
| 1 — DS2: review first pulls | Raw data into S3 | Done | ds2 | [first-pull review](../docs/sources/ds2-first-pull-review-2026-11-14.md) | 2026-11-14 | POWER (Marsden site 2003-2011) and SSURGO (primary-001) first pulls **accepted**; full runs cleared. Recomputed from the raw files, not from the summary. POWER: 3,287 rows, no fill values, temperature within 1 C of Marsden Table S1 in 8 of 9 years (+0.35 C bias), but precipitation runs **11 % low** (-92 mm/season, lower in 7 of 9 years) against the station, so dry spells are more likely overstated; recorded in the lineage. ALLSKY_SFC_SW_DWN comes from SYN1DEG, a 1-degree grid, making reference ET the least local indicator. SSURGO: 10 map units over 43.6 ha, shares sum to 1.000, no check findings; keep the slivers. **Decisions needed:** the primary field is dominantly 'Poorly drained', so the demo will fire `applicability_alfalfa_drainage`, a rule resting on an unsourced claim; and 'dominant' there is 47 %, not a majority. |
| 2 | ClickHouse skeleton + lineage | Not started | | | | |
| 3 | Field validation + crop history | Not started | | | | |
| 4 — DS2: climate + soil indicators | Soil + climate indicators | In progress | ds2 | [climate](features/2026-11-14-ds2-climate-indicators/), [ssurgo](features/2026-11-14-ds2-ssurgo-aggregation/) | 2026-11-14 | Indicator module built and tested ahead of the data: 8 POWER indicators (GDD, heat days, frost window, longest dry spell, dry-spell count, precipitation total, mean temperature, FAO-56 reference ET) as pure functions in `transform/indicators/climate.py`, 34 tests pass including the hand-computed GDD golden season (36.0 degree-days C), each with a lineage row stating grid scale (~50 km, not field). Missing data returns null with status 'unknown'; a null day never counts as zero and breaks a dry spell. **Open:** reference ET is not independently validated (no FAO-56 worked-example cross-check) and all thresholds are team-proposed, not expert-reviewed. Not run against real POWER data: Phase 1 has not landed, so the tests use synthetic frames matching `docs/sources/ds2-power-ssurgo-marsden.md`. SSURGO aggregation added: three weighting stages (horizon thickness, comppct_r, area_share) with 31 tests, hand-computed chain = 2.48 % OM over 0-30 cm, available water storage in cm, and categorical drainage and hydrologic-group shares that keep dual values such as B/D verbatim. A null area_share returns 'unknown' rather than assuming equal weights; components with no horizons stay in the denominator. **Open:** no expert review of the depth intervals or the 75 % coverage threshold; texture is not re-normalised by design. 89 tests pass across `transform/`. |
| 4 — DE: extract and clean | Soil + climate indicators | Not started | | | | Owed: POWER and SSURGO extraction and cleaning (-999 to null, per-variable missing-date report, unit checks), the Pandera schema, and the indicator load with lineage rows. Blocked on Phase 1: S3 holds only smoke-test objects and every ClickHouse table is empty as of 2026-11-14. |
| 5 | HLS vegetation and bare-field windows | Not started | | | | |
| 6 — DS2: reproduction | Marsden reproduction | Done | ds2 | [2026-11-14-ds2-marsden-reproduction](features/2026-11-14-ds2-marsden-reproduction/) | 2026-11-14 | Exit check met: 24 tests pass on applied N 74.5 / 56.6 / 40.8 and herbicide 1.925 / 0.261 / 0.195; yields attributed to Davis et al. (2012), not recomputed. The PRD's "total N" is applied N (manufactured + manure) and excludes biological N fixation. One documented strict `xfail`: the paper's text gives 2-yr manufactured N as 80, Table S3 weights to 74.5; isolated to 2011, cause unknown, not corrected. Code `transform/marsden/`, outputs `data/out/marsden/` (gitignored). Raw inputs are not in git — the DE owns copying them to S3. |
| 6 — DE: validate records | Marsden reproduction | Not started | | | | Owed: Pandera schema over the extracted Table S3 / S4 frames (checks are plain Python today), the five raw files to S3 at `raw/marsden/pone.0047149-supplement/2026-11-13/`, and the ClickHouse load of `management_by_year.csv`, `management_summary.csv` and the four `indicator_lineage.json` rows. |
| 7 — FE: web scaffold and home page | Frontend core | In progress | FE | [2026-11-14-fe-web-scaffold-and-home](features/2026-11-14-fe-web-scaffold-and-home/) | 2026-11-14 | Next.js app in `web/` and the landing page. Works against static content only; no API needed. |
| 7 — FE: field selection | Frontend core | In progress | FE | [2026-11-14-fe-field-selection](features/2026-11-14-fe-field-selection/) | 2026-11-14 | Step 1 of the journey: map and list of the 45 demo fields, geometry validation (FR-01). Reads DE's committed GeoJSON; no API needed. Built and checked; keyboard and tile-failure checks still open. |
| 7 — FE: profile, evidence drawer | Frontend core | In progress | FE | [2026-11-14-fe-field-profile](features/2026-11-14-fe-field-profile/) | 2026-11-14 | Step 2: real crop history and soil from committed data; weather and greenness are labelled sample values until Phases 4 and 5 and the API exist. Proposes the `FieldProfile` contract for BE. |
| 8 | Day-1 checkpoint | Not started | | | | |
| 9 | Strategy profiles + applicability rules | Done | ds2 | [2026-11-14-ds2-strategy-rules](features/2026-11-14-ds2-strategy-rules/) | 2026-11-14 | Exit check met: rule table written, versioned `2026-11-14.2` and reviewable at `docs/rules/strategy-profiles-and-applicability.md`, generated from `engine/rules/strategy_rules.py` with a test that fails if the two drift. 3 strategy profiles, 9 outcomes (soil carbon, erosion and nitrate leaching present but `claimable=False`), 8 crop claims, 16 applicability rules (3 added in Phase 10 for unstated operational constraints), each naming one outcome so no-manure limits the N comparison without touching herbicide (PRD 7.6). 37 tests. **Open and important:** nothing is expert-reviewed (no Iowa adviser approached); 7 of 8 crop claims are `research_needed` because no agronomic source was available, so the "why this crop" explanation is thin; 2 rules rest on those unsourced claims and must be withdrawn if no source is found; the GDD climate-distance band has no published basis. Expert review is the remaining work for this phase. |
| 10 — DS2: engine logic | Decision engine | Done | ds2 | [2026-11-14-ds2-decision-engine](features/2026-11-14-ds2-decision-engine/) | 2026-11-14 | `engine/decision.py`: `assess(profile, constraints) -> Decision`, pure and deterministic, returning one of the three PRD 8.3 outcomes with per-outcome and per-strategy findings traceable to rule ids. 31 tests cover the four required categories. No score, no ranking, no winner. Unknown is a sentinel distinct from False, so an unstated constraint qualifies or abstains instead of passing. Forbidden outcomes stay `not_assessed`. **Built without DS1** (deadline; BE and FE were blocked on the output shape) — the context keys and the `Decision` dataclass need joint review. Never run on a real profile: no indicator data exists yet. Farmer priorities are recorded but not acted on, pending a weighting decision. |
| 10 — BE: /compare endpoint | Decision engine | Not started | | | | Owed: wrap `engine.decision.assess` in `POST /fields/{id}/compare` and serialise the dataclasses. PRD 8.4 wants the indicators and lineage alongside the result; the API assembles those around it. |
| 11 — FE: comparison UI | Comparison UI + constraints form | In progress | FE | [2026-11-14-fe-comparison-ui](features/2026-11-14-fe-comparison-ui/) | 2026-11-14 | Step 4: renders DS2's `Decision` (outcome banner, three strategies, nine outcomes, open questions). Uses a TypeScript port of the engine, tested equal to `engine/decision.py`, until BE ships `POST /compare`. Abstains for every field today because no required indicator is computed; an optional sample-value preview shows the other outcomes. |
| 11 — FE: constraints form | Comparison UI + constraints form | In progress | FE | [2026-11-14-fe-priorities-form](features/2026-11-14-fe-priorities-form/) | 2026-11-14 | Step 3 of the journey: priorities and constraints, mapped to the four context keys DS2's applicability rules read (unanswered = unknown). Works against DS2's Phase 9 rules; Phase 10 engine not needed yet. |
| 11 — FE: adviser summary (step 5) | Comparison UI + constraints form | In progress | FE | [2026-11-14-fe-adviser-summary](features/2026-11-14-fe-adviser-summary/) | 2026-11-14 | Printable one-page brief for an adviser: result, options, answers, derived questions to ask, evidence sources. Reads the same `Decision` as the comparison; no new logic. |
| 12 | P1 data layers | Not started | | | | |
| 13 | P1 UI: map, timelines, scenario polish | Not started | | | | |
| 14 | Validation and feedback | Not started | | | | |
| 14 — FE: validation page | Validation and feedback | In progress | FE | [2026-11-14-fe-validation-page](features/2026-11-14-fe-validation-page/) | 2026-11-14 | `/validation`: the nine PRD §11 components against four kinds of evidence (internal test, agreement with another source, independent reference, expert review), sourced to the specs and dated. Hand-maintained snapshot: update it when a Phase 14 result lands. |
| 15 | Claim check and slide-deck prep | Not started | | | | |

---

## Day 1 — Foundation, data and P0 analytics

### Phase 0 — Align and set up (first ~1 h, whole team)
- Agree the fields. All are polygons in Story or Boone County, Iowa, drawn by the team and clearly labelled as demonstration geometry, not real farm boundaries. **F** is not an Iowa farmer, so no real boundary is expected. If one becomes available later (e.g. from an Iowa adviser), swap it in and record its provenance.
  - **One primary demo field:** a typical maize–soybean parcel (check the CDL rotation history), used as the worked example in the slide deck and checked by hand.
  - **A test set of ~30–50 fields (minimum ~30):** spread across both counties and soil types, used for development, validation and engine tests. Include some deliberately out-of-domain fields (e.g. continuous corn, pasture or non-rotation histories) to exercise abstention, with at least several fields per class you report on. Two people drawing in parallel keeps this feasible.
  - Store them as GeoJSON with `field_id`, `role` (`primary` or `test`), `boundary_source`, county and provenance properties.
- Create the repo, folder layout, `.env` handling and the shared S3 bucket; **DE** starts local ClickHouse.
- **BE + FE** agree the API contract (OpenAPI draft) and the evidence-type / unknown conventions.
- *Exit:* everyone can run the repo; the primary demo field and the test-set polygons are committed as GeoJSON with their provenance recorded.

### Phase 1 — Raw data into S3 (DE extracts; DS1, DS2 specify and review)
- **DS1/DS2** first write the source requirements sheet for each P0 source: which bands, variables, years and seasons, which quality flags and masks matter, and what a correct file looks like. Split: **DS1** covers HLS and CDL; **DS2** covers NASA POWER, SSURGO and the Marsden files. **DE** implements the extraction from the sheet, and a DS reviews the first pull of each source.
- While the sheets are being written, **DE** sets up the S3 layout and the manifest/checksum tooling, then extracts each source as its sheet is ready.
- **DE** pulls the **P0 sources** into `raw/`: CDL, SSURGO, NASA POWER, Marsden supplementary files, and a bounded HLS sample (bboxes of the primary and test fields × 2–3 seasons).
- Before pulling, write down the subset (per-field bbox + buffer, or one bbox covering all fields; growing-season windows; seasons) and a size budget that scales with the number of fields. For HLS, filter by tile, date and cloud cover, fetch only the needed bands, and use windowed COG reads. **DE** builds a one-field, one-season sample dataset (from the primary field) for dev and tests.
- Write a manifest beside each raw file (URL, version, retrieval date, SHA-256, size, licence) and verify the checksum after upload. Confirm each file opens and its bbox/CRS/date range match the request.
- *Exit:* each source has its raw files in S3 with a manifest and a verified checksum.

### Phase 2 — ClickHouse skeleton + lineage (DE; BE in parallel)
- Create the `data_sources`, `indicator_lineage`, `fields` and evidence-type tables, as plain `MergeTree` tables with typed columns, an evidence-type `Enum` and a `load_id` column. Make loads idempotent by loading into a staging table and running `REPLACE PARTITION`.
- Tune for size: `ORDER BY (field_id, indicator, date)` and a coarse `PARTITION BY`, compact types and codecs, and batch loads from Parquet in S3 (never row-by-row inserts).
- Set up the shared Pandera schema module and a `make check` stub (schema checks, post-load assertions, `pytest`).
- **BE** scaffolds FastAPI with stub endpoints returning mock data that matches the contract.
- *Exit:* tables exist; `make check` runs; the API returns the mock profile; FE can start building against it.

### Phase 3 — Field validation + crop history (DE builds; DS1 sets rules and reviews; BE serves)
- **DE** runs polygon validation and sets the real-vs-demo flag and the `primary`/`test` role for every field. Check that each polygon is valid, non-empty and inside Story or Boone County.
- **DE** extracts and clips CDL to the field polygons for every year, recording the product version and resolution (30 m → 10 m change from 2024).
- **DS1** first writes a short rules spec: the class-code groups, the dominant-crop threshold (below it a year is `mixed/uncertain`), and the rotation rule (e.g. corn and soybeans alternating in at least N of the last M years). The rules are versioned, and they feed the Phase 9 rule table.
- **DE** implements the spec: class shares per field per year, the dominant crop, the crop sequence and the rotation flag, each tagged with the rule version.
- **DS1** reviews the output: a hand-check of the primary field and a sample of test fields, plus any fields flagged `mixed/uncertain` or with an unexpected rotation flag.
- **DE** validates the summary with Pandera before loading it into ClickHouse. **BE** serves it through the API.
- *Exit:* the crop-history table for the primary and test fields passes schema checks, is loaded in ClickHouse and is served by the API.

### Phase 4 — Soil + climate indicators (DE extracts and cleans; DS2 builds indicators)
- **DE** extracts and cleans SSURGO and POWER (units, fill values, gaps, schema checks). **DS2** engineers the indicators.
- SSURGO map-unit/component properties with survey caveats. POWER temperature and precipitation indicators (e.g. GDD, heat days, dry spells, seasonal totals), each with units, window and scale.
- **DE** validates with Pandera before loading (units, ranges, required fields), converts POWER fill values (e.g. −999) to null and reports gaps in the daily series. **DS2** adds a golden-file test for one hand-computed indicator (e.g. GDD for one season).
- *Exit:* indicators loaded with lineage rows and passing schema checks. Each states its scale (grid, not field).

### Phase 5 — HLS vegetation and bare-field windows (DE prepares; DS1 features)
- **DE** delivers analysis-ready HLS: clipped to the field bboxes, reprojected, with the DS-specified quality mask (`Fmask`) applied. **DS1** engineers NDVI series, bare-field windows and the HLS-versus-CDL test on top of it.
- Process lazily in dask chunks, per scene and resumable (skip scenes whose output exists). **DS1** computes zonal stats per field per date and loads those rows, not pixels.
- **DS1** computes NDVI time series, valid-observation counts and gaps, and bare-field windows (unknown when under-sampled) from the masked data.
- Test across the test set whether HLS adds anything beyond CDL (not just on the primary field); keep or drop it explicitly.
- Enforce the integrity rules: valid-observation counts are always present, and under-sampled periods are labelled `unknown`, never classified. Add tests for both.
- *Exit:* HLS features loaded with denominators and passing checks, or a documented decision to drop them.

### Phase 6 — Marsden reproduction (DE validates; DS2 reproduces)
- **DE** validates the supplementary records with Pandera (units, ranges, required fields) before they are used.
- **DS2** reproduces the rotation-area-weighted nine-year management averages from the supplementary records and reconcile with the paper.
- *Exit:* a test passes on 74.5 / 56.6 / 40.8 kg N/ha/yr total N and 1.925 / 0.261 / 0.195 kg/ha/yr herbicide; yield claims are attributed to the paper, not recomputed.

### Phase 7 — Frontend core (FE, in parallel from Phase 2)
- Field select/upload on a map, profile dashboard shell, evidence/provenance drawer, "unknown / not assessed" components, all on API data.
- *Exit:* the profile screen renders real crop-history, soil and climate data end to end.

### Phase 8 — Day-1 checkpoint (whole team, ~30 min)
- Demo the data → API → UI path for one field. Re-cut P1 scope if behind.
- **F** reviews the profile for agronomic sense and flags missing constraints.

---

## Day 2 — Decision engine, P1, validation, demo

### Phase 9 — Strategy profiles + applicability rules (DS2; expert review if reachable; F sanity check)
- Define the three strategy profiles (2-yr, 3-yr oat/red clover, 4-yr oat/alfalfa), crop characteristics with sources (marked "research needed" if unsourced), and outcome-specific transferability rules.
- **F** is not an Iowa farmer, so seek review from an Iowa-knowledgeable agricultural expert or adviser (e.g. university extension) if one is reachable. **F** can sanity-check practicality (machinery, labour, markets). Rules without expert review are labelled "not expert-reviewed".
- *Exit:* a rule table is written, versioned and reviewable.

### Phase 10 — Decision engine (DS2 + DS1 build; BE integrates)
- **DS** own the engine logic and its tests. **BE** wraps it in the `/compare` endpoint.
- A deterministic engine that takes the profile, evidence and farmer constraints and returns worth exploring / qualified comparison / abstention, with trade-offs and unknowns.
- Unit tests for in-domain, out-of-domain, missing-data and abstention cases.
- *Exit:* tests pass. The `/compare` endpoint returns the structured result.

### Phase 11 — Comparison UI + constraints form (FE)
- Constraints/priorities form (water, manure, machinery, market/use), side-by-side scenario view, benefits, trade-offs, evidence gaps and the outcome banner.
- *Exit:* the full core journey works for the demo field. This is the **P0 complete** milestone.

### Phase 12 — P1 data layers (DE extracts; DS1, DS2 assess and engineer)
- **DE** extracts and cleans each layer. **DS** write the requirements sheet for each, decide whether it adds value, and build any features.
- NASS county context, AMS market context for oats/red clover/alfalfa, NAIP reference imagery, PRISM vs POWER comparison, SMAP/GPM regional context (with their scale caveats). Erosion susceptibility only if a defensible method is ready; otherwise mark it "not assessed".
- Apply the Phase 1 subset rules: request by bbox or county only, set a size budget per layer, and store regional values (SMAP/GPM) or reference tiles (NAIP) rather than full rasters in ClickHouse.
- **DE** writes manifests, validates with Pandera and adds lineage rows before loading, as for the P0 layers.
- *Exit:* each layer is in ClickHouse with lineage and passing checks, or explicitly marked dropped with a reason.

### Phase 13 — P1 UI: map, timelines, scenario polish (FE + BE)
- Interactive map with layers, climate/NDVI timelines with valid-observation markers, NAIP/NASS/AMS context panels, side-by-side polish.
- Keep it fast: serve pre-aggregated, paginated data, downsample long time series, cache stable responses, and use tiled COG/vector-tile layers rather than raw rasters or large GeoJSON.
- *Exit:* P1 views are visible in the app and read from the API.

### Phase 14 — Validation and feedback (DS1, DS2, F)
- CDL confusion matrix and class metrics across the test set, with correct terminology. Without an independent reference, this is agreement with another classification, not validation. Report both the number of fields and the number of field-years, and do not treat field-years as independent samples (pixels within a field are correlated). With ~30–50 fields, results are **indicative, not statistically strong**: give counts, avoid precise percentages or significance claims, and say so in the validation summary. Run the decision engine over the whole test set and check that in-domain, qualified and abstention outcomes match expectations. PRISM/POWER sanity check. **F** (and any adviser reachable) walks through the app; capture notes and the resulting changes. **F** is a Nigerian farmer, not an Iowa user, so their feedback covers usability and general agronomic sense, not Iowa-specific validation. State this plainly, and acknowledge the Iowa stakeholder-feedback gap (no adoption or Local Impact claims without evidence).
- *Exit:* a validation summary and a feedback log exist.

### Phase 15 — Claim check and slide-deck prep (whole team)
- Walk the Definition of Done checklist (PRD §16). Remove or reword unsupported claims. Prepare the data-lineage diagram, architecture diagram, scientific-method one-pager, and the **7-slide deck** (PRD §13; the submission is slides, not a video).
- Run `make check` (schema checks, post-load assertions such as no indicator without a lineage row, `pytest`). Rerun the pipeline on the same raw files and confirm identical table hashes. Record the run manifest (git SHA, input checksums, config).
- Capture real screenshots from the running app on the ClickHouse + S3 data (no live retrieval, no mock-ups) for the slides, and rehearse presenting the deck twice.
- *Exit:* `make check` passes, the app runs end to end, the 7-slide deck is complete and every claim is evidenced.

---

## Cut order if time runs short
1. Erosion susceptibility (already conditional)
2. SMAP/GPM context
3. PRISM comparison
4. AMS market context (keep NASS)
5. NAIP
6. Never cut: provenance, uncertainty/abstention, Marsden reproduction, the three-strategy comparison.

## Parallel track summary

| Block | DE | DS1 | DS2 | BE | FE | F |
|---|---|---|---|---|---|---|
| D1 start | S3 layout, manifest tooling, ClickHouse; then extract P0 sources as sheets arrive | Source requirements sheet (HLS, CDL) | Source requirements sheet (POWER, SSURGO, Marsden) | API scaffold | Map/UI shell | Field + constraints |
| D1 mid | Clean and load analysis-ready tables | CDL features, HLS features | Soil/climate indicators, Marsden | Profile endpoints | Profile screen | Review profile |
| D2 start | P1 extraction | Engine logic, P1 assessment | Rules + engine | Engine endpoint | Comparison UI | Rules sanity check (practicality) |
| D2 end | Lineage QA | Validation | Method write-up | Hardening | Polish | Feedback + demo |