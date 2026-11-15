"""One honest sentence about a field's crop sequence.

A port of `web/src/features/profile/build-crop-history.ts` so the API and the web app say the same thing
for the same sequence; `tests/test_crop_summary.py` uses the web app's own test cases. It describes only
what the sequence shows.
"""
from __future__ import annotations

CROP_LABELS = {
    "C": "Corn",
    "S": "Soybean",
    "G": "Grass or pasture",
    "A": "Alfalfa",
    "H": "Other hay",
    "O": "Oats",
    "L": "Clover",
    "X": "Other crop",
}

# A corn and soybean history counts as "mostly alternating" when at most this many years repeat the
# previous year's crop (2 of 10 year-to-year changes). More repeats read as a mix.
MAX_REPEATS_FOR_ALTERNATING = 2


def _join(items: list[str]) -> str:
    if len(items) <= 1:
        return "".join(items)
    return f"{', '.join(items[:-1])} and {items[-1]}"


def describe_sequence(sequence: str, first_year: int) -> str:
    """Describe a sequence such as ``SCSCSCSCSCS`` that starts in ``first_year``."""
    unknown = sorted(set(sequence) - set(CROP_LABELS))
    if not sequence or unknown:
        raise ValueError(f"unusable crop sequence {sequence!r} (unknown codes: {unknown})")

    years = [(first_year + index, code) for index, code in enumerate(sequence)]
    span = f"{years[0][0]} to {years[-1][0]}"
    distinct = list(dict.fromkeys(code for _, code in years))
    repeated = [
        year for index, (year, code) in enumerate(years) if index > 0 and code == years[index - 1][1]
    ]

    if len(distinct) == 1:
        return f"{CROP_LABELS[distinct[0]]} in every year, {span}."

    if set(distinct) <= {"C", "S"} and len(repeated) <= MAX_REPEATS_FOR_ALTERNATING:
        if not repeated:
            return (
                f"Corn and soybeans alternate every year, {span}: the pattern AgroCycle is built for."
            )
        crop_by_year = dict(years)
        named = [f"{CROP_LABELS[crop_by_year[year]].lower()} in {year}" for year in repeated]
        count = "one year" if len(repeated) == 1 else f"{len(repeated)} years"
        return (
            f"Corn and soybeans, mostly alternating, {span}. "
            f"A crop repeats in {count}: {_join(named)}."
        )

    counts = sorted(
        ((code, sequence.count(code)) for code in distinct), key=lambda item: -item[1]
    )
    parts = [
        f"{CROP_LABELS[code].lower()} {n} {'year' if n == 1 else 'years'}" for code, n in counts
    ]
    return f"A mix of crops, {span}: {', '.join(parts)}."
