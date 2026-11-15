# Screenshots for the 7-slide deck

The submission is a 7-slide deck with **real screenshots from the working app** (`PRD.md` §13). This folder
holds a repeatable capture of every screen, and says exactly what each picture is. The deck must say the same.

> **What "real" means here.** These were taken on 2026-11-15 with the web app talking to the API, and the API
> reading DE's indicators from the live ClickHouse: weather and soil values for all 45 demonstration fields over
> 11 seasons. Every comparison is a real engine result on that data. It is still a development build on
> **demonstration polygons, not real farms**, no value has been checked against a weather station, no rule has
> been reviewed by an agronomist, and no farmer has reviewed the app. Say so on the slides.
>
> **Greenness (satellite) is not shown:** no vegetation features have been computed, and the profile says
> "Not loaded". Do not describe the app as using satellite greenness.

## What each picture is

| File                                    | Screen                                           | What it shows                                                                                                                                                                                                   | Answers used                                                                                            |
| --------------------------------------- | ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `01-home.png`                           | Home                                             | The decision, three options, how it works, the honesty rules                                                                                                                                                    | none                                                                                                    |
| `02-field-map.png`                      | Choose a field                                   | 45 demonstration polygons in Story and Boone counties on satellite imagery; geometry checked                                                                                                                    | none                                                                                                    |
| `03-profile.png`                        | Field profile (Story demo field)                 | Real crop history, real weather means (rain 684 mm, 42 very hot days, 3.8 dry spells, 1,990 growing degree days; 11 of 11 seasons), real soil survey values, each with source and scale; greenness "Not loaded" | none                                                                                                    |
| `04-evidence-drawer.png`                | Evidence drawer on the rain card                 | The record behind one number: source, grid scale (about 50 km), the 11 % low rainfall caveat against the Iowa station, evidence type                                                                            | none                                                                                                    |
| `05-priorities.png`                     | Priorities and constraints                       | 12 optional questions; four feed the engine, three are recorded for an adviser                                                                                                                                  | soil high, water medium, inputs high; manure no, hay "could sell", oats yes, grain equipment "can hire" |
| `06-compare-with-caveats.png`           | Comparison                                       | A comparison with caveats: no manure, so the nitrogen result does not carry over while the herbicide result still applies                                                                                       | same as 05                                                                                              |
| `07-compare-worth-exploring.png`        | Comparison                                       | "Worth exploring further": every farm question answered yes, the Iowa trial figures, evidence types, cautions                                                                                                   | manure yes, keep animals, oats yes, equipment have; soil and inputs high                                |
| `08-compare-questions-unanswered.png`   | Comparison                                       | The farm questions left unanswered: the nitrogen result is held back, the others apply with caveats, and the open questions are listed                                                                          | soil and inputs high only                                                                               |
| `09-compare-outside-domain.png`         | Comparison, a continuous-corn field (`test-027`) | A field outside the evidence: no option offered, every outcome says it does not carry over                                                                                                                      | none                                                                                                    |
| `10-compare-one-measure-incomplete.png` | Comparison, `test-022`                           | Refusal at 96.7 %: one soil measure (organic matter) covers 96.7 % of this field's area, so the engine withholds the result rather than treat it as complete                                                    | all four farm questions yes                                                                             |
| `11-adviser-brief.png`                  | Brief for an adviser                             | One printable page: result, options, answers, questions to ask, sources                                                                                                                                         | same as 05                                                                                              |
| `12-validation.png`                     | How we checked this                              | Four kinds of evidence kept apart; the one result that did not match the paper                                                                                                                                  | none                                                                                                    |

Screenshots are full-page and tall (the map shot is window-sized). Crop the section a slide needs.

## What the run showed (one engine run on demonstration fields, not a validation)

With every farm question answered yes: **26 of 27** maize-soybean rotation fields reach "worth exploring"; all
**18** fields outside that pattern (11 continuous corn, 6 pasture or hay, 1 mixed) say "not enough evidence";
the 27th rotation field (`test-022`) is withheld for the reason in shot 10. With farm questions unanswered the
results are caveated or held back, never assumed.

## Slide map (`PRD.md` §13)

| Slide                                                                                  | What it must prove              | Use                                                               | Gap to close                                                                  |
| -------------------------------------------------------------------------------------- | ------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| 1. The decision and the changing context                                               | Specific problem                | `01-home` (top), `02-field-map`                                   | None                                                                          |
| 2. Field profile from NASA and other data                                              | Best Use of Data                | `03-profile`, `04-evidence-drawer`                                | Real NASA POWER weather and USDA soil. **No satellite greenness yet**: say so |
| 3. What the indicators can and cannot establish; Marsden evidence                      | Best Use of Science             | `04`, the figures in `07`, `docs/method/ds2-scientific-method.md` | None for the figures; they are reproduced from the paper's supplement         |
| 4. Architecture and data lineage                                                       | Best Use of Technology          | `docs/diagrams/architecture.png`, `lineage.png`                   | None; status is a snapshot                                                    |
| 5. Comparison of the three strategies against priorities and constraints               | Best Use of Technology          | `05`, `06`, `07`, `08`                                            | None                                                                          |
| 6. Benefits, trade-offs, uncertainties, qualified assessment or abstention, validation | Farmer-centred decision support | `06`, `09`, `10`, `11`, `12`                                      | None                                                                          |
| 7. Limitations, stakeholder-feedback gap, impact pathway                               | Local Impact, honest claims     | `12-validation`, the limits section of `06`                       | The stakeholder gap is stated on `12`; no farmer has reviewed the app         |

## Reproduce

You need the web app, the API, and the data service. The data service is the ClickHouse the team loaded.

```bash
# terminal 1: the API on the live data (set the real values in your own .env; never commit them)
AGROCYCLE_DATA_SOURCE=clickhouse make api

# terminal 2: the web app, built, pointing at the API
cd web && npm install && npm run build
AGROCYCLE_API_URL=http://localhost:8000 npx next start -p 3004

# terminal 3: capture
cd web && npm run screenshots -- http://localhost:3004 ../docs/demo/screenshots
```

Needs Chrome (set `CHROME_PATH` if it is not at the macOS default) and network access (satellite map tiles).
The list of shots is at the top of `web/scripts/capture-screenshots.mjs`.

**Without the API** the web app has no weather or soil values: the comparison says "not enough evidence" for
every field and the profile shows labelled sample weather. Do not use that mode for the deck.

To check what the API reads before capturing: `uv run python -m api.check_clickhouse primary-001`.

## Rules for the deck

- Do not claim yield, profit or measured soil outcomes. The app does not, and the engine refuses to.
- "Not enough evidence" is the product working as designed, and shots 09 and 10 show why. The PRD scores
  uncertainty and abstention (`PRD.md` §8.3, §12).
- Say plainly that all 45 fields are demonstration polygons, that the weather is a 50 km model and not a
  station, and that no farmer or adviser has reviewed the app.
