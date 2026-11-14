# Plan: Accessibility and keyboard pass

- **Role:** fe
- **Spec created:** 2026-11-14
- **Roadmap phase and task:** Phase 11/13 FE polish; closes the "keyboard, screen reader" items left open in the field-selection, profile, priorities, comparison and brief specs (PRD NFR-08)

## Goal

Find and fix what stops a keyboard or screen-reader user finishing the journey, and record honestly what was and was not tested.

## Approach

- **Automated:** run axe-core (WCAG 2.0/2.1 A and AA rules, including colour contrast) in headless Chrome on the built app for every page and the main states: home, field, profile, priorities, compare (abstention and preview), brief, validation, not-found.
- **Keyboard walk:** scripted Tab presses on the same pages, recording each stop's role and accessible name, whether a focus ring is visible, and whether anything keyboard-reachable has no name. Check the skip link, radio groups with arrow keys, the provenance drawer (opens, traps focus, Escape closes and returns focus), and the map's list alternative.
- **Fix what is found** at the component, not the page, and re-run.
- **Not claimed:** a real screen reader (VoiceOver, NVDA) was not run. Automated checks catch about a third of problems; the page will say so in this spec's results and nowhere else claims WCAG conformance.

## Files, tables and endpoints

Components found at fault; no new files expected. Scripts live in the scratchpad.

## Steps (in order)

1. Spec.
2. Axe run and keyboard walk; list findings.
3. Fix; re-run; `npm run check`.
4. Record results here and in the earlier specs' open items.

## Dependencies and interfaces with other roles

None. DS2's caution strings contain jargon that is readable but not plain; that is a wording issue, not an accessibility one, and is noted elsewhere.

## Risks and open questions

- Axe cannot judge reading order, meaningful link text in context, or whether the map is usable without a mouse beyond the list alternative.
- Map keyboard operation relies on MapLibre's controls plus the field list; the list is the accessible path.
