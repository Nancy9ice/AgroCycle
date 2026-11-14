# Requirements: SSURGO soil aggregation for a field

## Covers

- **PRD requirements:** FR-05 (retrieve relevant SSURGO map-unit and component properties, preserving
  mapped-survey context and uncertainty), FR-06 (data adequacy), FR-12 (traceability), NFR-01, NFR-03,
  NFR-05 (missing data must not silently create misleading outputs), NFR-06.
- **Roadmap exit check satisfied:** the soil half of Phase 4's DS2 work — "SSURGO map-unit/component
  properties with survey caveats", each stating its scale. Loading and the Pandera schema remain the DE's.

## Inputs

The DE's three SSURGO tables from Soil Data Access, representative (`_r`) columns only, nothing dropped or
filled, all keys kept:

| Table | Required columns | Also used |
|---|---|---|
| `map_units` | `field_id`, `mukey`, `area_share` | `musym`, `muname` |
| `components` | `mukey`, `cokey`, `comppct_r` | `slope_r`, `drainagecl`, `hydgrp`, `hydricrating`, `majcompflag` |
| `horizons` | `cokey`, `chkey`, `hzdept_r`, `hzdepb_r` | `om_r`, `claytotal_r`, `sandtotal_r`, `silttotal_r`, `ph1to1h2o_r`, `awc_r`, `ksat_r`, `dbthirdbar_r`, `cec7_r` |

Units are the source's own: percentages by weight for organic matter and texture, pH, cm/cm for `awc_r`,
micrometres/s for `ksat_r`, g/cm3 for `dbthirdbar_r`, meq/100 g for `cec7_r`, cm for depths, % for `slope_r`.

`area_share` is the field-area fraction from the Step A intersection, **or null** when the mukey-only fallback
query was used. That distinction is load-bearing: see criterion 4.

## Outputs

Numeric properties return a `SoilProperty`: `property_id`, `value` (float or **null**), `unit`, `depth_top_cm`,
`depth_bottom_cm`, `area_coverage`, `depth_coverage`, `map_units`, `status` (`ok` or `unknown`) and `reason`.

Categorical properties return a `SoilClassShares`: `property_id`, `shares` (class to field-area share),
`dominant`, `dominant_share`, `area_coverage`, `map_units`, `status`, `reason`.

| Function | Output | Unit |
|---|---|---|
| `aggregate_horizon_property` | `om_r`, texture, `ph1to1h2o_r`, `awc_r`, `ksat_r`, `dbthirdbar_r`, `cec7_r` over a depth interval | the source's own |
| `aggregate_available_water_storage` | depth-integrated available water | cm |
| `aggregate_component_property` | `slope_r`, `tfact` | %, tons/acre/yr |
| `aggregate_component_class` | `drainagecl`, `hydgrp`, `hydricrating` shares | share of field area |
| `check_soil_tables` | the sheet's data-quality findings as strings | — |

`SOIL_PROPERTY_LINEAGE` holds one row per exposed property for the `indicator_lineage` table, each with the
survey caveat in its `limitation`.

## Acceptance criteria

Each is covered by a test in `transform/indicators/tests/test_soil.py`.

1. The three weighting stages compose correctly: a hand-computed two-map-unit field with clipped horizons
   returns exactly 2.48 % organic matter over 0-30 cm.
2. Horizons are clipped to the requested interval, so a 25-60 cm horizon contributes 5 cm to a 0-30 cm request
   and a component wholly outside the interval contributes nothing.
3. A null property lowers the thickness that carried data and never becomes a zero.
4. **A null `area_share` returns `unknown`**, with a reason stating that equal weights are not assumed.
5. A component with no horizon data — water, a pit — stays in its map unit's denominator, so it lowers
   `depth_coverage` instead of vanishing.
6. Below `min_area_coverage` (default 75 %) the result is `unknown`, and `area_coverage` is still reported so
   the caller can see how much was mapped; a lower threshold passed by the caller accepts it and still reports
   the partial coverage.
7. Categorical properties return area-weighted shares summing to the coverage, name the dominant class only
   when coverage suffices, and keep a dual hydrologic group such as `B/D` as a single class.
8. `check_soil_tables` reports area shares that do not sum to about 1, null area shares, component percentages
   above 100, inverted horizon depths and orphan mukeys; and raises on duplicate keys or a missing column.
9. A field with no map units raises, rather than returning a value — the sheet calls this a geometry problem.
10. Every lineage row is complete, ids are unique, each carries `evidence_type: survey` and the survey caveat,
    and the texture row states that clay, sand and silt are not re-normalised.

## Evidence labels, scale and limitations to preserve

- **Evidence type:** `survey` for all seven. SSURGO is a mapped survey, not a measurement of this field.
- **Scale:** mapped soil units intersecting the field polygon. Component percentages describe the **map unit**
  and locate nothing within the field, so a 40 % component is not 40 % of the field.
- **Limitations to carry downstream:** the 0-30 cm and 0-100 cm intervals are conventions, not calibrations;
  the 75 % coverage threshold is a judgement call; clay, sand and silt are aggregated independently and need
  not sum to 100 after weighting, and are deliberately not re-normalised because that would hide missing
  horizons; a dominant drainage class with a small share is not a drainage class for the field, so shares must
  be shown with it; installed tile drainage is absent from SSURGO; a representative map-unit slope is not the
  field's slope distribution and supports no erosion claim; plant-available water also depends on rooting
  depth, compaction and crop, none of which is here. None of this is expert-reviewed.
- A partial `area_coverage` is itself a finding and must reach the user, not be rounded away.

## Out of scope

The SDA queries and extraction (DE), the geometry intersection and area computation (DE), the Pandera schema,
the ClickHouse load, the survey version dates from `sacatalog` (they belong in the lineage row, not in this
computation), erosion susceptibility (PRD-conditional, Phase 12), and any interpretation of these values as
suitability for a rotation, which is Phase 9's rule table.
