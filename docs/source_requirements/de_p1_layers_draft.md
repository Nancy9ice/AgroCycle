# P1 Layers: Source Requirements Sheet (DE draft, pending DS sign-off)

For: DS1 and DS2 to approve · From: DE · Status: **draft v1, 2026-11-15. Not signed off.**
Why a DE draft: DS1 and DS2 are busy, and Phase 12 says the DS write one sheet per layer. The DE drafted them from the PRD (section 4.2, 6, 10 and the S11 to S13 entries). Nothing here is a science decision until a DS confirms it.

## 0. How to sign off (one chat message per layer is enough)

For each layer a DS replies **approve**, **change X**, or **drop**. The DE records the reply in the tracker with the date and who sent it (relayed replies are labelled as relayed).

- **Approved:** the DE builds the layer (dry run, size check, then `--execute` on Nancy's say-so).
- **No reply:** the DE does a dry-run size check only. Nothing goes to S3 or ClickHouse. The tracker says "no sign-off".
- **Drop:** the tracker says dropped, with the DS's reason.

Who is asked: **DS2** for NASS and AMS (county and market context); **DS1** for NAIP (imagery vs CDL).

Rules for every layer (same as the P0 sources): raw files verbatim in `raw/<source>/<version>/<retrieval-date>/` with a manifest (URL or full query, version, retrieval time, SHA-256, size, licence); a missing value stays null; source units kept; pin the retrieval date and do not re-pull; request by bbox or county only; a lineage row and a `data_sources` row for every output; Pandera check before load.

| Layer | Owner to sign off | Evidence type | Scale | Priority | Size budget (proposal) |
|---|---|---|---|---|---|
| 1. NASS QuickStats [S12] | DS2 | survey (published statistics) | county, not field | P1 | < 5 MB |
| 2. AMS Market News [S13] | DS2 | published (market report) | market, not farm | P1 | < 20 MB |
| 3. NAIP [S11] | DS1 | observed imagery | 0.6 to 1 m, one flight date | P1 | < 100 MB (about 2 MB per field) |
| PRISM, SMAP/GPM, erosion | n/a | n/a | n/a | n/a | **Not in Phase 12** (section 4) |

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

## 3. NAIP (reference imagery for field inspection)

**Role:** visual reference for boundary and field inspection. It is not crop ground truth (PRD S11).
**Checked 2026-11-15:** Microsoft Planetary Computer's `naip` collection holds Iowa NAIP for 2015, 2017, 2019, 2021, 2023 and 2025 (0.3 to 1.0 m, four bands: red, green, blue, near-infrared, cloud-optimised GeoTIFF). The download token is anonymous. The catalogue gives **no licence text**, so the licence is recorded as unconfirmed.
**What to fetch:** the latest Iowa NAIP scene(s) covering the 45 fields, clipped to each field bbox plus a small buffer, saved as one small COG per field. Never the full tiles.
**Masks and rules:** record flight date, resolution, bands (RGB, NIR), and CRS in the manifest. One date only, so the page must say "one date, not a time series".
**Output:** `raw/naip/...` chips and a `naip_tiles` table (field_id, flight_date, resolution_m, s3_key, bbox, bands).
**Done (DE, on Nancy's go, 2026-11-15):** the 2025 chips for all 45 fields are in `raw/naip/naip-2025/2026-11-15/` (45 images + 45 manifests, 84.6 MB, 50 m buffer). The 2025 flights span 5 August to 26 September, so each manifest carries its own flight date(s); three fields (test-032, -041, -044) are cut from two tiles.
**DS1 decision needed:** is a single-date late-summer chip useful for her checks (boundary alignment of our CDL-derived polygons against real field edges)? FE: will the map use it as a toggle or basemap? Until one of them says yes, nothing else is built on it (no `naip_tiles` table yet).

## 4. Not in scope: PRISM, SMAP/GPM, erosion

Decision 2026-11-15 (Nancy, with the DE): Phase 12 is narrowed to NASS, AMS and NAIP.
- **PRISM vs POWER:** dropped. Low value for the farmer; it would only show how coarse POWER is. A DS can ask for it back (a monthly comparison, under 200 MB).
- **SMAP/GPM:** dropped. 9 to 10 km products say nothing about one field, the PRD table lists them as P2, and they are the heaviest pull for the weakest claim.
- **Erosion susceptibility:** not assessed. A defensible method needs DEM slope and length, the SSURGO K-factor and rainfall erosivity, with a validated method, and none is ready. If a DS wants it, the DE drafts a method sheet.
