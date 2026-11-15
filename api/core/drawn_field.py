"""A farmer's own crop history for a boundary they drew. Pure: no I/O.

The farmer names the crop for each of the last 11 seasons (2015 to 2025). DS1's classification rules
(`transform.crop_history.rules.classify_field`, section 3 to 7 of rules v1.0) then give the field's class, the same
rules the pre-processed fields go through, so a drawn field is judged by the same yardstick and no agronomy is
invented here. The answer is the farmer's word, labelled "Your input", and is never presented as CDL data.
"""
from __future__ import annotations

from api.db.facts import FIRST_CROP_YEAR
from transform.crop_history import rules as ds1

SEASONS = ds1.WINDOW_YEARS  # 11: the rules need exactly this many consecutive years

# What the farmer can pick -> (the web app's crop letter, DS1's group name).
CHOICES: dict[str, tuple[str, str]] = {
    "corn": ("C", "corn"),
    "soybeans": ("S", "soybeans"),
    "oats": ("O", "oats"),
    "alfalfa": ("A", "alfalfa"),
    "pasture_hay": ("G", "pasture_hay"),
    "other": ("X", ds1.OTHER_CROP),
}


class CropHistoryError(ValueError):
    """The answers cannot be used; the message is safe to show the farmer."""


def classify_crops(crops: list[str]) -> tuple[str, str]:
    """(sequence, field_class) for 11 crops, oldest first, starting FIRST_CROP_YEAR."""
    if len(crops) != SEASONS:
        raise CropHistoryError(
            f"Tell us the crop for all {SEASONS} seasons, {FIRST_CROP_YEAR} to {FIRST_CROP_YEAR + SEASONS - 1}."
        )
    unknown = sorted({c for c in crops if c not in CHOICES})
    if unknown:
        raise CropHistoryError(f"Unknown crop: {', '.join(unknown)}.")
    labels = {
        FIRST_CROP_YEAR + index: ds1.YearLabel(CHOICES[crop][1], ds1.STATUS_OK, 100.0, 0.0, 1)
        for index, crop in enumerate(crops)
    }
    field_class = ds1.classify_field(labels).field_class
    return "".join(CHOICES[crop][0] for crop in crops), field_class
