#!/usr/bin/env python3
"""Draws the two slide-4 diagrams as standalone SVG files. Standard library only.

    python3 docs/diagrams/build.py

The SVGs are the output; this script is the source, so a status change is a one-word edit here and a rerun.
Status must match `specs/roadmap.md`. Fixed light colours on a white ground on purpose: these are images for
slides, not themed pages.
"""
from __future__ import annotations

from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parent

INK, SOFT, FAINT = "#16201a", "#3b463f", "#5b665f"
BUILT, BUILT_FILL = "#235032", "#e1eddf"
PARTLY, PARTLY_FILL = "#8a5d0f", "#f6ebcd"
NOT, NOT_FILL = "#8f432a", "#f4e2d9"
EXTERNAL, EXTERNAL_FILL = "#5b665f", "#efede3"
FONT = "Geist, 'Helvetica Neue', Arial, sans-serif"


class Svg:
    def __init__(self, width: int, height: int, title: str, label: str):
        self.w, self.h, self.title, self.label = width, height, title, label
        self.parts: list[str] = []

    def add(self, markup: str) -> None:
        self.parts.append(markup)

    def text(self, x, y, content, size=13, weight=400, fill=INK, anchor="start", mono=False):
        family = "ui-monospace, Menlo, monospace" if mono else FONT
        self.add(
            f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}">{escape(content)}</text>'
        )

    def box(self, x, y, w, h, stroke, fill, dashed=False, radius=10, width=2):
        dash = ' stroke-dasharray="6 5"' if dashed else ""
        self.add(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{width}"{dash}/>'
        )

    def arrow(self, x1, y1, x2, y2, label=None, dashed=False, color=INK, label_dy=-8):
        dash = ' stroke-dasharray="5 4"' if dashed else ""
        self.add(
            f'<line x1="{x1}" y1="{y1}" x2="{x2 - 7}" y2="{y2}" stroke="{color}" stroke-width="2"{dash}/>'
            f'<polygon points="{x2},{y2} {x2 - 9},{y2 - 5} {x2 - 9},{y2 + 5}" fill="{color}"/>'
        )
        if label:
            self.text((x1 + x2) / 2, y1 + label_dy, label, size=11, weight=600, fill=SOFT, anchor="middle")

    def arrow_left(self, x1, y1, x2, y2, label=None, color=INK, label_dy=-8):
        """Like `arrow`, but the head is at the left end (x2 < x1)."""
        self.add(
            f'<line x1="{x1}" y1="{y1}" x2="{x2 + 7}" y2="{y2}" stroke="{color}" stroke-width="2"/>'
            f'<polygon points="{x2},{y2} {x2 + 9},{y2 - 5} {x2 + 9},{y2 + 5}" fill="{color}"/>'
        )
        if label:
            self.text((x1 + x2) / 2, y1 + label_dy, label, size=11, weight=600, fill=SOFT, anchor="middle")

    def render(self) -> str:
        body = "\n  ".join(self.parts)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
            f'width="{self.w}" height="{self.h}" role="img" aria-label="{escape(self.label)}">\n'
            f"  <title>{escape(self.title)}</title>\n"
            f'  <rect width="{self.w}" height="{self.h}" fill="#ffffff"/>\n  {body}\n</svg>\n'
        )


STATUS = {
    "built": (BUILT, BUILT_FILL, "Built"),
    "partly": (PARTLY, PARTLY_FILL, "Partly built"),
    "not": (NOT, NOT_FILL, "Not built"),
    "external": (EXTERNAL, EXTERNAL_FILL, "External"),
}


def stage(svg, x, y, w, h, title, lines, status, note=None, dashed=False):
    stroke, fill, label = STATUS[status]
    svg.box(x, y, w, h, stroke, fill, dashed=dashed or status == "not")
    svg.text(x + w / 2, y + 28, title, size=15, weight=700, anchor="middle")
    for i, line in enumerate(lines):
        svg.text(x + w / 2, y + 50 + i * 16, line, size=11.5, fill=SOFT, anchor="middle")
    svg.text(x + w / 2, y + h - 12, label if note is None else note, size=11, weight=700, fill=stroke, anchor="middle")


