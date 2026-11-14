# DS2 first-pull review — POWER and SSURGO, 14 November 2026

Roadmap Phase 1 asks a DS to review the first pull of each source before the full run. This is that review.
Both pulls are **accepted**; the findings below are limitations to carry, not defects to fix.

Reviewed by recomputing from the raw files in S3, not by reading the DE's summary.

## 1. POWER — Marsden site, 2003–2011

`raw/power/daily-point-api-v2.10.3/2026-11-14/marsden-site_20030101-20111231.json`

**Verdict: accepted, with a documented precipitation bias.**

Independently recomputed from the raw file and reproduced the DE's figures exactly. 3,287 daily rows (nine
years including two leap days), 7 variables, **zero** `-999` fill values, 244 days in every April–November
window. Header records API v2.10.3, sources MERRA2 / SYN1DEG / POWER, fill value −999.0, time standard LST.
Returned coordinates `-93.783, 42.017` at **310.22 m** elevation — that elevation is the value to pass to
reference ET.

### Against Marsden Table S1 (station ~1 km from the plots, April–November)

| Year | S1 °C | POWER °C | Δ°C | S1 mm | POWER mm | Δmm | Δ% |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2003 | 14.9 | 15.88 | +0.98 | 790 | 655 | −135 | −17.1 |
| 2004 | 15.0 | 15.70 | +0.70 | 697 | 670 | −27 | −3.9 |
| 2005 | 15.9 | 17.31 | **+1.41** | 748 | 586 | −162 | −21.7 |
| 2006 | 15.6 | 16.49 | +0.89 | 777 | 612 | −165 | −21.2 |
| 2007 | 16.4 | 16.17 | −0.23 | 839 | 854 | +15 | +1.8 |
| 2008 | 15.2 | 14.55 | −0.65 | 1145 | 970 | −175 | −15.3 |
| 2009 | 14.8 | 14.61 | −0.19 | 755 | 765 | +10 | +1.3 |
| 2010 | 16.5 | 16.06 | −0.44 | 1165 | 1067 | −98 | −8.4 |
| 2011 | 15.2 | 15.90 | +0.70 | 701 | 611 | −90 | −12.8 |

**Temperature passes.** Bias +0.35 °C, mean absolute 0.69 °C, 8 of 9 years within the ±1 °C the source sheet
expects. 2005 is +1.41 °C, the single exception; nine-year means are 15.50 (station) against 15.85 (POWER).

**Precipitation is systematically low.** Mean −92 mm per season, about −11 %, lower in 7 of 9 years, worst
−175 mm (2008). Nine-year means 846 mm against 754 mm.

This is a reanalysis-versus-gauge difference, not an extraction error, and the two series track each other
(both put 2008 and 2010 as the wet years and 2005 and 2011 as dry). It is not a reason to reject the pull, but
it has consequences:

- POWER rainfall totals must not be compared against station-based agronomic thresholds.
- Dry spells computed from POWER are **more likely overstated than understated**.
- Both are now recorded in the `INDICATOR_LINEAGE` limitations for `precipitation_total`,
  `longest_dry_spell` and `dry_spell_count`.

### Indicators run on the real series

First exercise of `transform/indicators/climate.py` outside synthetic frames. All nine seasons returned
`status="ok"` at 244/244 days.

| Year | GDD | Heat days | Rain mm | Longest dry | ET0 mm | Frost-free |
|---|---:|---:|---:|---:|---:|---:|
| 2003 | 1861 | 51 | 655 | 14 | 906 | 174 |
| 2004 | 1795 | 19 | 670 | 15 | 809 | 171 |
| 2005 | 2107 | 64 | 586 | 13 | 952 | 172 |
| 2006 | 1983 | 62 | 612 | 14 | 913 | 167 |
| 2007 | 1946 | 37 | 854 | 30 | 814 | 192 |
| 2008 | 1660 | 2 | 970 | 11 | 699 | 169 |
| 2009 | 1580 | 13 | 765 | 24 | 703 | 171 |
| 2010 | 1894 | 16 | 1067 | 16 | 743 | 202 |
| 2011 | 1883 | 36 | 611 | 20 | 804 | 168 |

Values are plausible for central Iowa and internally consistent (2008, the cool wet year, has 2 heat days and
the lowest ET0). Frost-free spans run 167–202 days, all well above the 120-day threshold in
`applicability_oat_season_length`, so that rule never fires here.

