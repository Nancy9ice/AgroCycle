# Plan: SSURGO soil aggregation for a field

- **Role:** ds2
- **Spec created:** 2026-11-14
- **Roadmap phase and task:** Phase 4, DS2: aggregate SSURGO map-unit and component properties to the field, preserving mapped-survey context and uncertainty

## Goal

Turn the DE's three SSURGO tables (map units with area shares, components, horizons) into field-level soil
values that state how much of the field they actually represent, so the profile can show organic matter,
texture, available water and drainage without implying that anyone sampled the field.

## Approach

Three weighting stages, each carrying its own denominator forward:

1. **Horizon to component**, thickness-weighted over a requested depth interval. Horizons are clipped to the
   interval, so a 0-25 cm horizon contributes 25 cm to a 0-30 cm request and a 25-60 cm horizon contributes 5.
2. **Component to map unit**, weighted by `comppct_r` over the components that have a value.
3. **Map unit to field**, weighted by the intersection `area_share`.

Component-level properties (`slope_r`) skip stage 1. Categorical properties (`drainagecl`, `hydgrp`,
`hydricrating`) cannot be averaged at all, so they return the area-weighted **share of each class** plus the
dominant class and its share, and the dual `hydgrp` strings such as `B/D` stay as they are rather than being
split or resolved.

Available water gets a second form: as well as the depth-weighted mean of `awc_r` in cm/cm, a storage figure in
cm, summed as thickness x awc over the interval, because that is the quantity a rotation decision would use.

The honesty rules do the real work here:

- **Null area shares are fatal, not neutral.** The source sheet's fallback query returns mukeys without areas.
  When any share is null the field value is `unknown` with a reason, because assuming equal weights would
  invent a soil map.
- **Components with no horizons stay in the denominator.** Water and pits have a `comppct_r` and no horizon
  data; dropping them would silently raise the organic matter of a field that is partly a pond.
- **Nothing is filled.** A null property lowers coverage; it never becomes zero.
- Every result reports `area_coverage` and, for horizon properties, `depth_coverage`, and falls to `unknown`
  below a coverage threshold.

## Files, tables and endpoints

Created:
- `transform/indicators/soil.py` — the aggregators, their dataclasses, the input checks and the lineage rows
- `transform/indicators/tests/test_soil.py` — unit tests including a hand-computed weighting chain

Changed:
- `docs/sources/ds2-power-ssurgo-marsden.md` — the Marsden section still points at the pre-move `ds2_marsden/`
  paths; corrected to `transform/marsden/` and `data/out/marsden/`

Consumes the DE's Phase 4 tables, which do not exist yet:
- map units: `field_id, mukey, area_share` (plus `musym`, `muname`)
- components: `mukey, cokey, comppct_r, majcompflag, slope_r, drainagecl, hydgrp, hydricrating`
- horizons: `cokey, chkey, hzdept_r, hzdepb_r` and the `_r` property columns

Produces field-level soil rows for the profile, plus `SOIL_PROPERTY_LINEAGE` rows for `indicator_lineage`.

## Steps (in order)

1. Fix the input contract and the structural checks: required columns, duplicate keys, the sheet's range rules.
2. Thickness-weighted horizon to component aggregation, with depth clipping and coverage.
3. `comppct_r` weighting to the map unit, keeping horizon-less components in the denominator.
4. `area_share` weighting to the field, with the null-share rule.
5. Component-level numeric and categorical aggregation.
6. Available-water storage in cm.
7. Lineage rows with the survey caveats, then tests including a hand-computed chain.

## Dependencies and interfaces with other roles

- **Upstream, not done:** Phase 1 and the DE's SSURGO extraction. S3 holds only smoke-test objects, so this is
  built and tested against the documented contract, as the climate indicators were.
- **DE:** owes the three tables with `_r` columns only, nothing dropped or filled, all keys kept, and the
  `area_share` per (field, mukey) from the Step A intersection. If Step A is rejected and the mukey-only
  fallback is used, `area_share` must be **null**, not an assumed equal split — this module depends on that
  distinction and will return `unknown` rather than guess. Also owes `sacatalog` survey version dates, which
  belong in the lineage row rather than this computation.
- **BE and FE:** `status="unknown"` and a partial `area_coverage` both need showing. A field that is 60 % mapped
  is not the same claim as one that is fully mapped, and the dominant drainage class with a 35 % share is not a
  drainage class for the field.
- **DS1:** same `*_coverage` convention as the climate indicators, so the profile has one shape.

## Data size and subsets

Tiny: a Story or Boone field touches 1-4 map units, each with a few components and 3-6 horizons. One query set
per field, as the sheet specifies. Nothing is downloaded here.

## Risks and open questions

- **The depth intervals are a choice.** 0-30 cm (plough layer) and 0-100 cm (root zone) are conventional, not
  calibrated, and they are arguments rather than constants.
- **The coverage threshold is a judgement call**, as it was for climate. Default 75 %.
- **Component percentages describe the map unit, not a location.** A 40 % component is not 40 % of the field,
  and nothing downstream may read it that way.
- A dual `hydgrp` such as `B/D` depends on drainage that SSURGO does not resolve; keeping the string means the
  consumer must handle it, which is the honest option but needs the FE to cooperate.
- `kffact` and `tfact` are stored as strings in some SSURGO releases; if the DE's pull delivers strings the
  numeric aggregator will raise rather than coerce, and that is the intended behaviour.
- No expert review of any of this yet.