def architecture() -> Svg:
    svg = Svg(
        1280,
        560,
        "AgroCycle architecture",
        "Data flows left to right from NASA and USDA sources through ingest, S3, transform and ClickHouse to the "
        "API and the web app. Everything on the main path is built; the greenness features, the Marsden "
        "load and three endpoints are not.",
    )
    svg.text(24, 34, "Where the data goes, and what is built", size=20, weight=700)
    svg.text(
        24, 56, "Solid green: built and tested.  Amber: built, not fully exercised.  Dashed red: not built.",
        size=12, fill=FAINT,
    )

    y, h, w = 96, 150, 130
    gap = 52
    xs = [24 + i * (w + gap) for i in range(7)]
    stage(svg, xs[0], y, w, h, "Sources", ["NASA POWER, HLS", "USDA CDL, SSURGO", "Marsden paper data"], "external")
    stage(svg, xs[1], y, w, h, "ingest/", ["Python job per", "source, with a", "checksum manifest"], "built")
    stage(svg, xs[2], y, w, h, "S3 raw", ["never edited", "738 files, plus", "HLS (210 MB)"], "built")
    stage(svg, xs[3], y, w, h, "transform/", ["clean, indicators,", "crop-history rules", "(no HLS features)"], "partly", note="Partly built")
    stage(svg, xs[4], y, w, h, "ClickHouse", ["curated tables,", "indicator lineage,", "crop history"], "built")
    stage(svg, xs[5], y, w, h, "FastAPI", ["profile, compare,", "with the decision", "engine inside"], "built")
    stage(svg, xs[6], y, w, h, "Web app", ["map, profile,", "comparison,", "adviser brief"], "built")

    mid = y + 62
    labels = ["pull", "upload", "clean", "load", "read", "JSON"]
    for i, label in enumerate(labels):
        svg.arrow(xs[i] + w, mid, xs[i + 1], mid, label)

    # What is not built, hanging under the stage it would feed.
    ny, nh = 330, 112
    stage(svg, xs[3] - 12, ny, w + 24, nh, "Greenness features", ["HLS images are in S3", "and counted; NDVI", "not computed"], "not")
    stage(svg, xs[4] - 12, ny, w + 24, nh, "Marsden tables", ["figures are computed", "in code, not yet", "loaded here"], "not")
    stage(svg, xs[5] - 12, ny, w + 24, nh, "More endpoints", ["evidence, lineage,", "polygon upload", ""], "not")
    svg.arrow(xs[3] + w / 2, ny, xs[3] + w / 2, y + h + 4, dashed=True, color=NOT)
    svg.add(f'<polygon points="{xs[3] + w / 2},{y + h + 4} {xs[3] + w / 2 - 5},{y + h + 14} {xs[3] + w / 2 + 5},{y + h + 14}" fill="{NOT}"/>')
    svg.text(xs[3] + w / 2 + 8, 292, "would feed", size=11, weight=600, fill=NOT)

    # The claims the design rests on.
    svg.box(24, 462, 1232, 78, "#bdb9a6", "#faf9f4", radius=10, width=1)
    svg.text(44, 488, "At request time the app reads curated data only. No call to NASA or USDA is in the request path, so the demo cannot fail on a live service.", size=12.5, fill=INK)
    svg.text(44, 510, "The decision engine is a pure function: the same field and the same answers always give the same result. It returns \"worth exploring\", a comparison with caveats, or", size=12.5, fill=INK)
    svg.text(44, 528, "\"not enough evidence\". It never returns a score, a ranking or a winner.", size=12.5, fill=INK)
    return svg


