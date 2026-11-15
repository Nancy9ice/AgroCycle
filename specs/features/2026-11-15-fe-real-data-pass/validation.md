# Validation: Make the screens and claims match real data

## Results (fill in after implementation)

- **Date completed:** 2026-11-15
- **What was run:** `npm run check` -> 196 web tests pass, lint and build clean; `pytest api engine` -> 157 pass; `ruff` clean on `api`, `web/scripts`, `engine`. The API was run against the live ClickHouse and the production web app against it; the screenshot pack was re-captured (12 images) and the profile soil section, the withheld-field comparison and the other shots were looked at. The five comparison outcomes quoted in the guide were re-checked against the live API.
- **Passed:**
  - 1: the comparison page's "why does this say not enough evidence" note now appears only when the engine lists a required measurement as unknown (test: shown without the indicators, hidden once all four are known even if farm questions are still unknown). With real data, a normal field shows no such note.
  - 2: the sample preview banner still shows whenever `preview` is true; its text and the brief's no longer claim the measurements "are not measured for this field".
  - 3: the validation page and the README no longer say that every real result is "not enough evidence" or that no indicator values exist; the wording holds with the API on and off.
  - 4: the validation page records the observation (26 of 27 in-domain fields reach "worth exploring", 18 of 18 out-of-domain abstain, `test-022` withheld at 96.7 % organic-matter coverage) and says it is one engine run on demonstration fields, not a validation.
  - 5: the weather row says the indicators are loaded for all 45 fields (4,390 of 4,410 rows complete; the 20 partial rows are all soil measures) and still says they are unchecked against a station, POWER is a 50 km model, and thresholds are team-proposed. The soil row no longer says the soil values were never run on real data or that drainage and organic matter are not loaded.
  - 6: the screenshot pack was re-taken against the API on live data; the guide's table lists the answers used for each shot, and its statuses are real.
  - 7: the architecture diagram shows the API as built, with the reason in its README.
  - 8: `npm run check` passes; no secret is in any file (the live credentials were passed as environment variables to single commands).
- **Also changed (found while doing this):** the profile's soil section said "Not loaded yet: how well it drains, organic matter, texture" although that data exists. The API now returns the real survey values (organic matter, texture, acidity, water storage, and the drainage mix: for the demo field 47 % poorly drained, 26 % somewhat poorly drained, 22 % well drained, 5 % other) each with a plain note, a partial value keeps DS2's coverage note, and the section lists as "not loaded" only what is actually missing. 13 new API tests.
- **Failed or skipped:**
  - Without `AGROCYCLE_API_URL` the web app still has no weather or soil values and says "not enough evidence" for every field; the guide says not to use that mode for the deck.
  - The `Soil moisture from space` item on the profile strip is still "Not loaded" (not planned).
  - Satellite greenness is not built and says so.
  - The difference from the Iowa site is exactly 0.0 for the primary field, because it sits in the same weather grid cell as the research farm. Real, but it means that rule cannot separate nearby fields; worth knowing before the deck says anything about climate distance.
  - Decisions still open: DS2's partial-value rule and the crop-code vocabulary.
- **Evidence location:** `docs/demo/screenshots/`, `api/tests/`, this file.
- **Roadmap exit check met:** the Phase 7 exit check ("the profile renders real crop-history, soil and climate data end to end") is met for crop history, soil and weather; greenness is not built.
- **Roadmap tracker updated:** yes, 2026-11-15
