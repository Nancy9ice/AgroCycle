# Plan: Comparison UI (step 4)

- **Role:** fe
- **Spec created:** 2026-11-14
- **Roadmap phase and task:** Phase 11, FE: comparison UI (the "side-by-side scenario view, benefits, trade-offs, evidence gaps and the outcome banner" half of "Comparison UI + constraints form")

## Goal

Show a farmer or adviser what the decision engine concluded for one field: one of the three PRD 8.3 outcomes (worth exploring, qualified comparison, abstention) with its reasons, the three strategies side by side, every outcome with its evidence type and what may not be said, and the questions still open. No score, no ranking, no winner.

## Approach

- **The UI renders the engine's `Decision`; it classifies nothing.** DS2's `engine/decision.py` (`assess(profile, constraints) -> Decision`, rules version 2026-11-14.2) is the contract. `features/compare/types.ts` mirrors it field for field, snake_case included, so swapping the stand-in for `POST /fields/{id}/compare` changes one file.
- **Stand-in engine, proven equal to the real one.** BE's endpoint does not exist yet and the engine is Python. A small TypeScript port (`evaluate.ts`, about 100 lines, rules only, no policy of its own) evaluates the rule table. `npm run sync:engine` runs the real Python engine and writes (a) the rule table as JSON, so no rule text is retyped, and (b) a fixture of its answers for 7 profiles x 81 constraint combinations. A unit test requires the port to match the fixture exactly. If DS2 changes a rule, re-running the sync either updates the table or fails the test.
- **Honest default: abstention.** The engine needs four indicators (`gdd`, `precipitation_total`, `frost_window`, `om_r_0_30cm`) to be known. None is computed for any field yet, so today the real result for every field is abstention. The screen shows exactly that, with the rest of the structure (strategies, withheld outcomes, caveats, questions) intact.
- **Optional preview with sample values.** A switch (`?preview=sample`) feeds the engine sample indicator values so the other two outcomes can be seen. It is off by default and a persistent banner says the climate and soil values are sample values, not this field's.
- **Priorities highlight, they do not decide.** The engine records priorities and ignores them (DS2 spec, criterion 10). The screen tags outcomes related to a high priority and says plainly where we have nothing to say (for example soil health is a high priority but soil carbon and erosion are not assessed).
- **Unknown is shown as unknown.** `abstained` and `not_assessed` both render as "Not assessed" with the reason; never blank, zero or neutral.
- Plain language over rule ids; rule ids and the engine's own reason sit in a "How this was decided" disclosure for advisers.

## Files, tables and endpoints

- `web/scripts/export_engine.py`, `npm run sync:engine`; generated `features/compare/data/rules.generated.json` and `engine-parity.generated.json`.
- `web/src/features/compare/` (types, rules loader, `evaluate.ts`, profile mapping, `get-comparison.ts`, Marsden figures, labels, components, tests).
- `web/src/app/fields/[fieldId]/compare/page.tsx` (replaces the placeholder).
- No tables. Stand-in for `POST /fields/{id}/compare`.

## Steps (in order)

1. Spec and tracker.
2. Export script; types; evaluator; parity test.
3. Field-to-profile mapping and `getComparison`.
4. Components: outcome banner, strategies, outcome cards, priorities, questions, limitations.
5. Page and route; `npm run check`; browser checks at 360, 390, 768, 1280 px for abstention and preview.

## Dependencies and interfaces with other roles

- **DS2:** the `Decision` shape and rule table. The TS port must change when `decision.py` changes semantics (the parity fixture will fail first).
- **BE:** please serialise `Decision` with `dataclasses.asdict` (snake_case), `UNKNOWN` as `null`. `Decision.unknowns` is a list of context keys and `indicator <id>` strings.
- **DS1:** `crop_history_is_maize_soybean` comes from DE's `field_class` (`rotation` = true). The four required indicators need to be computed per field before the engine can leave abstention.
- **Farmer reviewer:** plain-language wording of outcomes, strategy cards and adviser questions.

## Risks and open questions

- Marsden figures (74.5 / 56.6 / 40.8 kg N/ha/yr; 1.925 / 0.261 / 0.195 kg ai/ha/yr) are shown as numbers per strategy. They are typed once in `marsden-figures.ts` and a test checks each appears in DS2's statement, so they cannot drift.
- `candidate_strategies`/`strategy_worth_exploring` is reachable only with every claimable outcome in domain and no unknown, which needs all constraints answered "yes". That is the engine's rule, not the UI's.
- Required-indicator set is DS2's judgement; the preview mode fakes it only for display.
