# Validation

Run 2026-11-15, headless Chrome, production build.

| Check | Result |
|---|---|
| `pytest api`: new `test_imagery.py` (20 tests) | 96 pass in `api/`. Covers the warp to longitude/latitude, colours kept, transparent edge, size cap, refusal of non-colour, 16-bit and non-GeoTIFF chips, checksum mismatch, key outside `raw/naip/`, padded-bytes checksum, parameterised query, 404 and 503 behaviour, `/api/v1` mount |
| `ruff`, `tsc`, ESLint (0 errors), Prettier, Vitest | Clean; 226 web tests (9 new for the contract and the flight-date wording) |
| Stand-in photo: a UTM chip with the primary field's own polygon painted yellow, served by the real API and the real web proxy | The yellow shape sits inside the outline the map draws for that field; edges meet it |
| Field with no photo | No toggle |
| Toggle on and off; caption names two flight dates for a two-tile field | Yes |
| Phone width | Toggle present |

## Not verified

- **The real photo.** There were no S3 or ClickHouse credentials in this session, so the real chips were never read. `python -m api.check_imagery primary-001` is the check: open the PNG and compare it with the map.
- The chip's real CRS and band order (assumed UTM 15N, bands 1 to 3 = red, green, blue as DE's manifest says). A different layout is refused or would show wrong colours, which the check would reveal.
- NAIP licence for public display (unconfirmed by DE).
- A first run where the map did not zoom when the toggle was pressed with the map below the fold in headless Chrome; it zoomed correctly with the map in view. Not reproduced in view.
