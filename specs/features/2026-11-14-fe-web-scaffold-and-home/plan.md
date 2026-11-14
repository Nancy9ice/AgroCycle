# Plan: Web app scaffold and home page

- **Role:** fe
- **Spec created:** 2026-11-14
- **Roadmap phase and task:** Phase 7, FE: web scaffold and home page (first slice of "Frontend core")

## Goal
Stand up the `web/` Next.js app with a clean, scalable structure and design system, and build the landing (home) page that frames the decision, the three strategies, the flow, the evidence sources and the honesty rules. This is the entry point of the core journey (PRD §5.2).

## Approach
- Next.js (App Router, TypeScript strict, Tailwind v4). **Deviation from `specs/tech-stack.md`:** that file lists Next.js as a non-choice and specifies React + Vite. Next.js was chosen by the frontend owner at the start of the build; `tech-stack.md` is updated in this PR so the team sees the change.
- Feature-oriented layout: routes in `src/app` stay thin; page sections live in `src/features/<feature>`; shared UI primitives in `src/components`; shared domain data (strategies, evidence types) in `src/domain` so later screens reuse one source of truth.
- Design tokens live in `globals.css` (`@theme`), so components use semantic classes, never raw hex values.
- The home page is static content only. It shows no computed numbers, so nothing on it can be mistaken for a result. Later screens read typed mock JSON that matches the API contract until the FastAPI endpoints exist.
- Accessibility baseline: semantic landmarks, skip link, visible focus, 44 px targets, reduced-motion respect, no colour-only meaning.

## Files, tables and endpoints
- `web/` (new app): `src/app`, `src/components/{ui,layout,brand,evidence}`, `src/features/home`, `src/domain`, `src/lib`.
- `web/src/app/field/page.tsx`: a placeholder so the home call to action does not 404. Replaced by the field-selection task.
- `specs/tech-stack.md`: note the Next.js decision.
- `specs/roadmap.md`: tracker row for this task only.
- `Makefile`: `web-setup` and `web-check` targets.
- No tables or endpoints.

## Steps (in order)
1. Scaffold with `create-next-app`, then trim the boilerplate.
2. Design tokens, fonts, base styles.
3. Domain modules (strategies, evidence types) and shared primitives.
4. Site header and footer.
5. Home sections: hero, decision, strategies, how it works, honest outcomes, data sources.
6. Run lint, typecheck and build. Check the page in a browser at desktop and phone widths.

## Dependencies and interfaces with other roles
- None blocking. **BE** owns the API contract; FE will adopt generated types when the OpenAPI schema is published (Phase 2).
- Strategy definitions on the home page mirror PRD §2.2 (A, B, C). If DS2 changes the strategy profiles in Phase 9, update `web/src/domain/strategies.ts`.

## Risks and open questions
- Next.js 16 conventions differ from older versions (`cacheComponents` is enabled in the scaffold). Keep the home page fully static, and read the bundled docs in `web/node_modules/next/dist/docs/` before using data fetching.
- "Plan the switch" (step 5 of the flow) is in the design but not in the PRD core journey. It is listed on the home page as the last step and built last.
