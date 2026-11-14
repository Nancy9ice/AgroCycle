# DS2 Source Requirements Sheet: POWER, SSURGO, Marsden

For: Data Engineer (roadmap Phase 1) · From: DS2 · Status: draft v1, 14 Nov 2026
Scope: the three sources DS2 owns. HLS and CDL are in DS1's sheet.

## 0. Read this first

| Source | What the DE does | Effort | Priority |
| --- | --- | --- | --- |
| **Marsden** | **Nothing to extract.** Raw files, manifest and cleaned tables already exist in `transform/marsden/` and `data/` (section 3). Copy to S3, verify checksums, load. | ~15 min | Do first (zero risk) |
| **NASA POWER** | Daily point pull for every field plus the Marsden site (section 1) | ~1 h | 2nd |
| **SSURGO** | Soil Data Access queries per field polygon (section 2) | ~2 h | 3rd |

Rules that apply to every source:

- Keep raw files **verbatim** in S3 (`raw/<source>/<version>/<retrieval-date>/`) and write the manifest (URL or full query, version, retrieval timestamp, SHA-256, size, licence).
- A missing value stays **null**. Never fill with 0, a mean, or a neighbour. "Unknown is not neutral."
- Keep source units. State the unit in the column name or the schema. Do not convert unless this sheet says so.
- If a variable, column or table name is rejected by the service, **drop it and tell DS2**. Do not guess a substitute.
- Do not re-pull the same source between runs (POWER data can be reprocessed, so a later pull may differ). Pin the retrieval date.
- DS2 reviews the first pull of each source (section 4) before the full run.

## 1. NASA POWER (daily meteorology, gridded)

**Role:** climate indicators (growing degree days, heat days, frost, dry spells, seasonal totals, reference ET). Evidence type: `model_reanalysis`. Scale: **grid (roughly 50 km), not field.**

**What to fetch**

- Endpoint: POWER daily point API (`/api/temporal/daily/point`), `community=AG`, `format=JSON`. Leave `time-standard` at its default and use the same setting for every point.
- Points: the centroid of every field in `fields.geojson` **plus the Marsden site (42.0167 N, -93.7833 W; Text S1)**. POWER snaps to its grid, so record the coordinates it returns, dedupe fields that return the same cell, and keep a `field_id -> point_id` mapping. Expect only a few unique cells, so this is a handful of requests, not dozens.
- Period: **1991-01-01 to 2025-12-31** (whole calendar years, not just the growing season). This covers the 1991-2020 normals, recent years, and the 2003-2011 Marsden window.
- Variables:

| Variable | Meaning | Unit | Needed for |
| --- | --- | --- | --- |
| `T2M_MAX`, `T2M_MIN`, `T2M` | daily max, min, mean air temp at 2 m | °C | GDD, heat days, frost |
| `PRECTOTCORR` | corrected precipitation | mm/day | totals, dry spells |
| `RH2M` | relative humidity at 2 m | % | reference ET |
| `ALLSKY_SFC_SW_DWN` | all-sky downward shortwave radiation | MJ/m²/day (check the header) | reference ET |
| `WS2M` | wind speed at 2 m | m/s | reference ET |
| `GWETROOT`, `GWETTOP` (optional, separate call) | modelled root-zone and top-soil wetness | 0 to 1 | context only |

**Masks and rules to apply**

1. Convert the fill value **-999 to null** (confirm it in the response header).
2. Expected rows per point and variable: **12,784** (35 years, 9 leap years). Report every missing date per variable. Do not interpolate.
3. Hard checks (fail the load): `PRECTOTCORR >= 0`, `ALLSKY_SFC_SW_DWN >= 0`, `WS2M >= 0`, `RH2M` within 0-100.
4. Soft checks (flag, do not drop): `T2M_MIN <= T2M <= T2M_MAX`, temperatures within -50 to 50 °C.
5. Store the response `header` (API version, data sources, fill value, units) in the manifest.

**What a correct file looks like:** JSON with `properties.parameter.<VARIABLE>.<YYYYMMDD>` values, plus a header and the point's coordinates and elevation. Output table `power_daily`: `point_id, lat, lon, date, variable, value, qc_flag`, or wide with one column per variable and units documented.

**Quirks to know**

- A cell is about 0.5° x 0.625° (roughly 50 x 55 km at this latitude), so it is **far bigger than a field**. Two fields in the same cell get identical climate. That is expected and honest; do not "fix" it.
- Precipitation is a corrected reanalysis product, not a rain-gauge reading. Different variables come from different underlying products.
- Data lag: the latest days may be preliminary. Do not extend past 2025-12-31.

**DS2 computes (not the DE):** GDD, heat days, frost dates, dry-spell length, seasonal totals, reference ET. Thresholds are team-proposed and need expert review.

## 2. SSURGO (soil survey, via USDA Soil Data Access)

**Role:** soil profile per field. Evidence type: `survey`. Scale: **mapped soil units, not a lab sample of the field.**

**What to fetch** (per field polygon; WGS84 WKT; check it is valid and inside Story or Boone first)

