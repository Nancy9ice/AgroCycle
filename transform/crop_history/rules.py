"""DS1's CDL crop-history rules (v1.0) as pure functions. No I/O.

Source of truth: specs/features/2026-11-14-ds1-cdl-crop-history-rules/cdl-crop-rules.md. Where that
document is ambiguous, the reading used here is stated in a comment and listed in the Phase 3 spec
(risks) for DS1 to confirm. Thresholds use integer arithmetic on pixel counts, so a share of exactly
60 % or 20 % is decided without float rounding.
"""

from collections import Counter
from dataclasses import dataclass
from itertools import pairwise

RULE_VERSION = "ds1-cdl-rules-v1.0"

# Section 1 groups. A year is labelled by one of these groups (section 2 gives "corn", "soybeans",
# "oats", "alfalfa" as examples, so oats and alfalfa are groups of their own).
GROUPS: dict[str, frozenset[int]] = {
    "corn": frozenset({1, 12, 13, 225, 226}),
    "soybeans": frozenset({5, 26, 239, 240}),
    "oats": frozenset({28}),
    "alfalfa": frozenset({36}),
    # Section 5 names 176, 37, 58 and 59 as the pasture/hay/grass codes. Code 176 is also listed under
    # non-crop "if not pasture class"; it is read here as pasture/hay.
    "pasture_hay": frozenset({37, 58, 59, 176}),
    # Section 1 non-crop, plus 171 (evergreen trees, "not crop") and 0 (background / no data).
    "non_crop": frozenset(
        {0, 61, 111, 121, 122, 123, 124, 131, 141, 142, 143, 152, 171, 190, 195}
    ),
}
OTHER_CROP = "other_crop"  # any code not listed: kept, flagged, never an error
NO_DATA_CODE = 0

DOMINANT_PCT = 60  # a group at or above this share labels the year
LOW_CONFIDENCE_PCT = 20  # no-data above this share makes the year low-confidence
ROTATION_ALTERNATIONS = 7  # of the last 10 year-to-year transitions
WINDOW_YEARS = 11  # the last 11 years, so 10 transitions
CONTINUOUS_CORN_YEARS = 8
PASTURE_HAY_YEARS = 8
MIXED_MIN_CORN_SOY_YEARS = 5

STATUS_OK, STATUS_MIXED, STATUS_LOW = "ok", "mixed_uncertain", "low_confidence"
MIXED_LABEL = "mixed"
LOW_CONFIDENCE_LABEL = "low_confidence"  # the year is unusable: it names no crop

# One letter per year in the sequence string, as in DS1's example "S C S C ...".
TOKENS = {
    "corn": "C",
    "soybeans": "S",
    "oats": "O",
    "alfalfa": "A",
    "pasture_hay": "P",
    "non_crop": "N",
    OTHER_CROP: "X",
    MIXED_LABEL: "M",  # no group reached the threshold
}
# "U" = unclassified. Not "L": the web app and the field notes use L for clover, so a low-confidence year would
# read as clover. One letter, one meaning across DS1, DE and the web app.
TOKEN_LOW_CONFIDENCE = "U"

_CODE_TO_GROUP = {code: group for group, codes in GROUPS.items() for code in codes}


def class_group(code: int) -> str:
    return _CODE_TO_GROUP.get(code, OTHER_CROP)


def is_listed(code: int) -> bool:
    """False for a code DS1's rules do not mention; the caller flags it for review."""
    return code in _CODE_TO_GROUP


@dataclass(frozen=True)
class YearLabel:
    group: str  # a GROUPS key, OTHER_CROP, or "mixed"
    status: str  # ok, mixed_uncertain, low_confidence
    dominant_share_pct: float  # share of the largest group
    nodata_share_pct: float
    total_pixels: int

    @property
    def token(self) -> str:
        return TOKEN_LOW_CONFIDENCE if self.status == STATUS_LOW else TOKENS[self.group]


def label_year(pixels_by_code: dict[int, int]) -> YearLabel:
    """Section 2: the group with at least 60 % of the field's pixels labels the year; otherwise the
    year is mixed/uncertain. No-data above 20 % makes it low-confidence, which wins."""
    total = sum(pixels_by_code.values())
    if total <= 0:
        raise ValueError("a field-year with no pixels cannot be labelled")
    by_group = Counter()
    for code, count in pixels_by_code.items():
        by_group[class_group(code)] += count
    nodata = pixels_by_code.get(NO_DATA_CODE, 0)
    top_group, top_pixels = max(by_group.items(), key=lambda item: (item[1], item[0]))
    if nodata * 100 > LOW_CONFIDENCE_PCT * total:
        status = STATUS_LOW
    elif top_pixels * 100 >= DOMINANT_PCT * total:
        status = STATUS_OK
    else:
        status = STATUS_MIXED
    group = {STATUS_OK: top_group, STATUS_MIXED: MIXED_LABEL, STATUS_LOW: LOW_CONFIDENCE_LABEL}[status]
    return YearLabel(group, status, 100 * top_pixels / total, 100 * nodata / total, total)


@dataclass(frozen=True)
class FieldClass:
    field_class: str  # rotation, continuous_corn, pasture_hay, mixed, other
    sequence: str
    corn_years: int
    soybean_years: int
    pasture_hay_years: int
    alternations: int
    transitions_counted: int
    years: tuple[int, ...]


def _counts(label: YearLabel | None, group: str) -> bool:
    return label is not None and label.status == STATUS_OK and label.group == group


def classify_field(labels: dict[int, YearLabel]) -> FieldClass:
    """Sections 3 to 7, applied in DS1's order: rotation, continuous corn, pasture/hay, mixed, other.

    Needs 11 consecutive years (an error otherwise: a short window would be judged on fewer
    transitions without saying so). Years that are mixed/uncertain or low-confidence count for no group
    and their transitions are left out of the rotation count (neither for nor against). Other
    transitions that are not corn-soybean alternations count against the rotation. The rotation
    threshold is 7 absolute alternations, as written ("at least 7 of the last 10").
    """
    if len(labels) < WINDOW_YEARS:
        raise ValueError(f"the rules need {WINDOW_YEARS} years of labels, got {len(labels)}")
    years = tuple(sorted(labels)[-WINDOW_YEARS:])
    if years[-1] - years[0] != WINDOW_YEARS - 1:
        raise ValueError(f"the last {WINDOW_YEARS} years must be consecutive, got {years}")
    window = [labels[y] for y in years]
    corn = sum(_counts(label, "corn") for label in window)
    soy = sum(_counts(label, "soybeans") for label in window)
    pasture = sum(_counts(label, "pasture_hay") for label in window)

    alternations = counted = 0
    for earlier, later in pairwise(window):
        if earlier.status != STATUS_OK or later.status != STATUS_OK:
            continue  # a mixed or low-confidence year: the transition is not counted
        counted += 1
        if {earlier.group, later.group} == {"corn", "soybeans"}:
            alternations += 1

    if alternations >= ROTATION_ALTERNATIONS:
        field_class = "rotation"
    elif corn >= CONTINUOUS_CORN_YEARS:
        field_class = "continuous_corn"
    elif pasture >= PASTURE_HAY_YEARS:
        field_class = "pasture_hay"
    elif corn + soy >= MIXED_MIN_CORN_SOY_YEARS:
        field_class = "mixed"
    else:
        field_class = "other"
    return FieldClass(
        field_class, " ".join(label.token for label in window), corn, soy, pasture,
        alternations, counted, years,
    )
