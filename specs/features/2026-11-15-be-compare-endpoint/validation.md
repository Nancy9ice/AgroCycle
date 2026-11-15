# Validation: Compare endpoint and API skeleton

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
| --- | --- | --- |
| 1 Status codes | `pytest api` (TestClient) | Test output |
| 2 Equals the engine | `pytest api` | Test output |
| 3 Unknown stays unknown | `pytest api` | Test output |
| 4 Abstention without indicators | `pytest api` | Test output |
| 5 Indicator mapping | `pytest api` on fixture CSVs | Test output |
| 6 Sample preview | `pytest api` | Test output |
| 7 Matches the web port | Scripted requests compared with `npm test` fixture logic | Notes below |
| 8 No score fields | `pytest api` | Test output |
| 9 Fields and health | `pytest api`; live call | Notes below |
| 10 Lint, suite, server | `ruff`, `pytest`, `uvicorn`, `curl` | Command output |

## Results (fill in after implementation)

- **Date completed:** 2026-11-15 (implementation); items listed under "Failed or skipped" are still open
- **What was run:** `pytest api engine` -> **129 passed** (48 API tests, rest the engine's) in a Python 3.12 virtualenv; `ruff check api web/scripts engine` passes; the server was started with `uvicorn api.main:app` and called with `curl` (health, compare, a rejected answer, a 404, a CORS preflight from `http://localhost:3004`, `/openapi.json`); 60 requests (6 fields x 5 answer sets x preview on and off) were sent to the API and to the web app's TypeScript port and compared.
- **Passed:**
  - 1: 200 for a known field, 404 for an unknown one, 422 for an unknown priority, an extra key, or an answer that is not `true`, `false` or `null`.
  - 2: the response equals `engine.assess` for the same profile and constraints (a test builds both).
  - 3: omitted and `null` answers come back as `null` and are listed in `unknowns`.
  - 4: with no indicator outputs a rotation field abstains and lists the four required indicators; the three out-of-domain classes (continuous corn, pasture, mixed) abstain with every option `unavailable`.
  - 5: on fixture CSVs shaped like the runner's output: `frost_free_days` maps to `frost_window`, a `partial` season makes an indicator `unknown`, the drainage class is the one with the larger share, a field absent from the outputs is unknown.
  - 6: `sample_indicators` reaches all three outcomes and returns `preview: true`; with the switch off it returns 403.
  - 7: 60 of 60 requests identical between the API and the web port (the crop-history sentence was excluded from the comparison and is covered by its own tests).
  - 8: no key name contains score, rank, winner, best, recommendation or weight.
  - 9: `GET /fields` returns 45 fields, primary first; `GET /health` reports the data source and rules version `2026-11-15.2`.
  - 10: suite, lint and server as above.
  - A test fails if the web app's exported rule table falls behind the engine's `RULES_VERSION`.
- **Web switched to the API (2026-11-15):** `npm run check` -> 182 web tests pass, including 14 for the API client (request body, `null` kept as `null`, 404 gives undefined, 500/422/503 and unreachable throw, malformed or disallowed outcomes are rejected, no fallback when the API fails). End to end: the production web app with `AGROCYCLE_API_URL` set to the running API gave the same outcomes, strategy states and statuses as the local engine on all 7 browser scenarios (14 `POST` calls seen in the API log; console empty). With the API stopped, the compare and brief screens showed the error page with no result; the profile page (not API-backed) still loaded.
- **Bug caught by a test:** Pydantic's default mode turned `"yes"` and `1` into `true`. That would have read a guess as a farmer's answer. The answer fields now use `StrictBool`.
- **Failed or skipped:**
  - **`ClickHouseRepository` has never run against the live database.** Only a fake client. Its SQL joins `fields` and `crop_rotation`; `field_indicators` is not in `schema/` yet.
  - **No indicator outputs exist on disk**, so the indicator path was only tested on fixtures I wrote to match the runner's code, not on a real runner output.
  - `uv.lock` was not regenerated (`uv` is not installed on the machine used); run `uv lock`. Tests ran in a plain virtualenv with the packages installed by `pip`.
  - Not built: profile, Marsden evidence, lineage and polygon-upload endpoints.
  - The mapping rules in `api/profile.py` (strict `ok`, the `frost_window` name) are my choices and need DS2's confirmation.
- **Evidence location:** `api/tests/`; this file.
- **Roadmap exit check met:** yes for the `/compare` half of Phase 10 (the endpoint returns the structured result).
- **Roadmap tracker updated:** yes, 2026-11-15 (left "In progress": review by the BE owner and the live ClickHouse run are open)
