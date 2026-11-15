# Plan: Make the screens and claims match real data

- **Role:** fe
- **Spec created:** 2026-11-15
- **Roadmap phase and task:** Phase 11/15 FE: claim check after the live ClickHouse check passed

## Goal

On 2026-11-15 the API was run against the live ClickHouse and read DE's real indicators: all 45 fields, 11 seasons. The comparison now leaves "not enough evidence" for most in-domain fields. Several sentences I wrote when no data existed are now false (the comparison page's "why is every field not enough evidence", the validation page's "every real result is not enough evidence", the README status, the weather shots marked sample). Correct them, keep every claim true in both modes (API on, API off), and re-take the screenshots from real data.

## Approach

- **Claims depend on the data state, not on a date.** The "why not enough evidence" note appears only when the engine lists indicators as unknown. The validation page's statements are reworded so they are true with and without the API ("where a field's measurements are missing, the comparison says not enough evidence").
- **Say what was observed, once, with its limits.** The validation page records the live result: with every constraint answered yes, 26 of 27 in-domain fields reach "worth exploring", all 18 out-of-domain fields abstain, and one in-domain field (`test-022`) is withheld because soil organic matter covers 96.7 % of its area. This is the engine run on the demonstration fields, not a validation.
- **Screenshots from the API on the live data**, and the guide's status column changes from "sample" and "preview" to "real" where that is now true. Preview shots are dropped; a shot of the withheld field is added, because refusing at 96.7 % coverage is the product's rule working.
- **Diagram status:** the FastAPI stage turns green once the live check has passed.

## Files

`web/src/features/compare/compare-screen.tsx` (+ test), `web/src/features/compare/components/preview-notice.tsx`, `web/src/features/validation/content.ts`, `web/scripts/capture-screenshots.mjs`, `docs/demo/`, `docs/diagrams/build.py`, root `README.md`.

## Risks and open questions

- The web app without `AGROCYCLE_API_URL` still has no indicator values (its local engine passes unknown), so it still says "not enough evidence" for every field. That is why the wording must hold in both modes.
- The screenshots depend on live data and on the demo constraints chosen; the guide records the answers used.
