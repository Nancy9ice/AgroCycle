# Plan: Screenshot pack for the 7-slide deck, and a current README

- **Role:** fe
- **Spec created:** 2026-11-15
- **Roadmap phase and task:** Phase 15, claim check and slide-deck prep (the app's side: real screenshots, PRD §13)

## Goal

The submission is a 7-slide deck with **real screenshots from the working app** (PRD §13). Give the team a repeatable way to capture them, a caption for each that says exactly what the picture is (real, sample or fixture), and a map from slide to screenshot. Also make the root README describe the project as it now is.

## Approach

- **One script captures every shot from the running app** (`web/scripts/capture-screenshots.mjs`): headless Chrome over the DevTools protocol, no new dependencies. Re-run it after DS2's indicator outputs land and the weather screenshots become real.
- **Each screenshot's caption states its data status.** Four kinds, never blurred: *real* (the app's actual output today), *labelled sample* (the app says "sample" on the page), *preview* (sample indicator values, banner on the page), *fixture* (not used for the deck). Slide 2's weather picture is the one the team must replace; until DS2's real outputs exist the best honest shot is "labelled sample" or "weather not loaded", and the guide says which.
- **No staging of results.** Screenshots use the app's real states. The comparison's real state today is "not enough evidence"; the all-yes "worth exploring" shot is taken in preview mode and its banner stays in the frame.
- **Slide map** from PRD §13: which slides an app screenshot can serve (1, 2, 3, 5, 6, 7) and which it cannot (slide 4: architecture and lineage diagram, which the team draws).
- **README** brought up to date: status, repository layout (api, engine and web are no longer placeholders), how to run the API and the web app, and the environment variables.

## Files, tables and endpoints

- `web/scripts/capture-screenshots.mjs`, `docs/demo/README.md` (guide and captions), `docs/demo/screenshots/*.png`.
- Root `README.md`; `web/package.json` (`screenshots` script).
- No tables or endpoints.

## Steps (in order)

1. Spec and tracker.
2. Capture script.
3. Run it against the production build; look at every image.
4. Write captions and the slide map.
5. README; `npm run check`.

## Dependencies and interfaces with other roles

- **DS2 and DE:** weather screenshots become real only when `data/out/indicators/` exists. Until then the guide says what to show.
- **Whoever builds the deck:** slide 4 diagram, the scientific-method one-pager, and the validation examples are not app screenshots.

## Risks and open questions

- Screenshots are of a development build on one machine: map tiles need network access; the map shot will show whatever Esri serves.
- The script needs Chrome; the path is read from `CHROME_PATH` (default is the macOS location).