def lineage() -> Svg:
    svg = Svg(
        1280,
        560,
        "From a NASA observation to the number on screen",
        "One indicator traced end to end: NASA POWER daily highest temperatures become a count of very hot "
        "days per season, which the season summary shows with its caveats. No decision engine rule reads it.",
    )
    svg.text(24, 34, "One indicator, from a NASA observation to the number on screen", size=20, weight=700)
    svg.text(24, 56, "Very hot days: how it is made, where it is shown, and what does not read it.", size=12, fill=FAINT)

    y, h = 96, 156
    stage(svg, 24, y, 210, h, "NASA POWER weather", ["daily highest and lowest", "air temperature,", "grid cell about 50 km"], "built", note="Evidence: model estimate")
    stage(svg, 318, y, 210, h, "Very hot days", ["per season, Apr to Nov", "days at 30 °C or more", "unknown if < 90 % of days"], "built", note="Evidence: derived")
    stage(svg, 612, y, 210, h, "Highest and lowest season", ["the 11 seasons compared", "never added into a score", "unknown seasons left out"], "built", note="season summary")
    mid = y + 70
    svg.arrow(234, mid, 318, mid, "per season")
    svg.arrow(528, mid, 612, mid, "compare")

    # Who reads it.
    rx, rw = 906, 350
    svg.box(rx, y - 12, rw, 292, BUILT, "#ffffff", width=2)
    svg.text(rx + rw / 2, y + 12, "Who reads it", size=15, weight=700, anchor="middle")
    svg.text(rx + rw / 2, y + 30, "and what each does with it", size=11, fill=FAINT, anchor="middle")
    rows = [
        ("the season summary screen", "Shown, with its caveats", BUILT, BUILT_FILL),
        ("a season with too little data", "Shown as unknown, never zero", PARTLY, PARTLY_FILL),
        ("the decision engine's rules", "No rule reads it", NOT, NOT_FILL),
        ("the outcome banner", "Not changed by it", NOT, NOT_FILL),
    ]
    for i, (condition, effect, stroke, fill) in enumerate(rows):
        ry = y + 46 + i * 56
        svg.text(rx + 16, ry + 14, condition, size=12, weight=600, fill=SOFT)
        svg.box(rx + 16, ry + 22, rw - 32, 26, stroke, fill, radius=7, width=1.5)
        svg.text(rx + 28, ry + 40, effect, size=12.5, weight=700, fill=stroke)
    svg.arrow(822, mid, 906, mid, "shown by")

    # What the reader sees.
    svg.box(24, 292, 798, 92, "#bdb9a6", "#faf9f4", radius=10, width=1)
    svg.text(44, 318, "On screen", size=14, weight=700)
    svg.text(44, 340, "The compare page shows hot days per season and the highest and lowest season, and says what it counts.", size=12.5)
    svg.text(44, 360, "Every number opens \"Where this comes from\": source, grid scale, what is missing, and the lineage record.", size=12.5)
    svg.arrow_left(rx, 338, 822, 338, "caveats", label_dy=-8)

    svg.box(24, 410, 1232, 128, "#bdb9a6", "#faf9f4", radius=10, width=1)
    svg.text(44, 436, "What to be honest about", size=14, weight=700)
    notes = [
        "The 30 °C line is a team proposal that no agronomist has reviewed. It counts whole seasons and says nothing about crop stage.",
        "POWER is a model on a 50 km grid, not a weather station. Against the Iowa station it ran about 11 % low on rainfall.",
        "A climate rule built on growing degree days was withdrawn on 2026-11-15: its band had no published basis and could never fire.",
        "Missing data is never read as good news: an unknown season is left out, never counted as zero.",
    ]
    for i, line in enumerate(notes):
        svg.text(44, 460 + i * 20, "•  " + line, size=12.5, fill=INK)
    return svg


def _group(svg, x, y, w, h, title, subtitle=None):
    """A frame around a layer, with its name in the top-left corner."""
    svg.box(x, y, w, h, "#bdb9a6", "#faf9f4", radius=12, width=1.5)
    svg.text(x + 16, y + 24, title, size=14, weight=700)
    if subtitle:
        svg.text(x + 16 + len(title) * 8.2 + 12, y + 24, subtitle, size=11.5, fill=FAINT)


