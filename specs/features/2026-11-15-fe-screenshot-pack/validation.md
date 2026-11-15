# Validation: Screenshot pack and README

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
| --- | --- | --- |
| 1 Nine shots from one command | Run the script; list the output | Notes below |
| 2 Captions state data status | Read the guide against each image | Notes below |
| 3 Gaps stated | Read the guide | Notes below |
| 4 Nothing staged or edited | Compare with the live page; no image editing | Notes below |
| 5 Reproduction commands | Follow them on a clean checkout of the branch | Notes below |
| 6 README current | Read it | Notes below |
| 7 Check | `npm run check` | Command output |

## Results (fill in after implementation)

- **Date completed:** 2026-11-15 (implementation); items under "Failed or skipped" are still open
- **What was run:** `npm run build`, `next start`, then `npm run screenshots` against it (headless Chrome, 1280 px wide); every image was opened and looked at; `npm run check` -> 195 tests pass, lint and build clean.
- **Passed:**
  - 1: one command captured 11 screenshots (home, field map, profile, evidence drawer, priorities, three comparison states plus an outside-domain field, the adviser brief, validation).
  - 2: `docs/demo/README.md` gives each picture a status (real, labelled sample, preview) and what it proves; the preview shots keep their banner in frame (checked on `07`), and the profile and drawer shots show the "Sample values" label.
  - 3: the guide states that slide 4 is not an app screenshot, and lists the steps to replace the sample weather for slide 2 once DS2's outputs exist.
  - 4: nothing was edited or staged; the comparison's real state in the pack is the abstention the app actually gives today.
  - 5: reproduction commands are in the guide and are the ones used.
  - 6: the root README now describes the working build, the API and web run commands and the environment variables.
  - 7: the script lints, adds no dependency, and `npm run check` passes.
- **Bug found while capturing:** the first map shot was resized to the full page height, which left gaps in the imagery. The map is now photographed at window size.
- **Failed or skipped:**
  - **Slide 2 cannot show real weather yet.** No indicator outputs exist, so the profile shows labelled sample weather. This is the one picture the team must re-take.
  - Screenshots are of a development build on one machine; the map tiles come from Esri at capture time.
  - The pack is 7.8 MB of PNG in git. If that is a problem, remove `docs/demo/screenshots/` from git and regenerate.
  - The screenshots are full-page and very tall; slides will need crops.
  - Not done: the deck, the architecture and lineage diagrams, the scientific-method one-pager (DS2 has a draft in `docs/method/`).
- **Evidence location:** `docs/demo/screenshots/`, `docs/demo/README.md`.
- **Roadmap exit check met:** partly (Phase 15: the app's screenshots exist; the deck and diagrams are the team's).
- **Roadmap tracker updated:** yes, 2026-11-15 (left "In progress")
