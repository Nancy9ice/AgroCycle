# Validation: Reusable SVG components

## Checks

| Requirement | Verification | Evidence |
|---|---|---|
| Extracted SVGs, preserved artwork and edits | Search remaining SVG call sites and review git diff | Shared components and final diff |
| Accessibility and interaction | Inspect SVG defaults and existing named controls/menu classes | Icon and call-site source |
| Reusable illustration IDs | Inspect instance ID and pattern references | Field illustration source |
| Compatibility | Lint, typecheck, existing tests, production build and changed-file formatting | Results below |

## Results
- **Date completed:** 2026-11-15
- **What was run:** `npm run lint`, `npm run typecheck`, `npm run test`, `npm run build`, Prettier checks on all changed frontend files, `git diff --check`, SVG call-site search and diff review. A one-off React server render exercised two illustration instances together.
- **Passed:** Typecheck; all 13 test files / 226 tests; changed-file formatting; diff whitespace check; production build including 190 generated pages. Lint exits successfully with no errors. Inline SVG markup now exists only in the shared SVG folders and the Next.js favicon. User hero and logo changes are preserved.
- **Reuse check:** Two illustrations rendered with 18 distinct pattern IDs and 18 matching fill references, preserving image roles and supplied classes. Decorative icon defaults, named controls and native menu toggle classes were inspected in source.
- **Warnings and limitations:** Existing unused `contextType` lint warning in `features/ask/ask-panel.tsx:20`. The first build hit a sandbox port-binding restriction; the retry retained that error in Turbopack's cache. A fresh build with the old cache saved under the system temporary directory and the necessary sandbox permission passed. No browser visual or screen-reader check was performed for this extraction.
- **Evidence location:** Commands and output in this session; source and feature spec in this branch.
- **Roadmap exit check met:** Yes for this maintenance task. Phase 7's broader real-data profile exit check is not claimed.
- **Roadmap tracker updated:** Yes, 2026-11-15.

## Follow-up: `.ts` icon modules
- Converted all nine icon modules from `.tsx` to `.ts` using React `createElement`, retaining props, SVG paths, colours and extension-free imports.
- Documented the matching rule: use Lucide only when it fits; create a custom `.ts` icon otherwise. Existing custom icons remain in use.
- Re-ran typecheck, lint, all 226 tests, formatting checks for the icons and README, whitespace checks and the production build (190 generated pages). All pass; lint retains the one existing `ask-panel.tsx` warning.
- Confirmed `components/icons/` contains no `.tsx` files. Illustration components remain `.tsx`.
- Roadmap maintenance task returned to Done on 2026-11-15.
