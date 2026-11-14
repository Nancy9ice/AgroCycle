# Requirements: Repo, infra and field GeoJSON setup

## Covers
- **PRD requirements:** FR-01, NFR-01, NFR-06
- **Roadmap exit check satisfied:** everyone can run the repo; the primary demo field and the test-set polygons are committed as GeoJSON with their provenance recorded.

## Scope and decisions
- In scope: repo layout, env handling, S3 and ClickHouse connectivity, field GeoJSON schema, validation and commit.
- The bucket and ClickHouse credentials already exist; nothing is provisioned.
- The BE/FE API contract is a separate task, not this spec.

## Inputs
- Env variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `S3_BUCKET`, `CLICKHOUSE_HOST`, `CLICKHOUSE_PORT`, `CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD`, `CLICKHOUSE_SECURE`
- Polygons drawn by DE (WGS84, EPSG:4326)
- Story and Boone County boundaries (public Census TIGER)

## Outputs
`data/fields/fields.geojson`: one Feature per field, with properties:

| Property | Type | Rule |
|---|---|---|
| `field_id` | string | unique, e.g. `primary-001`, `test-014` |
| `role` | enum | `primary` or `test`; exactly one `primary` |
| `boundary_source` | enum | `demo` or `real` |
| `county` | enum | `Story` or `Boone` |
| `provenance` | string | who drew it, how and when |
| `domain_note` | string | in-domain, or out-of-domain type (continuous corn, pasture, non-rotation) |

## Acceptance criteria
1. A fresh clone plus a local env file runs `make check` successfully.
2. `smoke_s3.py` uploads, downloads and checksums a small test object under a `smoke/` prefix.
3. `smoke_clickhouse.py` connects, runs `SELECT 1`, and creates, queries and drops a scratch table.
4. `fields.geojson` has one `primary` and at least 30 `test` fields, split across both counties.
5. Every polygon is valid, non-empty and inside its stated county. Invalid ones fail with a clear message.
6. Every field has all properties above. All `demo` boundaries are labelled `demo`.
7. Several out-of-domain fields exist, noted in `domain_note`.
8. No secret, raw data or env file is committed.

## Evidence labels, scale and limitations to preserve
- Fields are `assumption/user input`: demo geometry, not real farm boundaries.
- The primary field is a typical maize–soybean parcel, to be checked against CDL history by DS1.

## Out of scope
Raw data extraction, manifest tooling, ClickHouse table creation, the API contract, CDL clipping.
