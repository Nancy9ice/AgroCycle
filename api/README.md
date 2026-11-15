# AgroCycle API

FastAPI service that turns "this field plus what the farmer told us" into the decision engine's result.
It holds no policy: every rule, sentence and status comes from `engine/` (DS2).

```bash
make api            # http://localhost:8000, interactive docs at /docs, schema at /openapi.json
uv run pytest api   # tests
```

## Endpoints

| Method and path | Purpose |
|---|---|
| `GET /health` | Status, data source, rules version |
| `GET /fields`, `GET /fields/{id}` | The 45 demonstration fields |
| `GET /fields/{id}/profile` | Crop history, weather and soil with provenance, in the web app's `FieldProfile` shape (camelCase). Real values only: a section with nothing behind it is `not_loaded`; the API never serves sample data |
| `POST /fields/{id}/compare` | The comparison: one of *worth exploring*, *qualified comparison* or *abstention*, with reasons |

**Not built yet:** `GET /evidence/marsden`, `GET /lineage/{id}`, `POST /fields` (polygon upload). Their shapes
are in `specs/tech-stack.md`.

### `GET /fields/{id}/profile`

- Crop history and soil come from DE's field notes. Weather is the mean of four indicators over the seasons whose
  result is `available` (a `partial` or `unknown` season is left out and counted in "N of M seasons"), read from
  DS2's indicator CSVs. No CSVs, no weather: `not_loaded`.
- Each weather indicator's provenance (source, grid scale, missing-data rule, limitation, evidence type) is read
  from DS2's `INDICATOR_LINEAGE`, so it cannot drift from the code that computes it. This needs `pandas`, which
  the project already depends on.
- Greenness is always `not_loaded`: no HLS features exist yet.

### `POST /fields/{id}/compare`

```json
{
  "manure_access": false,
  "forage_use_or_buyer": null,
  "oat_use_or_buyer": true,
  "small_grain_equipment_or_contractor": null,
  "priorities": ["soil"],
  "sample_indicators": false
}
```

- Each answer is `true`, `false` or `null`. **`null` or omitted means unknown and is never read as `false`.**
  Anything else (`"yes"`, `1`) is rejected with 422 rather than interpreted.
- The client sends only answers and priorities. The server builds the field profile, so a client cannot send
  a wrong one.
- `sample_indicators: true` is a demo affordance: it pretends the four required indicators are known and
  fine, and the response says `"preview": true`. Switch it off with `AGROCYCLE_ALLOW_SAMPLE_PREVIEW=false`.
- The response is the engine's `Decision` with its own field names and `UNKNOWN` as `null`. There is no score,
  rank or winner.

## Data sources

| `AGROCYCLE_DATA_SOURCE` | Reads | Status |
|---|---|---|
| `files` (default) | `data/fields/*`; DS2's indicator CSVs from `data/out/indicators/` (or `AGROCYCLE_INDICATORS_DIR`) if present | Tested |
| `clickhouse` | `fields`, `crop_rotation` | Tested against a fake client only, **not the live database**. `field_indicators` is not in `schema/` yet, so every indicator is unknown |

Until indicator outputs exist, every rotation field abstains ("not enough evidence"). That is the correct,
honest result, not a bug.

## Mapping decisions (for DS2 to confirm) — `api/profile.py`

- The runner's `frost_free_days` is the engine's `frost_window`.
- A required indicator is `ok` only if **every** season row is `available`; a `partial` or missing season
  makes it `unknown`. Conservative on purpose.
- Field class `rotation` is the one in-domain class; a field with no class is unknown, not out of domain.
- The mean of the seasons' frost-free days is passed to the engine; the dominant drainage class is the one
  with the largest area share.

## Keeping the web app in step

The web app carries a copy of the rule table (`web/src/features/compare/data/`), exported from this engine.
`api/tests/test_web_export_is_current.py` fails if it falls behind; fix with `cd web && npm run sync:engine`.
