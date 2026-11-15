# Screenshots for the 7-slide deck

The submission is a 7-slide deck with **real screenshots from the working app** (`PRD.md` §13). This folder
holds a repeatable capture of every screen, and says exactly what each picture is. The deck must say the same.

> **Read this first.** No field has computed weather, soil or greenness values yet, so the app's honest result
> today is _"We cannot compare these options for this field yet"_ for every field. Three of the pictures below
> use clearly labelled sample values so the other screens can be shown. Each says so on the page itself, and the
> label must stay in the frame. Do not crop it out, and do not call these pictures results.

## What each picture is

Status key: **Real** = the app's actual output today. **Labelled sample** = the page says "sample" on it.
**Preview** = sample indicator values, with a banner saying so.

| File                                     | Screen                              | Status                                                                | What it shows                                                                                               |
| ---------------------------------------- | ----------------------------------- | --------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `01-home.png`                            | Home                                | Real                                                                  | The decision, three options, how it works, the honesty rules                                                |
| `02-field-map.png`                       | Choose a field                      | Real                                                                  | 45 demonstration polygons in Story and Boone counties on satellite imagery; geometry checked                |
| `03-profile.png`                         | Field profile                       | Real crop history and soil; **labelled sample** weather and greenness | Where each number comes from, scale, and what is missing                                                    |
| `04-evidence-drawer.png`                 | Evidence drawer                     | Real (crop history)                                                   | The provenance record behind one output: source, precision, gaps, evidence type                             |
| `05-priorities.png`                      | Priorities and constraints          | Real                                                                  | 12 optional questions; four feed the engine, three are recorded for an adviser                              |
| `06-compare-real-result.png`             | Comparison                          | **Real result: not enough evidence**                                  | Abstention with reasons, three options, every outcome shown, nothing treated as neutral                     |
| `07-compare-preview-worth-exploring.png` | Comparison                          | **Preview** (sample banner at top)                                    | The "worth exploring" outcome, the Iowa-trial figures, evidence types, cautions                             |
| `08-compare-preview-with-caveats.png`    | Comparison                          | **Preview** (sample banner at top)                                    | A comparison with caveats; no manure makes the nitrogen result not carry over while herbicide still applies |
| `09-compare-outside-domain.png`          | Comparison, a continuous-corn field | Real                                                                  | A field outside the evidence: no option is offered, every outcome says it does not carry over               |
| `10-adviser-brief.png`                   | Brief for an adviser                | Real                                                                  | One printable page: result, options, answers, questions to ask, sources                                     |
| `11-validation.png`                      | How we checked this                 | Real                                                                  | Four kinds of evidence kept apart; the one result that did not match the paper                              |

Screenshots are full-page and tall. Crop the section a slide needs, but keep any banner or label that applies to it.

## Slide map (`PRD.md` §13)

| Slide                                                                                  | What it must prove              | Use                                                                               | Gap to close                                                                                                                           |
| -------------------------------------------------------------------------------------- | ------------------------------- | --------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| 1. The decision and the changing context                                               | Specific problem                | `01-home` (top), `02-field-map`                                                   | None                                                                                                                                   |
| 2. Field profile from NASA and other data                                              | Best Use of Data                | `03-profile`                                                                      | **Weather and greenness are sample.** Re-take after DS2's indicator outputs exist (below). Until then say "sample values" on the slide |
| 3. What the indicators can and cannot establish; Marsden evidence                      | Best Use of Science             | `04-evidence-drawer`, the figures in `07`, `docs/method/ds2-scientific-method.md` | None for the figures; they are reproduced from the paper's supplement                                                                  |
| 4. Architecture and data lineage                                                       | Best Use of Technology          | **Not an app screenshot.** Draw the diagram                                       | The team draws it. The lineage text on screen is in the evidence drawers                                                               |
| 5. Comparison of the three strategies against priorities and constraints               | Best Use of Technology          | `05-priorities`, `06`, `07`, `08`                                                 | Say which are preview                                                                                                                  |
| 6. Benefits, trade-offs, uncertainties, qualified assessment or abstention, validation | Farmer-centred decision support | `06`, `09`, `10`, `11`                                                            | None                                                                                                                                   |
| 7. Limitations, stakeholder-feedback gap, impact pathway                               | Local Impact, honest claims     | `11-validation`, the limits section of `06`                                       | The stakeholder gap is stated on `11`; no farmer has reviewed the app yet                                                              |

## Reproduce

```bash
cd web
npm install
npm run build && npx next start -p 3004      # terminal 1: web app on its own engine copy
npm run screenshots -- http://localhost:3004 ../docs/demo/screenshots   # terminal 2
```

Needs Chrome (set `CHROME_PATH` if it is not at the macOS default) and network access (satellite map tiles).
The list of shots is at the top of `web/scripts/capture-screenshots.mjs`.

To capture through the API instead, run `make api` and start the web app with `AGROCYCLE_API_URL=http://localhost:8000`.

## Replacing the sample weather with real weather (slide 2)

1. DS2 or DE runs the indicator runner (`uv run python -m transform.indicators.runner`), which writes
   `data/out/indicators/field_indicators.csv` and `soil_properties.csv`.
2. Start the API with those outputs (`make api`; set `AGROCYCLE_INDICATORS_DIR` if they are elsewhere) and the
   web app with `AGROCYCLE_API_URL=http://localhost:8000`.
3. Re-run the capture. The profile then shows real weather means, each with its source and grid scale; the
   comparison can leave "not enough evidence" once the engine's four required indicators are known (the
   engine also needs `om_r_0_30cm`, soil organic matter).
4. Update the status column above: `03` and the comparison shots become real, and `07` and `08` stop being
   previews.

## Rules for the deck

- Never show a preview or sample picture as a result. The banner is part of the picture.
- Do not claim yield, profit or measured soil outcomes. The app does not, and the engine refuses to.
- "Not enough evidence" is the product working as designed. A slide that says so, and why, is a strength:
  the PRD scores uncertainty and abstention (`PRD.md` §8.3, §12).
- Say plainly that all 45 fields are demonstration polygons and no farmer has reviewed the app.
