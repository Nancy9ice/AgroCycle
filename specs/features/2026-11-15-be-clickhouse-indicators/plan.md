# Plan: Read the loaded indicators from ClickHouse

- **Role:** be (written by the frontend developer; the BE owner should review)
- **Spec created:** 2026-11-15
- **Roadmap phase and task:** Phase 10/7 BE: serve real data. DE's Phase 4 loaded `field_indicators` (4,410 rows, 45 fields, 11 seasons), `soil_properties` and `indicator_lineage` into ClickHouse, so the API can leave "not enough evidence" for real.

## Goal

Make `AGROCYCLE_DATA_SOURCE=clickhouse` serve real weather and soil indicators on `/profile` and `/compare`, instead of reading CSVs from a folder. The data is already there; the API has not been reading it.

## Approach

- **Same logic, new source.** The ClickHouse tables have exactly the columns DS2's runner writes to CSV (plus `load_id`). Both repositories now turn rows into the same facts through one function (`facts_from_rows`), so the file and ClickHouse paths cannot drift: the same conservative rules apply (a season counts only if its status is `available`; `frost_free_days` is the engine's `frost_window`; the dominant drainage class is the one with the largest share).
- **Two small queries per request** (one per table, filtered by field), parameterised. No caching yet: the tables are tiny and read-only at demo time.
- **Crop sequence stays on the committed field notes.** ClickHouse's `crop_rotation.sequence` is space-separated tokens in DS1's vocabulary, where `L` meant *low confidence* (changed to `U` on 2026-11-15 so `L` is clover everywhere) and `P`, `N`, `M` have no equivalent in the web app. Passing it through would crash or mislabel crops. So in ClickHouse mode the field class (DS1's rule-based `rotation` or not) comes from ClickHouse, and the sequence and soil series come from DE's committed notes. The vocabulary clash is recorded as an open item for DS1, DE and FE.
- **A check command.** `python -m api.check_clickhouse [field_id]` prints exactly what the API would read for a field, so someone with credentials can verify the live path in seconds. It is the one thing I cannot run myself: I have no credentials and did not use `.env`.

## Files, tables and endpoints

- `api/repository.py` (shared row-to-facts function; ClickHouse reads indicators and soil classes), `api/settings.py`, `api/check_clickhouse.py`, tests, README.
- Reads `fields`, `crop_rotation`, `field_indicators`, `soil_properties`. No writes.

## Steps (in order)

1. Spec and tracker.
2. Refactor to one row-to-facts function; ClickHouse queries; settings.
3. Tests with a fake client that answers by table; check command.
4. Run the suite; record what could not be run live.

## Dependencies and interfaces with other roles

- **DE:** table and column names (`schema/003_indicators.sql`) are the contract; DE's note that the loaded tables have empty values where DS2's `unknown_reason` was blank (open item for DS2) does not affect the status or value the API reads.
- **DS1, DE, FE:** crop-code vocabulary: DS1's tokens (`C S O A P N X M L`) versus the web app's CDL-style codes (`C S G A H O L X`). `L` means different things. One vocabulary should be chosen before the crop sequence is read from ClickHouse.
- **Whoever has credentials:** run `python -m api.check_clickhouse primary-001` against the live database and record the result in this spec.

## Risks and open questions

- Not run against the live database (no credentials used). The queries are tested against a fake client only.
- Read-only access: the API should use a read-only ClickHouse user in deployment.
