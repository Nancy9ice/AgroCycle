"""Build the observed cover calendar for one field from HLS NDVI and DS1's bare windows. Pure: no I/O.

This is what satellite images say about cover, month by month, for the field itself. It is not an expected-cover
calendar for a rotation: the cover claims for crops B and C are marked "research needed" and no source gives their
timing, so nothing is said about them. NDVI measures greenness, not which crop is there.
"""
from __future__ import annotations

import calendar
from datetime import date

from api.schemas.cover import BareWindowOut, CoverCalendarOut, CoverMonthOut, CoverYearOut

NDVI_THRESHOLD = 0.3  # DS1's bare-field threshold (hls_bare_windows)
MIN_BARE_DAYS = 14  # ... held for at least this many consecutive days
MIN_USABLE_SHARE = 0.5  # an image counts when at least half the field is clear of cloud
MIN_IMAGES_FOR_A_STATE = 2  # one image in a month is too little to call the month
BARE_SHARE_OF_MONTH = 0.5  # a month is bare when at least half its days are inside a bare window

LEGEND = {
    "bare": "Bare: seen in at least two usable images that month, inside a bare window.",
    "likely_bare": "Likely bare: inside a bare window, but there is no usable image that month, so this is inferred between images.",
    "green": "Green: at least two usable images, and not bare. This says there is green cover, not which crop.",
    "unknown": "Unknown: too few usable images to say. It is never read as bare or as green.",
}

CAVEATS = [
    (
        "This is what satellite images show for this field. It says nothing about which crop was growing: NDVI "
        "measures greenness, and a green field can be a crop, a cover crop or weeds."
    ),
    (
        "Images cover April to October of 2023, 2024 and 2025. Other months have no image, so a month there is "
        "unknown unless a bare window inferred between two images crosses it."
    ),
    (
        f"A bare window is {MIN_BARE_DAYS} or more days in a row with NDVI under {NDVI_THRESHOLD}. That threshold "
        "is the team's own, not expert-reviewed, and clouds leave gaps that the windows bridge."
    ),
    "Cover is not soil health, and this does not assess erosion.",
    (
        "It shows the field as it is, not what a different rotation would look like. We have no sourced timing for "
        "the cover that the three-year or four-year rotations would give, so none is shown."
    ),
]


def _month_days(year: int, month: int) -> list[date]:
    return [date(year, month, d) for d in range(1, calendar.monthrange(year, month)[1] + 1)]


def _as_date(value) -> date:
    return value if isinstance(value, date) else date.fromisoformat(str(value)[:10])


def build_cover_calendar(field_id: str, ndvi: list[dict], windows: list[dict], data_version: str) -> CoverCalendarOut | None:
    """None when the field has no satellite images at all."""
    usable = [
        _as_date(r["acquired"])
        for r in ndvi
        if r.get("ndvi_mean") is not None and (r.get("valid_share") or 0) >= MIN_USABLE_SHARE
    ]
    if not ndvi:
        return None

    spans = sorted(
        ((_as_date(w["start"]), _as_date(w["end"]), w) for w in windows), key=lambda item: item[0]
    )

    def in_window(day: date) -> bool:
        return any(start <= day <= end for start, end, _ in spans)

    # One row for each year that has images. A bare window can cross a year boundary and cover months of a year
    # without images; those months are only shown for years that do have some.
    years = sorted({d.year for d in usable})

    out_years: list[CoverYearOut] = []
    for year in years:
        months: list[CoverMonthOut] = []
        for month in range(1, 13):
            days = _month_days(year, month)
            images = sum(1 for d in usable if d.year == year and d.month == month)
            bare_days = sum(1 for d in days if in_window(d))
            mostly_bare = bare_days >= BARE_SHARE_OF_MONTH * len(days)
            if mostly_bare and images >= MIN_IMAGES_FOR_A_STATE:
                state = "bare"
            elif mostly_bare:
                state = "likely_bare"
            elif images >= MIN_IMAGES_FOR_A_STATE:
                state = "green"
            else:
                state = "unknown"
            months.append(
                CoverMonthOut(month=month, state=state, usable_images=images, bare_days=bare_days, days=len(days))
            )
        out_years.append(
            CoverYearOut(
                year=year,
                months=months,
                bare_months=sum(m.state in ("bare", "likely_bare") for m in months),
                months_with_images=sum(m.state in ("bare", "green") for m in months),
            )
        )

    usable_months = {(d.year, d.month) for d in usable}
    bare_windows = []
    for start, end, w in spans:
        crossed = {(start.year, start.month)}
        d = start
        while d <= end:
            crossed.add((d.year, d.month))
            d = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
        bare_windows.append(
            BareWindowOut(
                start=start.isoformat(), end=end.isoformat(), bare_days=int(w["bare_days"]),
                confidence=str(w["confidence"]),
                # True only when every month the window crosses has a usable image to back it.
                seen_in_images=all(m in usable_months for m in crossed),
            )
        )
    return CoverCalendarOut(
        field_id=field_id,
        source="NASA HLS (Landsat and Sentinel-2), NDVI per image",
        evidence_type="derived",
        scale="field",
        ndvi_threshold=NDVI_THRESHOLD,
        min_bare_days=MIN_BARE_DAYS,
        years=out_years,
        bare_windows=bare_windows,
        legend=LEGEND,
        caveats=CAVEATS,
        data_version=data_version,
    )
