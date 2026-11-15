# Requirements: Read the loaded indicators from ClickHouse

## Covers

PRD FR-03, FR-12, NFR-05 (source failures must not silently create misleading outputs). Roadmap Phase 4 (served to the app) and Phase 7 exit check ("the profile renders real data end to end").

## Inputs

ClickHouse tables `fields`, `crop_rotation`, `field_indicators`, `soil_properties` (DE, `schema/`), through `AGROCYCLE_DATA_SOURCE=clickhouse`.

## Outputs

The same `/profile` and `/compare` responses as the file source, built from ClickHouse rows.

## Acceptance criteria

1. For a field with rows in `field_indicators`, the repository returns the same `IndicatorFacts` as the file source does for the same rows (shared function, tested on identical rows through both paths).
2. A `partial` or `unknown` season is not in a mean, and does not make a required indicator `ok`; a field with no rows returns "nothing known".
3. The dominant drainage class comes from `soil_properties` (largest share for `drainagecl`).
4. Queries are parameterised (no field id is spliced into SQL); a hostile id changes no query text.
5. A ClickHouse failure raises (the route returns a server error); it never returns "nothing known" as though the data were absent.
6. In ClickHouse mode the field class comes from ClickHouse and the crop sequence and soil from the committed notes; a field present in ClickHouse but missing from the notes still returns a profile with crop history and soil `not_loaded`.
7. `python -m api.check_clickhouse <field_id>` prints the field record, indicator statuses, the seasonal means and the drainage class the API would use.
8. `pytest api engine` and `ruff` pass.

## Out of scope

The crop-code vocabulary decision, caching, a read-only database user, writing to ClickHouse, running against the live database (needs credentials).
