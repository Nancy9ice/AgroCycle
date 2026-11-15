# Validation: evidence hierarchy, adviser brief and engine authority

| Requirement | How verified |
|---|---|
| 1, 2, 4, 5 | `web/src/features/compare/evidence-ledger.test.ts` (12 tests), plus rendering the compare screen and reading the text. |
| 3, 6 | Rendered `/fields/primary-001/plan` and `/compare` and read the text; `web/src/features/plan/brief-sources.test.ts`. |
| 7, 8 | `web/src/features/compare/api-client.test.ts` (`getComparison` and "the offline engine in production"). |
| 9 | `api/tests/test_web_export_is_current.py`; the test body was run by hand against the committed files and against a reworded rule (detected). |

## Results (2026-11-15)
- Web: `tsc --noEmit` clean; `vitest` 251 tests pass; ESLint 0 errors (2 existing warnings in files not touched); Prettier clean on the files changed.
- Rendered the compare screen and the brief from the dev server with sample answers and read them end to end.
- The committed engine export was regenerated and compared: identical in content to what the Python engine produces now.
- **Not run:** `make check` and `uv run pytest` (no `uv` or pytest in the environment used). The logic of `test_web_export_is_current.py` was executed by hand with plain Python 3.9. **Run `make check` before marking this Done.** `next build` was not run either; run `npm run check` in `web/`.
