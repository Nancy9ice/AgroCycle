# Plan: Reusable SVG components

- **Role:** FE
- **Spec created:** 2026-11-15
- **Roadmap phase and task:** Phase 7, FE: reusable SVG components (maintenance)

## Goal
Keep SVG markup out of screen and layout files, making the existing artwork reusable without changing the design.

## Approach
Extract small icons and the current logo mark into `web/src/components/icons/`, with typed SVG props. Move the field patchwork SVG into `components/illustrations/`, leaving the figure and legend in the home feature. Give each illustration instance unique pattern IDs. Preserve the user's uncommitted hero and logo edits. No new dependency is needed.

Follow-up: icon modules use `.ts` and React `createElement` instead of JSX. Use Lucide only when its artwork matches the requested icon; otherwise create a custom `.ts` module. Keep current custom artwork and existing import paths.

## Files, tables and endpoints
Shared icon and illustration components; existing SVG call sites in brand, layout, home, field and profile components; import examples in `web/README.md`. No data or API changes.

## Steps (in order)
1. Extract the existing artwork and replace inline SVG call sites.
2. Run lint, typecheck, existing tests and a production build; review the diff and record results.

## Dependencies and interfaces with other roles
Uses the existing frontend and static content. This maintenance task needs no API or upstream data work and does not alter another role's interface.

## Risks and open questions
Preserve icon sizes, stroke widths, accessible names, native mobile-menu toggling and illustration labels. Keep shared components usable from both server and client components.
