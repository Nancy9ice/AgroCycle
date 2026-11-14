# AgroCycle — Mission

Source of truth for detail: `PRD.md`. This file is the short constitution the team works from during the 2-day hackathon.

## Mission

Help farmers and agricultural advisers explore crop-rotation strategies that could improve soil health and resilience to changing weather and water conditions, by connecting NASA Earth observations with local agricultural evidence and farmer priorities. We prioritise transparent trade-offs, scientific defensibility and honest uncertainty over the number of datasets or features shown.

**Challenge:** NASA Space Apps 2026 — "Field Shift: Adapting Farms with NASA Data".

## Who it is for

- Farmers exploring rotation options.
- Agricultural advisers / extension professionals.

## The decision we support

> Given a field under maize–soybean rotation in Story or Boone County, Iowa, what do the available environmental, soil, crop and experimental evidence say about the existing system versus two diversified alternatives, including benefits, trade-offs, operational requirements and evidence gaps?

| Strategy | Rotation |
|---|---|
| A — Existing | 2-year maize–soybean |
| B — Diversified | 3-year, with oat and red clover phases |
| C — Diversified | 4-year, with oat and alfalfa phases |

This is a bounded pilot, not a universal crop-selection system.

## Scope for the 2 days: MVP = P0 + P1

**P0 (build first, the analytical and decision core)**
- Field polygon input and validation. Demo polygons are clearly labelled: one primary demo field for the story, plus a test set of ~30–50 fields in Story/Boone for validation and engine tests
- CDL crop history; SSURGO soil; NASA POWER climate indicators
- Bounded HLS sample for seasonal vegetation and bare-field windows (kept only if it adds value beyond CDL)
- Field environmental profile that separates field-, grid- and regional-scale data
- Marsden Farm records: reproduce the documented management comparisons
- Three-strategy comparison with trade-offs, farmer priorities and constraints
- Evidence matching, uncertainty reporting, qualified comparison or abstention, and provenance

**P1 (in MVP, built once P0 works)**
- Interactive map, timelines and side-by-side scenario comparison
- NAIP imagery for field inspection
- NASS QuickStats for county context
- AMS Market News for alternative-crop market context
- PRISM vs POWER comparison
- SMAP / GPM regional context
- Terrain-derived erosion susceptibility, only if a defensible method exists
- Farmer / adviser feedback

**P2 (stretch, only if time remains):** CoCoRaHS, ECOSTRESS, other NASA datasets, other regions.

## Principles (non-negotiable)

1. **Decision support, not an autonomous agronomist.** The engine may return a *strategy worth exploring*, a *qualified comparison* or an *abstention*. It never has to force a ranking.
2. **Deterministic and traceable.** Calculations and decision rules are documented and testable. AI may help explain outputs but must never invent evidence or agronomic conclusions.
3. **Label the evidence type** on every material output: observed product, derived indicator, classified output, survey information, model/reanalysis, experimental record, published finding, or assumption/user input.
4. **Respect scale.** Never imply field-level measurement from a coarser product. Satellite data does not directly measure soil health. NDVI is not yield. LST is not air temperature.
5. **Unknown is not neutral.** Unsupported dimensions are shown as "unknown / not assessed", never silently omitted or treated as favourable.
6. **No overclaiming.** No guaranteed yield, profit, soil-carbon, erosion or nitrate outcomes. CDL agreement is agreement with another classification, not independent validation. Marsden results are not universal predictions.
7. **Farmer constraints are first-class inputs** (water, manure, machinery, market/use), not footnotes.
8. **Avoid composite scores** unless components, weights and sensitivity are explicit.

## Definition of success

- A user can go end to end: select a field, view the profile, compare the three strategies against their priorities, and see benefits, trade-offs, uncertainties and a qualified outcome or abstention.
- NASA data visibly and materially informs the analysis, rather than decorating the map.
- Marsden management calculations reproduce from the source records (e.g. total N 74.5 / 56.6 / 40.8 kg/ha/yr).
- Every competition claim is backed by evidence, and stakeholder engagement is documented or the gap acknowledged.

## Award targets (internal strategy, not the official rubric)

Best Use of Data · Best Use of Science · Best Use of Technology · Local Impact

## Team and roles

| Role | Primary focus |
|---|---|
| Data engineer | Extraction of all sources and basic transformation (clip, reproject, standardise, apply given quality masks, clean, schema checks), the S3 raw store, the ClickHouse load and lineage |
| Data scientist 1 | Source requirements for HLS/CDL, feature engineering (crop sequences, NDVI, bare-field windows), HLS-vs-CDL test, validation, decision engine logic |
| Data scientist 2 | Source requirements for POWER/SSURGO/Marsden, climate/soil indicators, Marsden reproduction, applicability rules, decision engine logic |
| Backend engineer | API, wrapping the DS-built decision engine, provenance output |
| Frontend engineer | Map, profile, comparison UI, constraint inputs |
| Farmer (Nigerian, not an Iowa user) | Practical farming reality check, usability and constraints feedback, demo credibility. Does not supply the Iowa field boundary or validate Iowa-specific outcomes. |

## Out of scope

Yield or profit guarantees, field-level yield prediction, claims of measured soil-carbon / erosion / nitrate outcomes, recommendations outside the evidence domain, claims of adoption or realised impact, and a single opaque score.