- Service: Soil Data Access REST (`https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest`, JSON body `{"format":"JSON+COLUMNNAME","query":"..."}`).
- **Step A, map units and areas** (preferred, gives area shares):

  ```sql
  SELECT mp.mukey,
         mp.mupolygongeo.STIntersection(geometry::STGeomFromText('<WKT>', 4326)).STAsText() AS isect_wkt
  FROM mupolygon AS mp
  WHERE mp.mupolygongeo.STIntersects(geometry::STGeomFromText('<WKT>', 4326)) = 1
  ```

  DE computes each intersection's area in an equal-area or UTM CRS and stores the share of the field. **Fallback** if this is rejected: `SELECT DISTINCT mukey FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('<WKT>')`, which returns mukeys only. Then set `area_share = null` and flag `area_unknown`. Do not assume equal weights.
- **Step B, map unit and components:** from `mapunit` (`mukey, musym, muname`) and `component` (`mukey, cokey, compname, comppct_r, majcompflag, slope_r, slopelenusle_r, drainagecl, hydgrp, hydricrating, taxclname, tfact`) for the mukeys from Step A.
- **Step C, horizons:** from `chorizon` for those `cokey`s: `cokey, chkey, hzname, hzdept_r, hzdepb_r, sandtotal_r, silttotal_r, claytotal_r, om_r, ph1to1h2o_r, awc_r, ksat_r, dbthirdbar_r, cec7_r, kffact`.
- **Step D, survey provenance:** survey area version date from `sacatalog` for `IA015` (Boone) and `IA169` (Story), if available.
- One query set per field. Keep results small; no statewide queries.

**Masks and rules to apply**

1. Use **representative values (`_r`) only**. Do not use low/high (`_l`, `_h`) columns.
2. **Do not drop or fill anything.** Keep components with no horizons (water, pits), keep non-major components (`majcompflag`), keep nulls as null. DS2 does the weighting.
3. Keep one row per (field, mukey) with `area_share`, one row per (field, cokey), one row per horizon. Keep all keys (`mukey`, `cokey`, `chkey`).
4. Source units, kept as-is: `om_r`, clay, sand, silt (%), `ph1to1h2o_r` (pH), `awc_r` (cm/cm), `ksat_r` (µm/s), `dbthirdbar_r` (g/cm³), `cec7_r` (meq/100 g), depths (cm), `slope_r` (%).
5. Checks: depths ascending with `hzdept_r < hzdepb_r`; `comppct_r` 0-100; per-map-unit component percentages sum to at most 100; field area shares sum to about 1 (flag if not).

**What a correct result looks like:** a field in Story/Boone typically touches 1-4 map units, each with several components, most with 3-6 horizons. A field with zero map units is a geometry or CRS problem. Stop and tell DS2.

**Quirks to know**

- Component percentages within a map unit describe the map unit, not a spot in the field.
- `hydgrp` can be dual (for example `B/D`: drained / undrained). Keep the string as-is.
- Some columns are null for many components. That is normal, not an error.
- If a column name is rejected, drop it and report it (see section 0).

**DS2 computes:** area- and component-weighted organic matter, texture, drainage, available water, with survey caveats.

## 3. Marsden Farm (already extracted: copy and load)

Everything is in `transform/marsden/` (code) and `data/` (inputs and outputs):

- `data/raw/marsden/pone.0047149-supplement/2026-11-13/` (gitignored; paper PDF plus Tables S1, S3, S4 and Text S1, with `MANIFEST.json` holding SHA-256 values). **Copy verbatim to S3** at `raw/marsden/pone.0047149-supplement/2026-11-13/` and verify checksums.
- Load `data/out/marsden/management_by_year.csv` and `data/out/marsden/management_summary.csv` (columns: `rotation` ('2-yr','3-yr','4-yr'), `year`, `manufactured_n`, `manure_n`, `applied_n` in kg N/ha, `herbicide` in kg ai/ha). Evidence type `experimental`.
- Load `data/out/marsden/indicator_lineage.json` into `indicator_lineage` (4 rows, already complete).
- Keep `data/out/marsden/reconciliation.csv` and `data/out/marsden/run_manifest.json` as evidence.
- Do **not** re-parse the .docx files. Table S1 (site weather) is raw-only for now; DS2 will use it later to sanity-check POWER.

## 4. First-pull review (DS2 checks before the full run)

1. **POWER:** pull the Marsden-site point for **2003-2011 only**, one request, and send it. DS2 compares growing-season (Apr-Nov) mean temperature and rainfall with Marsden Table S1. Expect mean temperatures within about 1 °C and rainfall in the same ballpark (a reanalysis grid will not match a station exactly). Row count, nulls and units are checked at the same time.
2. **SSURGO:** run Steps A-C for the **primary demo field only** and send the three tables. DS2 checks map-unit count, area shares, units and nulls.
3. If either fails the check, DS2 will say what to change. Then run the full set.

## 5. Open items

- ~~`fields.geojson` (Phase 0): needed for the point list and the SSURGO polygons.~~ **Closed 2026-11-14:** committed on `main` at `data/fields/fields.geojson`, 45 features (1 `primary`, 44 `test`) in CRS84, with `field_id`, `role`, `boundary_source`, `county`, `provenance`, `domain_note` and `cover_detail`. Use the polygon centroids for the POWER point list and the polygons themselves for the SSURGO WKT. Compute areas in EPSG:5070, as `scripts/select_fields.py` already does.
- SSURGO table and column names and the POWER response details come from DS2's knowledge of the services and were not verified live. Section 4 is the safeguard. Report any rejection exactly as the service words it.
