# Plan: Priorities and constraints form (step 3)

- **Role:** fe
- **Spec created:** 2026-11-14
- **Roadmap phase and task:** Phase 11, FE: constraints form (the form half of "Comparison UI + constraints form"; the comparison UI is a separate task)

## Goal

Let a farmer or adviser say what matters to them (priorities) and what is possible on the farm (constraints), in plain language, and carry those answers to the comparison. Constraints are first-class inputs (PRD §9), not footnotes.

## Approach

- **The questions follow the rules, not the other way round.** DS2's applicability rules (`docs/rules/strategy-profiles-and-applicability.md`, version 2026-11-14.1) read four farmer facts: `manure_access`, `forage_use_or_buyer`, `oat_use_or_buyer` and `small_grain_equipment_or_contractor`. Each has a question here. A pure function, `toEngineContext`, turns the answers into exactly those keys: yes becomes `true`, no becomes `false`, "not sure" or unanswered becomes `null`. **Unanswered is never "yes"**, so the engine abstains or qualifies instead of assuming.
- **Honest about what is used.** Three constraints from the PRD (hay equipment, storage, extra labour) and the five priorities have no rule yet. They are captured and shown as "Recorded for your adviser" or "Changes what we highlight", not presented as if they decide anything.
- **Answers live in the URL** (`?manure=no&soil=high`), so a result can be shared and survives a reload, as the design promised ("every result has a link you can share"). A small codec parses and validates the URL: unknown keys and values are dropped, so a hand-edited link cannot inject anything.
- **Native radio groups** inside a fieldset per question: arrow keys work, one answer at a time, and a "Clear answer" button returns a question to unanswered.
- **No free-text box.** The design's "anything else" field was not used by the engine, and free text does not belong in a shareable URL.
- Next step: "Compare strategies" goes to `/fields/[fieldId]/compare?...`, a placeholder that echoes the answers (unanswered shown as "Not provided") until the comparison UI is built.

## Files, tables and endpoints

- `web/src/features/priorities/` (question definitions, codec, engine-context mapping, form, summary, tests).
- `web/src/app/fields/[fieldId]/priorities/page.tsx` (replaces the placeholder), `.../compare/page.tsx` (placeholder).
- `web/src/lib/routes.ts`: `compareRoute`.
- No tables or endpoints. `POST /fields/{id}/compare` will receive the output of `toEngineContext`.

## Steps (in order)

1. Spec and tracker.
2. Question definitions, codec and engine-context mapping with tests.
3. Form, summary panel, screen.
4. Compare placeholder that reads the answers.
5. `npm run check`; browser check at desktop and phone widths.

## Dependencies and interfaces with other roles

- **DS2 (Phase 9, Done):** the four context keys and their True/False/None semantics come from `engine/rules/strategy_rules.py`. If DS2 renames a key or adds a rule input, update `engine-context.ts`.
- **BE (Phase 10, not started):** please confirm the compare request takes these four keys (nullable booleans) plus the priorities as optional low/medium/high values.
- **Farmer reviewer:** please sanity-check the wording of the questions for practicality.

## Risks and open questions

- "Limited manure" has no engine meaning (the rule is yes/no/unknown), so it is not an option. A farmer with a little manure should answer "Not sure" and ask an adviser; the form says so.
- The priorities have no effect on any rule yet; the form must not imply they do. Wording says they change what is highlighted first, which the comparison UI will implement.
