"""The season stress summary (AgroCycle, DS2; BE's F2).

BE asked for crop-phase stress tests — maize silking, July days above 32 degrees. Neither the Marsden
supplement nor the paper gives a single planting date, phase window or crop-stage temperature, so those
windows and thresholds would have been ours to invent. This is the honest version of the same feature: the
weather the field actually had each season, from indicators that already exist with lineage, and no claim
about which crop stage it hit.

`season_stress` is a ClickHouse **view** over `field_indicators`, not a copy, so it cannot drift from the
indicators and needs no reload when they change. One row per field and season.

`season_stress_thresholds` is a small table carrying the threshold behind each column, because a count of
heat days means nothing without the temperature that defines one. Every threshold is team-proposed and not
expert-reviewed, and the table says so on every row.
"""
from __future__ import annotations

from transform.indicators import climate

VIEW = "season_stress"
THRESHOLDS_TABLE = "season_stress_thresholds"

# indicator_id -> column in the view
COLUMNS: dict[str, str] = {
    "heat_days": "heat_days",
    "longest_dry_spell": "longest_dry_spell_days",
    "dry_spell_count": "dry_spells",
    "precipitation_total": "rainfall_mm",
    "gdd": "growing_degree_days",
    "reference_et_total": "reference_et_mm",
    "mean_temperature": "mean_temp_c",
}

VIEW_DDL = f"""
CREATE OR REPLACE VIEW {VIEW} AS
SELECT
    field_id,
    toYear(window_start) AS season,
    window_start,
    window_end,
    {", ".join(
        f"anyIf(value, indicator_id = '{indicator}') AS {column}"
        for indicator, column in COLUMNS.items()
    )},
    countIf(status = 'available') AS indicators_available,
    countIf(status = 'partial')   AS indicators_partial,
    countIf(status = 'unknown')   AS indicators_unknown,
    any(run_id) AS run_id
FROM field_indicators
WHERE category = 'climate' AND indicator_id IN ({", ".join(f"'{i}'" for i in COLUMNS)})
GROUP BY field_id, season, window_start, window_end
"""

THRESHOLDS_DDL = f"""
CREATE TABLE IF NOT EXISTS {THRESHOLDS_TABLE} (
    column          String,
    indicator_id    String,
    what_it_counts  String,
    threshold       String,
    unit            LowCardinality(String),
    evidence_basis  Enum8('experimental' = 1, 'team_proposed' = 2, 'assumption' = 3),
    review          Enum8('not_expert_reviewed' = 1, 'expert_reviewed' = 2),
    limitation      String,
    code_version    LowCardinality(String),
    loaded_at       DateTime64(3, 'UTC') DEFAULT now64(3)
) ENGINE = MergeTree ORDER BY column
"""

_NOT_A_CROP_STAGE = (
    "This is the weather the field had across the whole April-November season. It says nothing about which "
    "crop stage the weather hit, because no source we hold gives crop-phase windows for this area."
)

THRESHOLDS = (
    {
        "column": "heat_days",
        "indicator_id": "heat_days",
        "what_it_counts": "Days the daily maximum temperature reached the threshold or more",
        "threshold": f">= {climate.HEAT_DAY_THRESHOLD_C:g}",
        "unit": "degrees C",
        "limitation": (
            f"{_NOT_A_CROP_STAGE} A gridded daily maximum is smoother than a field's, so local extremes are "
            "under-represented."
        ),
    },
    {
        "column": "longest_dry_spell_days",
        "indicator_id": "longest_dry_spell",
        "what_it_counts": "Longest run of consecutive days below the wet-day threshold",
        "threshold": f"< {climate.WET_DAY_THRESHOLD_MM:g}",
        "unit": "mm of rain per day",
        "limitation": (
            f"{_NOT_A_CROP_STAGE} A rainfall dry spell is not agricultural drought: it ignores soil water "
            "storage, rooting depth and irrigation. POWER also ran about 11 % dry against the Marsden "
            "station record, so dry spells are more likely overstated than understated."
        ),
    },
    {
        "column": "dry_spells",
        "indicator_id": "dry_spell_count",
        "what_it_counts": "Number of dry runs lasting at least the minimum length",
        "threshold": f">= {climate.DRY_SPELL_MIN_DAYS} days below {climate.WET_DAY_THRESHOLD_MM:g} mm",
        "unit": "days",
        "limitation": (
            f"{_NOT_A_CROP_STAGE} Both the wet-day threshold and the minimum length change the count, so it "
            "is comparable only against the same settings."
        ),
    },
    {
        "column": "rainfall_mm",
        "indicator_id": "precipitation_total",
        "what_it_counts": "Total rainfall over the season",
        "threshold": "none: a total, not a count",
        "unit": "mm",
        "limitation": (
            "A bias-corrected reanalysis product, not a rain gauge. Measured against the Marsden station "
            "record it ran 92 mm per season low, about 11 %."
        ),
    },
    {
        "column": "growing_degree_days",
        "indicator_id": "gdd",
        "what_it_counts": "Accumulated heat, with both daily extremes clamped",
        "threshold": f"base {climate.GDD_BASE_C:g}, cap {climate.GDD_UPPER_CAP_C:g}",
        "unit": "degrees C",
        "limitation": (
            f"{_NOT_A_CROP_STAGE} Base 10 with a 30 cap follows the common maize convention and is not a "
            "local calibration."
        ),
    },
    {
        "column": "reference_et_mm",
        "indicator_id": "reference_et_total",
        "what_it_counts": "Total reference evapotranspiration, FAO-56 Penman-Monteith",
        "threshold": "none: a total, not a count",
        "unit": "mm",
        "limitation": (
            "Grass-surface demand, not the water use of any crop in the rotation. Checked against FAO-56 "
            "Example 18; its radiation input comes from a coarser 1-degree grid."
        ),
    },
    {
        "column": "mean_temp_c",
        "indicator_id": "mean_temperature",
        "what_it_counts": "Mean of the daily mean temperature over the season",
        "threshold": "none: a mean, not a count",
        "unit": "degrees C",
        "limitation": f"{_NOT_A_CROP_STAGE} A season mean hides the distribution.",
    },
)


def threshold_rows(code_version: str) -> list[dict]:
    return [
        {
            **row,
            # Reference ET is the only one with an outside check; the rest are our own thresholds.
            "evidence_basis": "team_proposed",
            "review": "not_expert_reviewed",
            "code_version": code_version,
        }
        for row in THRESHOLDS
    ]
