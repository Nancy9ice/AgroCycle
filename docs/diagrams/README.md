# Diagrams for slide 4

Two figures for slide 4 of the deck (architecture and data lineage, `PRD.md` §13). Each makes one claim.

| File                                            | Claim it makes                                                                                                                                                                                                    |
| ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`architecture.png`](architecture.png)                         | Where the data goes from NASA and USDA sources to the screen, and **which parts are built and which are not**                                                                                                     |
| [`backend-architecture.svg`](backend-architecture.svg) / `.png` | How the FastAPI backend serves a request, layer by layer (middleware, routes, core logic and the decision engine, data access, ClickHouse, S3 and Claude), how it is deployed, and **which parts are merged, in an open pull request, or not built** |
| [`lineage.svg`](lineage.svg) / `.png`           | One indicator traced end to end: NASA daily temperatures become a count of very hot days per season, which the season summary shows with its caveats. No decision engine rule reads it |

The SVGs are vector (use them in the deck if it takes SVG); the PNGs are 2560 px wide for slides.

## What the marks mean

- **Solid green:** built and tested. **Amber:** built but not fully exercised. **Dashed red:** not built.
- An arrow's label says what moves along it. Dashed arrows are connections that do not exist yet.

## Status is a snapshot, written from the tracker

Status comes from `specs/roadmap.md` as of 2026-11-15:

- Sources, ingest, S3 and ClickHouse are done. Indicators, crop history, lineage and HLS valid-pixel counts are loaded.
- **transform** is amber: indicators and crop-history rules are built; HLS vegetation features (NDVI) are not.
- **FastAPI** is green: the engine and endpoints are built and tested, and on 2026-11-15 the ClickHouse reader was run against the live database (`python -m api.check_clickhouse`) and served real indicators for all 45 fields.
- Not built: HLS greenness features, Marsden tables in ClickHouse, the evidence and lineage endpoints, polygon upload.

To change a status, edit `build.py`, re-run, and re-export the PNGs:

```bash
python3 docs/diagrams/build.py        # also rewrites architecture.svg; delete it, architecture.png is maintained by hand
chrome --headless=new --hide-scrollbars --force-device-scale-factor=2 --window-size=1280,560 \
  --screenshot="docs/diagrams/lineage.png" "file://$PWD/docs/diagrams/lineage.svg"
# The backend diagram is taller and wider:
chrome --headless=new --hide-scrollbars --force-device-scale-factor=2 --window-size=1400,1130 \
  --screenshot="docs/diagrams/backend-architecture.png" "file://$PWD/docs/diagrams/backend-architecture.svg"
```

`backend-architecture` is a snapshot of `api/` as of 2026-11-15. Its numbers (22 endpoints merged, the rules version, the 5-minute cache) come from the code, so re-check them when those change. Amber marks the drawn-field work that was still in an open pull request when it was drawn: turn it green in `backend()` once that merges.

## Accuracy notes

- The lineage figure traces very hot days (`transform/indicators/climate.py`: 30 °C or more, 90 % valid-day threshold) and the season summary that shows it (`api/core/season_summary.py`). It shows that no engine rule reads the indicator. It used to trace growing degree days into a 300 degree-day climate rule; that rule was withdrawn on 2026-11-15 (see `engine/rules/strategy_rules.py`, section 6). If a rule starts reading a climate indicator, redraw `lineage()` in `build.py`.
- The "11 % low" rainfall figure is DS2's own comparison with the Iowa station record (`docs/sources/ds2-first-pull-review-2026-11-14.md`).
- Do not describe this as a validated pipeline. `docs/demo/README.md` and the validation page say what has and has not been checked.
