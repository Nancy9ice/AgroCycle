# Plan: Landing-page design

- **Role:** FE
- **Spec created:** 2026-11-15
- **Roadmap phase and task:** Phase 7, FE: landing-page visual design

## Goal
Create a distinctive, simple agricultural landing page with a photographic hero, text overlay and graceful scroll transitions.

## Approach
Use an original generated aerial farmland background, cream and forest surfaces, editorial typography and varied section compositions. Each section stays in its existing feature file. A shared progressive-enhancement reveal component handles viewport entry, reduced motion, anchor navigation and keyboard focus; static content remains visible without JavaScript. Preserve the app flow, strategy definitions and evidence caveats. Keep new custom icons in `.ts`.

## Files and steps
1. Generate and save an optimized hero image under `web/public/images/`, recording its origin and prompt.
2. Add scoped home styles and a shared reveal component; redesign the hero and six section files. Keep non-home layouts stable.
3. Run frontend checks and inspect desktop/mobile layouts, navigation, animation and reduced-motion/no-JavaScript behavior in a local browser.
4. Record validation and update the roadmap.

## Dependencies and interfaces
Static home content; no API or data pipeline dependency. Uses installed Next.js, React and Tailwind. No animation package or external image service.

## Risks
Maintain readable photo overlays, prevent motion-related discomfort, preserve evidence labels and demo scope, and avoid suggesting illustrative imagery is real field observation. Keep image download and animation costs bounded.

## Desktop spacing refinement
At the user’s request, desktop horizontal padding uses 3vw with a 48 px maximum, half the initial value. Tablet and phone padding are unchanged.

## Navigation follow-up
Keep the server-rendered navigation composition and add a shared client header shell that tracks scroll direction through a passive, animation-frame-throttled listener. On the landing page, preserve the transparent hero header at the top; use a solid fixed header while scrolled, revealing on upward scroll and hiding on downward scroll. Keep it visible near the top, with focused controls or an open menu; respect reduced motion. Other pages retain their sticky header.
