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
    stage(svg, xs[5], y, w, h, "FastAPI", ["profile, compare,", "with the decision", "engine inside"], "partly", note="Not run on live DB")
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
        "From a NASA observation to the outcome on screen",
        "One indicator traced end to end: NASA POWER daily temperatures become growing degree days, then a "
        "difference from the Iowa trial site, which the decision engine's rules turn into either no effect, a "
        "caveat on every outcome, or withholding every outcome.",
    )
    svg.text(24, 34, "One indicator, from a NASA observation to the outcome on screen", size=20, weight=700)
    svg.text(24, 56, "Warmth for crop growth: how it is made, and the three things it can do to the result.", size=12, fill=FAINT)

    y, h = 96, 156
    stage(svg, 24, y, 210, h, "NASA POWER weather", ["daily highest and lowest", "air temperature,", "grid cell about 50 km"], "built", note="Evidence: model estimate")
    stage(svg, 318, y, 210, h, "Growing degree days", ["per season, Apr to Nov", "base 10 °C, capped 30 °C", "unknown if < 90 % of days"], "built", note="Evidence: derived")
    stage(svg, 612, y, 210, h, "Gap to the Iowa site", ["mean of the seasons, against", "the research farm's record", "unknown if no usable season"], "built", note="degree-day difference")
    mid = y + 70
    svg.arrow(234, mid, 318, mid, "per season")
    svg.arrow(528, mid, 612, mid, "average")

    # The engine's rules.
    rx, rw = 906, 350
    svg.box(rx, y - 12, rw, 292, BUILT, "#ffffff", width=2)
    svg.text(rx + rw / 2, y + 12, "Decision engine rules", size=15, weight=700, anchor="middle")
    svg.text(rx + rw / 2, y + 30, "each names the rule it fired", size=11, fill=FAINT, anchor="middle")
    rows = [
        ("over 300 degree-days", "Caveat on every outcome", PARTLY, PARTLY_FILL),
        ("unknown", "Caveat: the gap is named", PARTLY, PARTLY_FILL),
        ("any required indicator missing", "Every outcome withheld", NOT, NOT_FILL),
        ("300 or less", "No effect", BUILT, BUILT_FILL),
    ]
    for i, (condition, effect, stroke, fill) in enumerate(rows):
        ry = y + 46 + i * 56
        svg.text(rx + 16, ry + 14, "if " + condition, size=12, weight=600, fill=SOFT)
        svg.box(rx + 16, ry + 22, rw - 32, 26, stroke, fill, radius=7, width=1.5)
        svg.text(rx + 28, ry + 40, effect, size=12.5, weight=700, fill=stroke)
    svg.arrow(822, mid, 906, mid, "rules read it")

    # What the reader sees.
    svg.box(24, 292, 798, 92, "#bdb9a6", "#faf9f4", radius=10, width=1)
    svg.text(44, 318, "On screen", size=14, weight=700)
    svg.text(44, 340, "The banner says one of three things: worth exploring, a comparison with caveats, or not enough evidence.", size=12.5)
    svg.text(44, 360, "Every number opens \"Where this comes from\": source, grid scale, what is missing, and the lineage record.", size=12.5)
    svg.arrow_left(rx, 338, 822, 338, "banner", label_dy=-8)

    svg.box(24, 410, 1232, 128, "#bdb9a6", "#faf9f4", radius=10, width=1)
    svg.text(44, 436, "What to be honest about", size=14, weight=700)
    notes = [
        "The 300 degree-day band is a team guess with no published basis. DS2 calls it the weakest rule in the table, and it only adds a caveat.",
        "POWER is a model on a 50 km grid, not a weather station. Against the Iowa station it ran about 11 % low on rainfall.",
        "Growing degree days say how warm it was, not when a crop was planted or how it yielded. The app claims no yield or profit.",
        "Missing data is never read as good news: an unknown here makes the result more cautious, never less.",
    ]
    for i, line in enumerate(notes):
        svg.text(44, 460 + i * 20, "•  " + line, size=12.5, fill=INK)
    return svg


def main() -> None:
    for name, svg in (("architecture", architecture()), ("lineage", lineage())):
        (OUT / f"{name}.svg").write_text(svg.render(), encoding="utf-8")
        print(f"wrote docs/diagrams/{name}.svg")


if __name__ == "__main__":
    main()
