# Requirements: Comparison UI (step 4)

## Covers

- **PRD requirements:** FR-09 (compare strategies across supported dimensions, unavailable ones shown), FR-10 (how constraints affect feasibility), FR-11 (comparison, qualified assessment or abstention with reasons, no forced ranking), FR-06, FR-12 (traceability), NFR-02, NFR-05, NFR-08. PRD 8.2, 8.3, 8.4, 8.5.
- **Roadmap exit check satisfied:** partly. The full core journey for the demo field (field, profile, priorities, compare) works; the plan step and API wiring remain.

## Inputs

- `/fields/[fieldId]/compare?<answers>` with optional `preview=sample`.
- The field (committed data), its profile (crop history, soil), the answers mapped by `toEngineContext`.
- DS2's rule table (`rules.generated.json`).

## Outputs

- The compare screen for all 45 demo fields.
- `getComparison(fieldId, answers, options) -> Decision` (stand-in for the API).

## Acceptance criteria

1. The screen shows exactly one of three outcomes, in words, with the engine's reason in plain language and the rules that drove it. It shows no number, rank, star or winner that combines strategies.
2. Today's default for every field is abstention because no required indicator is computed; the screen says so and still shows the three strategies, all outcomes (withheld ones marked) and the questions to resolve.
3. With `?preview=sample` the screen shows a persistent notice that climate and soil values are sample values, and can reach all three outcomes depending on the answers.
4. Three strategies are always shown side by side (stacked on a phone): rotation, why included, operational requirements, and a feasibility state (nothing rules it out / needs checking / not available on your farm) with reasons from the engine.
5. All nine outcomes are shown, each with a status in words (never colour only), an evidence-type badge, the statement when the engine allows one, and the caution (what may not be said) always. `abstained`, `out_of_domain` and `not_assessed` are never blank, zero or neutral.
6. Applied nitrogen and herbicide show the Marsden figures per strategy with units and the label "Experimental record, one site, nine seasons". Yield and profitability are attributed to the paper and say AgroCycle did not reproduce them.
7. A high priority tags the related outcomes and explains where nothing can be said. Priorities never change the outcome.
8. Each unknown in the result becomes a plain-language question; farmer questions link back to the form with answers preserved.
9. The standing limitations, rules version and "not expert-reviewed" are visible.
10. The TypeScript evaluator equals the real Python engine for 7 profiles x 81 constraint combinations (outcome, reason, unknowns, per-strategy feasibility and rules, per-outcome status and rules).
11. A field outside the domain (continuous corn, pasture, mixed) abstains and says why; unknown field id gives the not-found page.
12. `npm run check` passes; no horizontal scroll at 360, 390, 768, 1280 px; console clean.

## Evidence labels, scale and limitations to preserve

- Evidence type and source come from the rule table unchanged (`experimental`, `published`).
- Answers are `assumption / user input`; sample indicator values are labelled sample wherever they influence a result.
- No profitability, yield or soil-carbon claim of AgroCycle's own.

## Out of scope

The plan step (5), real indicator values, the API call, acting on priorities, saving or printing the result, accounts.
