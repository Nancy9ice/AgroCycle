# Validation: Read the loaded indicators from ClickHouse

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
| --- | --- | --- |
| 1 Same facts from both sources | `pytest api` | Test output |
| 2 Partial and unknown seasons | `pytest api` | Test output |
| 3 Drainage class | `pytest api` | Test output |
| 4 Parameterised queries | `pytest api` | Test output |
| 5 Failures raise | `pytest api` | Test output |
| 6 Hybrid record | `pytest api` | Test output |
| 7 Check command | Run against a fake client in a test; run live by someone with credentials | Test output; live output pasted below |
| 8 Suite and lint | `pytest`, `ruff` | Command output |

## Results (fill in after implementation)

- **Date completed:** 2026-11-15 (implementation); the live-database check is still open
- **What was run:** `pytest api engine` -> **149 passed** (Python 3.12 virtualenv); `ruff check api web/scripts engine` passes. Nothing was run against the live ClickHouse: I have no credentials and did not read `.env`.
- **Passed:**
  - 1: identical rows through the file path and the ClickHouse path give equal `IndicatorFacts` (a test writes the same logical rows as a CSV and as ClickHouse tuples and compares).
  - 2: a `partial` season is not in the mean and makes the indicator `unknown`; an `unknown` season with a null value is omitted; a field with no rows is "nothing known".
  - 3: the dominant drainage class is the one with the larger share.
  - 4: with a hostile field id (`'; DROP TABLE ...`) every query is sent unchanged with the id as a parameter.
  - 5: a database error raises `ConnectionError` through both `get_field` and `get_indicators`.
  - 6: the class comes from ClickHouse, the crop sequence and soil from the notes; a field absent from the notes loads with crop history and soil `not_loaded`; the fields query never asks for `sequence`.
  - 7: `api.check_clickhouse.describe` is tested against a fake client; it imports without boto3 and only needs the project's dependencies when run.
  - 8: suite and lint as above.
- **Failed or skipped:**
  - **Live run not done.** Whoever has the credentials should run `uv run python -m api.check_clickhouse primary-001` and paste the output here. Until then the ClickHouse path is verified only against a fake.
  - **Likely consequence to confirm with DE and DS2:** DE reports 20 `partial` rows among 4,410. Under the API's conservative rule (an indicator is `ok` only if every season is `available`), a field with a partial season in `gdd`, `precipitation_total`, `frost_free_days` or `om_r_0_30cm` will still make the engine abstain. Which fields and indicators those are can only be seen in the data. If DS2 decides a `partial` season may count, it is one line in `api/profile.py`, with the reason written down.
  - The vocabulary clash between DS1's crop tokens and the web app's crop codes is recorded, not resolved.
  - No caching, no read-only database user.
- **Evidence location:** `api/tests/test_repository.py`; this file.
- **Roadmap exit check met:** not yet (needs the live check).
- **Roadmap tracker updated:** yes, 2026-11-15 (left "In progress")