def _chip(svg, x, y, w, h, title, lines, status="built", dashed=False):
    stroke, fill, _ = STATUS[status]
    svg.box(x, y, w, h, stroke, fill, dashed=dashed or status == "not", radius=8, width=1.6)
    svg.text(x + w / 2, y + 20, title, size=12.5, weight=700, anchor="middle")
    for i, line in enumerate(lines):
        svg.text(x + w / 2, y + 38 + i * 14.5, line, size=10.5, fill=SOFT, anchor="middle")


def _down(svg, x, y1, y2, label=None, color=INK, dashed=False):
    dash = ' stroke-dasharray="5 4"' if dashed else ""
    svg.add(
        f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2 - 7}" stroke="{color}" stroke-width="2"{dash}/>'
        f'<polygon points="{x},{y2} {x - 5},{y2 - 9} {x + 5},{y2 - 9}" fill="{color}"/>'
    )
    if label:
        svg.text(x + 10, (y1 + y2) / 2 + 4, label, size=11, weight=600, fill=SOFT)


def _up(svg, x, y1, y2, color=INK):
    """An arrow pointing up, from y1 (lower) to y2 (higher)."""
    svg.add(
        f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2 + 7}" stroke="{color}" stroke-width="2"/>'
        f'<polygon points="{x},{y2} {x - 5},{y2 + 9} {x + 5},{y2 + 9}" fill="{color}"/>'
    )