**One new limitation found in the header:** `ALLSKY_SFC_SW_DWN` comes from **SYN1DEG, a 1-degree grid**,
coarser than the ~0.5° × 0.625° temperature fields. Reference ET is therefore the least local indicator we
produce. Recorded in its lineage row.

## 2. SSURGO — primary-001

`raw/ssurgo/soil-data-access/2026-11-14/primary-001/` (steps A–D, each with a manifest)

**Verdict: accepted as it stands. Keep all ten map units.**

Reconstructed the area shares from the step A intersection WKT in EPSG:5070 and ran the Phase 4 aggregation.
`check_soil_tables` returned **no findings**: shares sum to 1.000, component percentages sum to 100 in every
map unit, horizon depths all ascend, no orphan keys.

Field area 43.6 ha across 10 map units, 30 components, 114 horizons.

| Share | Map unit |
|---:|---|
| 30.0 % | Canisteo clay loam, Bemis moraine, 0–2 % |
| 29.2 % | Nicollet loam, 1–3 % |
| 11.9 % | Clarion loam, Bemis moraine, 2–6 % |
| 9.8 % | Webster clay loam, Bemis moraine, 0–2 % |
| 7.3 % | Harps clay loam, Bemis moraine, 0–2 % |
| 5.3 % | Clarion loam, Bemis moraine, 6–10 % |
| 2.7 % | Coland-Terril complex, 1–5 % |
| 1.9 % | Storden loam, Bemis moraine, 6–10 % |
| 1.6 % | Okoboji silty clay loam, 0–1 % |
| 0.1 % | Storden loam, Bemis moraine, 10–16 % |

**Ten map units is fine.** The "1–4" in the source sheet was my estimate for a typical field, not a rule, and
43.6 ha crossing a moraine drainage sequence is expected to touch more. **Do not drop the slivers:** the
aggregation is area-weighted, so a 0.1 % unit moves nothing, while dropping it would change the denominator
and silently alter every value.

Aggregated to the field, all at 100 % area and depth coverage:

| Property | Value |
|---|---|
| `om_r_0_30cm` | 5.33 % by weight |
| `claytotal_r_0_30cm` | 27.01 % |
| `sandtotal_r_0_30cm` | 31.66 % |
| `ph1to1h2o_r_0_30cm` | 6.81 pH |
| `awc_r_0_100cm` | 0.19 cm/cm |
| `available_water_storage_0_100cm` | 18.55 cm |
| `slope_r` | 2.10 % |

Drainage: Poorly drained 47.1 %, Somewhat poorly drained 25.9 %, Well drained 21.6 %, Very poorly drained
4.4 %, Moderately well drained 1.0 %. Hydrologic group: C/D 51.5 %, B/D 25.9 %, B 21.8 %, C 0.8 %.

Survey version 2026-09-08 for IA015 and IA169; belongs in the lineage row, not in the computation.

### Two findings the team must decide on

1. **The primary demo field fires `applicability_alfalfa_drainage`.** Its dominant drainage class is "Poorly
   drained", so the four-year alfalfa strategy will be shown **qualified** in the demo. That rule rests on
   crop claim `alfalfa_drainage_sensitivity`, which is `research_needed`. It is no longer hypothetical: either
   a citable source is found before the demo, or the rule is withdrawn as its own rationale requires.
2. **"Dominant" here means 47 %, not a majority.** The soil lineage already warns that a dominant class with a
   small share is not a drainage class for the field, and this field proves the point: 53 % of it is *not*
   poorly drained. The rule currently reads the dominant class whatever its share. Worth deciding whether
   `aggregate_component_class` should require a majority before naming a dominant, or whether the engine
   should carry the share into the rule. Not changed unilaterally.

## 3. Answers to the DE's full-run questions

- **Grid dedupe:** agreed. One request per field plus the Marsden site (46 requests, ~70 MB) and grouping
  identical series in Phase 4 is the right order. POWER echoing the requested coordinates rather than a cell
  centre means dedupe-by-cell was never safe; grouping on the returned series is.
- **GWETROOT / GWETTOP:** not wanted. No indicator or applicability rule reads them, they were listed as
  context only, and the deadline is tomorrow. Skip.
- **Manifests, raw-versus-processing and Marsden scope** were agreed separately: per-file manifests keeping
  the DS2 SHA-256 values, raw stored verbatim with conversions in Phase 4, and only raw files in Phase 1.

**Clear to start the full POWER and SSURGO runs.**
