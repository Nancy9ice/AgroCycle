# Plan: Farmer-first flow (add your field, quick start, plain words, phone)

- **Role:** fe
- **Spec created:** 2026-11-15
- **Roadmap phase and task:** Phase 11 FE: review feedback from the team (items 2 to 9; item 1, the visual identity, is handled separately)

## Goal

A farmer arriving on the site should be invited to add their own field first, with the demo fields as an
explore option. The path must work on a phone, ask fewer things at once, and use words a farmer uses.

## Approach

1. **Add your field first (items 2, 6, 9).** The landing page's primary button and the closing CTA say "Add your field". `/field` opens on "My field": a map where the farmer draws a boundary by tapping its corners (or panning under a centre crosshair and pressing "Add corner here", which also works from the keyboard), plus "Use my location". A second tab, "Demo fields", is today's map and list.
2. **Honest about what happens next.** The boundary is checked in the browser with the existing FR-01 checks (inside Story or Boone, no self-crossing, area). The API can validate a drawn boundary (`POST /fields`) but does not store it or process any data for it (`is_preprocessed: false`, every source "not assessed"). So after a valid boundary the page says the evidence for new boundaries is not built yet and offers a demo field. It never shows another field's data as the farmer's. The location and the boundary stay in the browser.
3. **Quick start for the questions (item 7).** One button fills in a starting point: Medium for the five priorities and "Not sure" for the farm questions that offer it. "Not sure" is unknown to the engine, so nothing about the farm is invented. Every answer stays editable and there is a clear-all button.
4. **Say when the site is not connected (item 4).** Without `AGROCYCLE_API_URL` the web app has no data and every field says "not enough evidence". The compare page now says that the site is not connected to the data service, instead of implying the data does not exist.
5. **Plain words (item 8).** Rewrite the jargon a farmer meets on the home, field, profile, questions and result screens, keeping every evidence-type label and caution. Example: "Model estimate on a 0.5° × 0.625° grid" becomes "Weather for your area, not measured on your field".
6. **Phone check (item 3).** Walk every screen at 360 and 390 px with touch emulation: no sideways scroll, tap targets at least 44 px, the drawing map usable by tap.

## Out of scope

The visual identity (item 1). Storing a boundary and building its evidence (BE and DE; see requirements). Boundary file upload stays marked not available.