def backend() -> Svg:
    """System architecture of the backend: the parts and how they connect. Deliberately not a list of endpoints."""
    W, H = 1280, 660
    svg = Svg(
        W,
        H,
        "AgroCycle backend, system architecture",
        "A farmer's browser reaches Traefik, which serves the Next.js web app and the FastAPI API. The web app calls "
        "the API from its server. The API has routes, core logic, a pure decision engine and a data access layer. "
        "The data access layer reads and writes ClickHouse, reads aerial photos from S3 and calls Claude for the AI "
        "explanation. Separately, data pipelines run by the data team bring NASA and USDA data into S3 and ClickHouse.",
    )
    svg.text(24, 34, "AgroCycle backend: system architecture", size=20, weight=700)
    svg.text(24, 56, "Solid green: our code.  Grey: an external service.  Amber: run by a person, outside the API.", size=12, fill=FAINT)

    # The request path, left to right
    y = 150
    _chip(svg, 24, y, 150, 70, "Browser", ["the farmer or", "an adviser"], "external")
    _chip(svg, 214, y, 150, 70, "Traefik", ["HTTPS and routing"], "external")
    _chip(svg, 404, y, 170, 70, "Web app", ["Next.js, server-side"], "built")
    svg.arrow(174, y + 35, 214, y + 35, "")
    svg.arrow(364, y + 35, 404, y + 35, "")
    svg.text(489, y + 100, "calls the API from the server;", size=11, fill=SOFT, anchor="middle")
    svg.text(489, y + 115, "the browser never does", size=11, fill=SOFT, anchor="middle")

    # The API, with its four parts
    gx, gy, gw, gh = 636, 84, 340, 372
    _group(svg, gx, gy, gw, gh, "API", "FastAPI, /api/v1")
    parts = [
        ("Routes", ["HTTP endpoints (list at /docs),", "one error shape, request log"], "built"),
        ("Core logic", ["profiles, comparison, validation,", "rule register, AI explanation"], "built"),
        ("Decision engine", ["pure Python: the same input always", "gives the same result"], "built"),
        ("Data access", ["one interface; cached lookups;", "reads and writes the stores"], "built"),
    ]
    for i, (title, lines, status) in enumerate(parts):
        _chip(svg, gx + 16, gy + 40 + i * 83, gw - 32, 70, title, lines, status)
        if i < len(parts) - 1:
            _down(svg, gx + gw / 2, gy + 110 + i * 83, gy + 123 + i * 83)
    svg.arrow(574, y + 35, gx, y + 35, "")
    # Traefik also sends /api/* straight to the API: shown as a line over the top of the web app.
    svg.add(f'<path d="M 289 {y} L 289 112 L {gx} 112" fill="none" stroke="{SOFT}" stroke-width="1.6" stroke-dasharray="5 4"/>')
    svg.add(f'<polygon points="{gx},112 {gx - 9},107 {gx - 9},117" fill="{SOFT}"/>')
    svg.text(460, 104, "/api/* and /docs", size=11, weight=600, fill=SOFT, anchor="middle")

    # The stores and services the API uses
    sx, sw = 1030, 206
    _chip(svg, sx, 90, sw, 110, "ClickHouse", ["curated data, decision rules,", "saved comparisons, feedback", "and drawn boundaries"], "external")
    _chip(svg, sx, 226, sw, 86, "S3", ["raw files and the", "aerial photo chips"], "external")
    _chip(svg, sx, 338, sw, 86, "Claude (Anthropic)", ["wording of a stored", "result, on request"], "external")
    dx = gx + gw
    # The data access part reads and writes each store.
    ay = gy + 40 + 3 * 83 + 35
    for ty in (145, 269, 381):
        svg.add(f'<line x1="{dx - 16}" y1="{ay}" x2="{sx - 8}" y2="{ty}" stroke="{INK}" stroke-width="1.8"/>')
        svg.add(f'<polygon points="{sx},{ty} {sx - 10},{ty - 5} {sx - 10},{ty + 5}" fill="{INK}"/>')

    # The pipelines that fill the stores, outside the request path
    py = 500
    _group(svg, 24, py, 952, 120, "Data pipelines", "run by the data team, outside the API")
    _chip(svg, 40, py + 36, 190, 70, "Public sources", ["NASA POWER and HLS, USDA CDL,", "SSURGO and NAIP, Marsden data"], "external")
    _chip(svg, 290, py + 36, 150, 70, "Ingest", ["pull, checksum,", "store raw"], "built")
    _chip(svg, 500, py + 36, 190, 70, "Transform", ["clean, compute indicators,", "classify crop history"], "built")
    _chip(svg, 750, py + 36, 210, 70, "Drawn-boundary step", ["a person runs it per saved", "field; same pipeline"], "partly")
    svg.arrow(230, py + 71, 290, py + 71, "")
    svg.arrow(440, py + 71, 500, py + 71, "")
    svg.arrow(690, py + 71, 750, py + 71, "")
    # The pipelines load ClickHouse and S3: one line up the right-hand side, with a stub into each store.
    rail = sx + sw + 26
    svg.add(f'<path d="M 960 {py + 71} H {rail} V 145" fill="none" stroke="{INK}" stroke-width="2"/>')
    for ty in (145, 269):
        if ty != 145:
            svg.add(f'<line x1="{rail}" y1="{ty}" x2="{sx + sw + 8}" y2="{ty}" stroke="{INK}" stroke-width="2"/>')
        svg.add(f'<polygon points="{sx + sw},{ty} {sx + sw + 10},{ty - 5} {sx + sw + 10},{ty + 5}" fill="{INK}"/>')
    svg.add(f'<line x1="{rail}" y1="145" x2="{sx + sw + 8}" y2="145" stroke="{INK}" stroke-width="2"/>')
    svg.text(1000, py + 62, "loads", size=11, weight=600, fill=SOFT)

    svg.text(24, 640, "Run with docker compose on one server. GitHub Actions tests and deploys main.", size=11, fill=SOFT)
    return svg


def main() -> None:
    for name, svg in (("architecture", architecture()), ("lineage", lineage()), ("backend-architecture", backend())):
        (OUT / f"{name}.svg").write_text(svg.render(), encoding="utf-8")
        print(f"wrote docs/diagrams/{name}.svg")


if __name__ == "__main__":
    main()
