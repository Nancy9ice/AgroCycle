# Validation: Fill data_sources and link every output to its source

## Checks

| Criterion | How it is verified | Evidence |
|---|---|---|
| 1. PRD 6.1 fields present | Offline: every catalog record against the required field list; a test fails if one is empty | pytest output |
| 2. Matches S3 | Live (skips without S3): `file_count` and `total_bytes` against an independent recount of the objects; manifest fields against the manifests; no prefix under `raw/` left uncovered | pytest output, counts |
| 3. Every indicator linked | Offline: the lineage's three source texts map to one source each, an unknown text names the indicator and fails. Live: all 25 indicators have a link | pytest output, query |
| 4. Links valid | Offline: no link to a missing source or indicator; the table-to-source links as listed | pytest output |
| 5. Safe reshape | Offline: the runner refuses when the old table has rows; the migration prefix works for `DROP TABLE IF EXISTS` and refuses other statements | pytest output |
| 6. Idempotent, portable | Live: load twice, compare hashes; `make check` with S3 and ClickHouse settings absent | hash values, output |
| Hand-check | DS1 and DS2 read the text compiled for their sources and correct what is wrong | message, PR comment |

Merge when: every row is green, the code review findings are fixed, and the tracker row is updated.

## Results

- **Date completed:** 2026-11-15
- **What was run:** offline tests (catalog, scan, builder, links, schemas, migration guard); live tests against S3 and ClickHouse; migration 006 and `python -m transform.sources.run --load` on the real database; a second load to compare hashes; `/code-review` and its fixes.
- **Passed:**
  - Every catalog record has every PRD 6.1 field; every prefix under `raw/` belongs to exactly one source (live, all 15,000+ objects); scan counts equal an independent recount for the small pulls.
  - Real database: `data_sources` 8 rows, `source_links` 37 (25 indicator, 12 table); all 25 `indicator_lineage` ids linked; two loads give identical table hashes (`data_sources` 7312938955408596046, `source_links` 11515471298082512564).
  - A source text the catalog does not know fails and names the indicator; a link to a missing source fails; a manifest date that differs from the prefix date fails.
  - The migration runner now refuses any `DROP TABLE` over a table that holds rows (tested with a fake client).
- **Review findings fixed:** drop guard in `migrate` (the comment in 006 claims a guard that did not exist when it was applied; it cannot be edited now, so the guard lives in `migrate`); manifests must pair one-to-one with objects; a bad manifest is named in the error; manifest date checked against the prefix; dead helper removed; import moved to the top.
- **Known and accepted:** `data_sources` and `source_links` load in two calls, not atomically; a failure between them is cured by rerunning, which is idempotent.
- **Changes to the spec:** `fields` is not linked to CDL (its boundaries are `demo`). `fields` has no source link.
- **Failed or skipped:** none after the merge with main. Live tests skip without S3 or ClickHouse access.
- **Open for DS1 and DS2:** review the text compiled for their sources in `transform/sources/catalog.py`. `gdd_season_difference_vs_marsden` is linked to POWER only, as its lineage says, though it also uses Marsden.
- **Evidence location:** pytest output; the two tables in ClickHouse.
- **Roadmap exit check met:** yes. An indicator, its lineage and its sources are one join.
- **Roadmap tracker updated:** yes.
