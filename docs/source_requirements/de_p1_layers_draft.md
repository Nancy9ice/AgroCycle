# P1 Layers: Source Requirements Sheet (DE draft, pending DS sign-off)

For: DS1 and DS2 to approve · From: DE · Status: **draft v1, 2026-11-15. Not signed off.**
Why a DE draft: DS1 and DS2 are busy, and Phase 12 says the DS write one sheet per layer. The DE drafted them from the PRD (section 4.2, 6, 10 and the S11-S17 entries). Nothing here is a science decision until a DS confirms it.

## 0. How to sign off (one chat message per layer is enough)

For each layer a DS replies **approve**, **change X**, or **drop**. The DE records the reply in the tracker with the date and who sent it (relayed replies are labelled as relayed).

- **Approved:** the DE builds the layer (dry run, size check, then `--execute` on Nancy's say-so).
- **No reply:** the DE does a dry-run size check only. Nothing goes to S3 or ClickHouse. The tracker says "no sign-off".
- **Drop:** the tracker says dropped, with the DS's reason.

Who is asked: **DS2** for NASS, AMS, PRISM (climate and market context); **DS1** for NAIP (imagery vs CDL); **either** for SMAP/GPM.

Rules for every layer (same as the P0 sources): raw files verbatim in `raw/<source>/<version>/<retrieval-date>/` with a manifest (URL or full query, version, retrieval time, SHA-256, size, licence); a missing value stays null; source units kept; pin the retrieval date and do not re-pull; request by bbox or county only; a lineage row and a `data_sources` row for every output; Pandera check before load.

| Layer | Owner to sign off | Evidence type | Scale | Priority | Size budget (proposal) |
|---|---|---|---|---|---|
| 1. NASS QuickStats [S12] | DS2 | survey (published statistics) | county, not field | P1 | < 5 MB |
| 2. AMS Market News [S13] | DS2 | published (market report) | market, not farm | P1 | < 20 MB |
| 3. PRISM vs POWER [S14] | DS2 | model/reanalysis (gridded) | 4 km grid | P1 | < 200 MB |
| 4. NAIP [S11] | DS1 | observed imagery | 0.6 to 1 m, one flight date | P1 | < 100 MB (about 2 MB per field) |
| 5. SMAP / GPM [S16, S17] | DS2 or DS1 | model/retrieval | 9 to 10 km | P1 in roadmap, P2 in PRD table | < 50 MB (values, not rasters) |
| Erosion susceptibility | n/a | n/a | n/a | conditional | **Not assessed** (decision 2026-11-15: no defensible method is ready) |

## 1. NASS QuickStats (county context)

**Role:** county acreage, yield and production for context. Never field-level yield validation (PRD, FR for S12).
**What to fetch:** QuickStats API (`https://quickstats.nass.usda.gov/api/`, free key from NASS, kept outside the repo). `agg_level_desc=COUNTY`, `state_alpha=IA`, counties **Story and Boone**, `source_desc=SURVEY`.
- Commodities: CORN, SOYBEANS, OATS, HAY (the alfalfa line is under HAY, class ALFALFA).
- Statistics: AREA PLANTED, AREA HARVESTED, YIELD, PRODUCTION.
- Years: 2003-2025, to cover the Marsden window, the CDL years and recent seasons.
- Keep the source row as returned (`short_desc`, `unit_desc`, `Value`, `year`, `reference_period_desc`, `freq_desc`).
**Masks and rules:** values like `(D)` (withheld) and `(Z)` become null with a `suppressed` flag. Strip thousands commas. Units stay as given (BU / ACRE, ACRES, TONS).
**Expected limits:** red clover has no county line; oats and alfalfa county lines may be thin or withheld. Report which cells are empty. Do not fill them.
**Output table:** `county_stats` (county_fips, year, commodity, statistic, unit, value, suppressed).
**DS decision needed:** which commodities and years to keep.

## 2. AMS Market News (alternative-crop market context)

**Role:** prices and availability for oats, red clover and alfalfa, shown as context with commodity, location, date, unit and report type.
**What to fetch:** USDA AMS Market News reports (MARS API, `https://marsapi.ams.usda.gov/`, key if required, kept outside the repo) for Iowa or the nearest regional hay and grain reports.
**Unverified (the PRD says "report coverage needs checking"):** which report IDs cover oats, alfalfa hay and red clover seed, and how far back they go. The DE's first task is a **coverage check** (list candidate reports, their commodity, region, frequency and date range) and a DS picks the reports from that list. The DE does not choose report IDs by guess.
**Masks and rules:** keep the report's own unit and quality grade; keep price low and high as separate columns; no averaging across reports.
**Output table:** `market_prices` (report_id, report_type, commodity, region, date, unit, grade, price_low, price_high).
**DS decision needed:** which reports, and how many years back.

## 3. PRISM vs POWER (does PRISM add local detail?)

**Role:** a comparison only. PRISM is kept only if it adds useful local climate detail over POWER (PRD S14).
**What to fetch:** PRISM 4 km daily `ppt`, `tmax`, `tmin` (the PRISM web service rate-limits; do not request the same file twice a day), sampled at the same points as POWER (the `field_id -> point_id` map, plus the Marsden site).
**Subset proposal (size budget):** monthly 1991-2025 for the long comparison, plus daily for the 2023-2025 growing seasons (Apr 1 - Oct 31) for the daily comparison. Not daily for 35 years (about 38,000 files).
**Masks and rules:** PRISM units are mm and °C. Same fill-to-null rule. Record the PRISM data stability (provisional, early or stable) per month.
**Output table:** `prism_daily` / `prism_monthly` (point_id, date, variable, value, stability).
**Comparison (DS2 owns the verdict):** per point and variable, the DE reports the difference series and summary (bias, correlation, missing days). DS2 decides keep or drop.
**Expected result to be honest about:** the whole area has few unique POWER cells, so PRISM may only show that POWER is coarse. That is a valid finding.

## 4. NAIP (reference imagery for field inspection)

**Role:** visual reference for boundary and field inspection. It is not crop ground truth (PRD S11).
**Unverified (the PRD says "Iowa coverage and use need verification"):** the latest Iowa NAIP year and access route (Planetary Computer STAC `naip` collection or USDA APFO). The DE's first task is to confirm coverage and year for Story and Boone.
**What to fetch:** the latest Iowa NAIP scene(s) covering the 45 fields, clipped to each field bbox plus a small buffer, saved as one small COG per field. Never the full tiles.
**Masks and rules:** record flight date, resolution, bands (RGB, NIR), and CRS in the manifest. One date only, so the page must say "one date, not a time series".
**Output:** `raw/naip/...` chips and a `naip_tiles` table (field_id, flight_date, resolution_m, s3_key, bbox, bands).
**DS1 decision needed:** is a single-date chip useful for her checks, and which buffer.

## 5. SMAP and GPM (regional context)

**Role:** regional soil-moisture and precipitation context only. SMAP footprints are kilometres wide, so they say nothing about moisture in one field (PRD S16). GPM IMERG is a satellite precipitation product, not a rain gauge (S17).
**What to fetch (products and versions to confirm before pulling):** SMAP 9 km soil moisture (L3 enhanced or L4 root-zone) and GPM IMERG Final daily, via Earthdata (the login the DE already uses). Pull by bbox over Story and Boone, growing seasons 2023-2025.
**What to store:** the value in the cell over each unique field centroid, with the cell id and size, not rasters. Keep SMAP quality and retrieval flags; keep the IMERG precipitation quality index.
**Output table:** `regional_context` (cell_id, product, version, date, variable, value, unit, cell_size_km, qc_flag).
**DS decision needed:** include or drop. If included, DS2 writes the wording that stops it being read as field-scale.

## 6. Erosion susceptibility

Marked **not assessed** (decision 2026-11-15, DE with Nancy). A defensible method needs DEM slope and length, soil erodibility (SSURGO K-factor) and rainfall erosivity, with a validated method. Not ready. If a DS wants it, say so and the DE will draft a method sheet.
