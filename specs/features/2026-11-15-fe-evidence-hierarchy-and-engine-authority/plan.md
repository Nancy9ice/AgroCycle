# Plan: evidence hierarchy, adviser brief and API-as-authoritative-engine

## Roadmap phase and task
Phase 11, FE: comparison UI and adviser summary. Fixes reviewer items 5.2, 5.3 and 6.1 (engineering and integration review).

## Approach
1. **5.2 Evidence hierarchy.** One module, `features/compare/evidence-ledger.ts`, files everything in a comparison under one of six layers (`domain/evidence.ts`): looked up for your field, worked out from those, soil survey, Marsden experiment, published and not reproduced, assumed or unknown. The compare screen shows it in the open; each outcome card names its layer above the figure; sample-preview values are marked "sample".
2. **5.3 Adviser brief.** Add field identity and demonstration status, crop-history period and source, the ledger, strategy descriptions and needs, priorities and constraints (which are read by the rules), withheld and unassessed outcomes with reasons, and engine, rules, data and source versions. Say it is not a prescription or a plan. Show the decision's own `rules_version`, not the web copy's.
3. **6.1 One authoritative engine.** `getComparison` returns `provenance` (`api` or `offline_fallback`, rules version, data version, run time). The offline copy is labelled on screen and in the brief, and in production it refuses to answer unless `AGROCYCLE_ALLOW_OFFLINE_ENGINE=true`. The API's staleness test now compares the whole export, not just the version string.

## Files changed
`web/src/domain/evidence.ts`, `web/src/lib/api.ts`, `web/src/features/compare/{get-comparison,evidence-ledger,compare-screen}.ts(x)`, `web/src/features/compare/components/{evidence-ledger,engine-notice,outcome-cards}.tsx`, `web/src/features/plan/{plan-screen.tsx,brief-sources.ts}`, tests beside them, `api/tests/test_web_export_is_current.py`, `README.md`, `web/README.md`, `web/.env.example`.

## Dependencies and risks
- Needs `Comparison.profile`, fetched with the comparison. A profile failure must not take the comparison down; the brief says the period and source are unavailable instead.
- Production deployments without `AGROCYCLE_API_URL` now error. `docker-compose.yml` already sets it, so the deployed stack is unaffected.
