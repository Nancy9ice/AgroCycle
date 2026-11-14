"""Climate indicators from NASA POWER daily meteorology (AgroCycle, DS2, roadmap Phase 4).

Pure functions over a cleaned daily series. No I/O, no network, no hidden state, so every indicator is
testable on synthetic frames and reproducible from the same input.

Input contract (see ``docs/sources/ds2-power-ssurgo-marsden.md``): one row per day with a ``date`` column
(``datetime.date``, or anything ``pandas.to_datetime`` accepts) and the POWER variables in POWER units:

    T2M_MAX, T2M_MIN, T2M        degrees C
    PRECTOTCORR                  mm/day
    RH2M                         %
    ALLSKY_SFC_SW_DWN            MJ/m2/day
    WS2M                         m/s at 2 m

POWER's -999 fill value must already be null; this module never converts it, because a module that quietly
accepted -999 as a temperature would produce a plausible wrong number.

Missing data is never neutral. A null or absent day is not a zero: it lowers the valid-day count, breaks a
dry spell rather than extending it, and once coverage falls below ``min_coverage`` the indicator returns
``value=None`` with ``status="unknown"`` and a reason.

Scale: a POWER cell is roughly 0.5 x 0.625 degrees, about 50 km at this latitude. These are grid values, not
field measurements, and two fields in one cell get identical climate.

Thresholds are team-proposed defaults and are **not expert-reviewed**; each is a keyword argument.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd

DATE_COLUMN = "date"
MIN_COVERAGE = 0.9

GDD_BASE_C = 10.0
GDD_UPPER_CAP_C = 30.0
HEAT_DAY_THRESHOLD_C = 30.0
FROST_THRESHOLD_C = 0.0
WET_DAY_THRESHOLD_MM = 1.0
DRY_SPELL_MIN_DAYS = 10

_ALBEDO = 0.23
_SOLAR_CONSTANT = 0.0820
_STEFAN_BOLTZMANN = 4.903e-9
_CLEARNESS_FLOOR = 0.33

Window = tuple[date, date]


@dataclass(frozen=True)
class IndicatorValue:
    """One indicator over one window, carrying the denominator it was computed from."""

    indicator_id: str
    value: float | None
    unit: str
    window_start: date
    window_end: date
    days_expected: int
    days_valid: int
    status: str
    reason: str | None = None


@dataclass(frozen=True)
class FrostWindow:
    """Last spring frost, first autumn frost and the frost-free span between them."""

    last_spring_frost: date | None
    first_autumn_frost: date | None
    frost_free_days: int | None
    window_start: date
    window_end: date
    days_expected: int
    days_valid: int
    status: str
    reason: str | None = None


def expected_days(window: Window) -> int:
    """Number of calendar days in the window, both ends inclusive."""
    start, end = window
    if end < start:
        raise ValueError(f"window end {end} precedes start {start}")
    return (end - start).days + 1


def _daily_frame(daily: pd.DataFrame, window: Window, columns: list[str]) -> pd.DataFrame:
    if DATE_COLUMN not in daily.columns:
        raise KeyError(f"missing required column: {DATE_COLUMN}")
    missing = [column for column in columns if column not in daily.columns]
    if missing:
        raise KeyError(f"missing required column(s): {', '.join(missing)}")

    start, end = window
    dates = pd.to_datetime(daily[DATE_COLUMN]).dt.date
    selected = (dates >= start) & (dates <= end)
    frame = daily.loc[selected, columns].copy()
    frame.insert(0, DATE_COLUMN, dates[selected])
    if frame[DATE_COLUMN].duplicated().any():
        repeated = sorted(frame.loc[frame[DATE_COLUMN].duplicated(), DATE_COLUMN].unique())
        raise ValueError(f"duplicate date(s) in the daily series: {repeated[:5]}")
    return frame.sort_values(DATE_COLUMN).reset_index(drop=True)


def _complete_days(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    return frame.dropna(subset=columns).reset_index(drop=True)


def _coverage_failure(
    indicator_id: str,
    unit: str,
    window: Window,
    days_expected: int,
    days_valid: int,
    min_coverage: float,
) -> IndicatorValue | None:
    if days_expected and days_valid / days_expected >= min_coverage:
        return None
    return IndicatorValue(
        indicator_id=indicator_id,
        value=None,
        unit=unit,
        window_start=window[0],
        window_end=window[1],
        days_expected=days_expected,
        days_valid=days_valid,
        status="unknown",
        reason=(
            f"{days_valid} of {days_expected} days have complete data; "
            f"below the {min_coverage:.0%} coverage required"
        ),
    )


def growing_degree_days(
    daily: pd.DataFrame,
    window: Window,
    base_c: float = GDD_BASE_C,
    upper_cap_c: float = GDD_UPPER_CAP_C,
    min_coverage: float = MIN_COVERAGE,
) -> IndicatorValue:
    """Accumulated growing degree days, both daily extremes clamped to [base_c, upper_cap_c]."""
    if upper_cap_c <= base_c:
        raise ValueError(f"upper_cap_c {upper_cap_c} must exceed base_c {base_c}")
    columns = ["T2M_MAX", "T2M_MIN"]
    frame = _daily_frame(daily, window, columns)
    valid = _complete_days(frame, columns)
    total_days = expected_days(window)

    failure = _coverage_failure("gdd", "degree-days C", window, total_days, len(valid), min_coverage)
    if failure is not None:
        return failure

    t_max = valid["T2M_MAX"].clip(lower=base_c, upper=upper_cap_c)
    t_min = valid["T2M_MIN"].clip(lower=base_c, upper=upper_cap_c)
    value = float(((t_max + t_min) / 2.0 - base_c).clip(lower=0.0).sum())
    return IndicatorValue(
        indicator_id="gdd",
        value=value,
        unit="degree-days C",
        window_start=window[0],
        window_end=window[1],
        days_expected=total_days,
        days_valid=len(valid),
        status="ok",
    )


def heat_days(
    daily: pd.DataFrame,
    window: Window,
    threshold_c: float = HEAT_DAY_THRESHOLD_C,
    min_coverage: float = MIN_COVERAGE,
) -> IndicatorValue:
    """Count of days whose maximum temperature reaches threshold_c or more."""
    columns = ["T2M_MAX"]
    frame = _daily_frame(daily, window, columns)
    valid = _complete_days(frame, columns)
    total_days = expected_days(window)

    failure = _coverage_failure("heat_days", "days", window, total_days, len(valid), min_coverage)
    if failure is not None:
        return failure

    return IndicatorValue(
        indicator_id="heat_days",
        value=float((valid["T2M_MAX"] >= threshold_c).sum()),
        unit="days",
        window_start=window[0],
        window_end=window[1],
        days_expected=total_days,
        days_valid=len(valid),
        status="ok",
    )


def seasonal_precipitation_total(
    daily: pd.DataFrame,
    window: Window,
    min_coverage: float = MIN_COVERAGE,
) -> IndicatorValue:
    """Total precipitation over the window."""
    columns = ["PRECTOTCORR"]
    frame = _daily_frame(daily, window, columns)
    valid = _complete_days(frame, columns)
    total_days = expected_days(window)

    failure = _coverage_failure(
        "precipitation_total", "mm", window, total_days, len(valid), min_coverage
    )
    if failure is not None:
        return failure

    return IndicatorValue(
        indicator_id="precipitation_total",
        value=float(valid["PRECTOTCORR"].sum()),
        unit="mm",
        window_start=window[0],
        window_end=window[1],
        days_expected=total_days,
        days_valid=len(valid),
        status="ok",
    )


def seasonal_mean_temperature(
    daily: pd.DataFrame,
    window: Window,
    min_coverage: float = MIN_COVERAGE,
) -> IndicatorValue:
    """Mean of the daily mean temperature over the window."""
    columns = ["T2M"]
    frame = _daily_frame(daily, window, columns)
    valid = _complete_days(frame, columns)
    total_days = expected_days(window)

    failure = _coverage_failure(
        "mean_temperature", "C", window, total_days, len(valid), min_coverage
    )
    if failure is not None:
        return failure

    return IndicatorValue(
        indicator_id="mean_temperature",
        value=float(valid["T2M"].mean()),
        unit="C",
        window_start=window[0],
        window_end=window[1],
        days_expected=total_days,
        days_valid=len(valid),
        status="ok",
    )


def _dry_spell_lengths(
    daily: pd.DataFrame,
    window: Window,
    wet_threshold_mm: float,
) -> tuple[list[int], int]:
    """Dry-run lengths over the window, and the count of days with usable precipitation."""
    frame = _daily_frame(daily, window, ["PRECTOTCORR"])
    by_date = dict(zip(frame[DATE_COLUMN], frame["PRECTOTCORR"], strict=True))

    start, end = window
    lengths: list[int] = []
    run = 0
    days_valid = 0
    day = start
    while day <= end:
        rainfall = by_date.get(day)
        if rainfall is None or pd.isna(rainfall):
            # An unknown day cannot be assumed dry, so it ends the run instead of extending it.
            if run:
                lengths.append(run)
            run = 0
        else:
            days_valid += 1
            if rainfall < wet_threshold_mm:
                run += 1
            else:
                if run:
                    lengths.append(run)
                run = 0
        day += timedelta(days=1)
    if run:
        lengths.append(run)
    return lengths, days_valid


def longest_dry_spell(
    daily: pd.DataFrame,
    window: Window,
    wet_threshold_mm: float = WET_DAY_THRESHOLD_MM,
    min_coverage: float = MIN_COVERAGE,
) -> IndicatorValue:
    """Longest run of consecutive days below wet_threshold_mm; an unknown day breaks the run."""
    lengths, days_valid = _dry_spell_lengths(daily, window, wet_threshold_mm)
    total_days = expected_days(window)

    failure = _coverage_failure(
        "longest_dry_spell", "days", window, total_days, days_valid, min_coverage
    )
    if failure is not None:
        return failure

    return IndicatorValue(
        indicator_id="longest_dry_spell",
        value=float(max(lengths, default=0)),
        unit="days",
        window_start=window[0],
        window_end=window[1],
        days_expected=total_days,
        days_valid=days_valid,
        status="ok",
    )


def dry_spell_count(
    daily: pd.DataFrame,
    window: Window,
    min_days: int = DRY_SPELL_MIN_DAYS,
    wet_threshold_mm: float = WET_DAY_THRESHOLD_MM,
    min_coverage: float = MIN_COVERAGE,
) -> IndicatorValue:
    """Number of dry runs lasting at least min_days."""
    if min_days < 1:
        raise ValueError(f"min_days must be at least 1, got {min_days}")
    lengths, days_valid = _dry_spell_lengths(daily, window, wet_threshold_mm)
    total_days = expected_days(window)

    failure = _coverage_failure(
        "dry_spell_count", "spells", window, total_days, days_valid, min_coverage
    )
    if failure is not None:
        return failure

    return IndicatorValue(
        indicator_id="dry_spell_count",
        value=float(sum(1 for length in lengths if length >= min_days)),
        unit="spells",
        window_start=window[0],
        window_end=window[1],
        days_expected=total_days,
        days_valid=days_valid,
        status="ok",
    )


def frost_window(
    daily: pd.DataFrame,
    window: Window,
    threshold_c: float = FROST_THRESHOLD_C,
    split: date | None = None,
    min_coverage: float = MIN_COVERAGE,
) -> FrostWindow:
    """Last frost on or before ``split`` and first frost after it, with the span between.

    ``split`` separates the spring and autumn halves and defaults to the midpoint of the window, which suits
    a calendar-year window. Pass it explicitly for any other window.
    """
    columns = ["T2M_MIN"]
    frame = _daily_frame(daily, window, columns)
    valid = _complete_days(frame, columns)
    total_days = expected_days(window)
    start, end = window
    midpoint = split if split is not None else start + timedelta(days=(end - start).days // 2)

    if not total_days or len(valid) / total_days < min_coverage:
        return FrostWindow(
            last_spring_frost=None,
            first_autumn_frost=None,
            frost_free_days=None,
            window_start=start,
            window_end=end,
            days_expected=total_days,
            days_valid=len(valid),
            status="unknown",
            reason=(
                f"{len(valid)} of {total_days} days have a minimum temperature; "
                f"below the {min_coverage:.0%} coverage required"
            ),
        )

    frost = valid.loc[valid["T2M_MIN"] <= threshold_c, DATE_COLUMN]
    spring = [day for day in frost if day <= midpoint]
    autumn = [day for day in frost if day > midpoint]
    last_spring = max(spring, default=None)
    first_autumn = min(autumn, default=None)

    if last_spring is None or first_autumn is None:
        return FrostWindow(
            last_spring_frost=last_spring,
            first_autumn_frost=first_autumn,
            frost_free_days=None,
            window_start=start,
            window_end=end,
            days_expected=total_days,
            days_valid=len(valid),
            status="unknown",
            reason=(
                "the window does not contain a frost on both sides of "
                f"{midpoint.isoformat()}, so the frost-free span is not bounded"
            ),
        )

    return FrostWindow(
        last_spring_frost=last_spring,
        first_autumn_frost=first_autumn,
        frost_free_days=(first_autumn - last_spring).days - 1,
        window_start=start,
        window_end=end,
        days_expected=total_days,
        days_valid=len(valid),
        status="ok",
    )


def _saturation_vapour_pressure(temperature_c: float) -> float:
    return 0.6108 * math.exp(17.27 * temperature_c / (temperature_c + 237.3))


def _extraterrestrial_radiation(latitude_deg: float, day_of_year: int) -> float:
    latitude = math.radians(latitude_deg)
    inverse_distance = 1 + 0.033 * math.cos(2 * math.pi * day_of_year / 365)
    declination = 0.409 * math.sin(2 * math.pi * day_of_year / 365 - 1.39)
    # Clamped because |tan(lat) * tan(decl)| exceeds 1 inside the polar day and night.
    sunset_cosine = max(-1.0, min(1.0, -math.tan(latitude) * math.tan(declination)))
    sunset_angle = math.acos(sunset_cosine)
    return (
        (24 * 60 / math.pi)
        * _SOLAR_CONSTANT
        * inverse_distance
        * (
            sunset_angle * math.sin(latitude) * math.sin(declination)
            + math.cos(latitude) * math.cos(declination) * math.sin(sunset_angle)
        )
    )


def et0_fao56_daily(
    t_max_c: float,
    t_min_c: float,
    t_mean_c: float,
    rh_pct: float,
    radiation_mj: float,
    wind_ms: float,
    latitude_deg: float,
    elevation_m: float,
    day_of_year: int,
) -> float:
    """Daily reference evapotranspiration, FAO-56 Penman-Monteith, in mm/day.

    Daily soil heat flux is taken as zero, as FAO-56 allows at a 24-hour step. Not yet checked against a
    published worked example; see the limitation in ``INDICATOR_LINEAGE``.
    """
    saturation = (_saturation_vapour_pressure(t_max_c) + _saturation_vapour_pressure(t_min_c)) / 2
    actual = saturation * rh_pct / 100.0
    slope = 4098 * _saturation_vapour_pressure(t_mean_c) / (t_mean_c + 237.3) ** 2
    pressure = 101.3 * ((293 - 0.0065 * elevation_m) / 293) ** 5.26
    psychrometric = 0.000665 * pressure

    clear_sky = (0.75 + 2e-5 * elevation_m) * _extraterrestrial_radiation(latitude_deg, day_of_year)
    # FAO-56 restricts the cloudiness ratio to about 0.33-1; outside it the net longwave term misbehaves.
    clearness = 1.0 if clear_sky <= 0 else max(_CLEARNESS_FLOOR, min(1.0, radiation_mj / clear_sky))
    net_short = (1 - _ALBEDO) * radiation_mj
    net_long = (
        _STEFAN_BOLTZMANN
        * (((t_max_c + 273.16) ** 4 + (t_min_c + 273.16) ** 4) / 2)
        * (0.34 - 0.14 * math.sqrt(max(actual, 0.0)))
        * (1.35 * clearness - 0.35)
    )
    net_radiation = net_short - net_long

    aerodynamic = psychrometric * (900 / (t_mean_c + 273)) * wind_ms * (saturation - actual)
    numerator = 0.408 * slope * net_radiation + aerodynamic
    denominator = slope + psychrometric * (1 + 0.34 * wind_ms)
    return max(0.0, numerator / denominator)


def reference_et_total(
    daily: pd.DataFrame,
    window: Window,
    latitude_deg: float,
    elevation_m: float,
    min_coverage: float = MIN_COVERAGE,
) -> IndicatorValue:
    """Total FAO-56 reference evapotranspiration over the window."""
    columns = ["T2M_MAX", "T2M_MIN", "T2M", "RH2M", "ALLSKY_SFC_SW_DWN", "WS2M"]
    frame = _daily_frame(daily, window, columns)
    valid = _complete_days(frame, columns)
    total_days = expected_days(window)

    failure = _coverage_failure(
        "reference_et_total", "mm", window, total_days, len(valid), min_coverage
    )
    if failure is not None:
        return failure

    total = sum(
        et0_fao56_daily(
            t_max_c=row["T2M_MAX"],
            t_min_c=row["T2M_MIN"],
            t_mean_c=row["T2M"],
            rh_pct=row["RH2M"],
            radiation_mj=row["ALLSKY_SFC_SW_DWN"],
            wind_ms=row["WS2M"],
            latitude_deg=latitude_deg,
            elevation_m=elevation_m,
            day_of_year=row[DATE_COLUMN].timetuple().tm_yday,
        )
        for _, row in valid.iterrows()
    )
    return IndicatorValue(
        indicator_id="reference_et_total",
        value=float(total),
        unit="mm",
        window_start=window[0],
        window_end=window[1],
        days_expected=total_days,
        days_valid=len(valid),
        status="ok",
    )


_SOURCE = "NASA POWER daily point API, community AG"
_SOURCE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
_SCALE = (
    "POWER grid cell, about 0.5 x 0.625 degrees (roughly 50 km at this latitude). A grid value, not a field "
    "measurement; two fields in one cell share it."
)
_MISSING_RULE = (
    "A null or absent day is never read as zero. It lowers the valid-day count and, for dry spells, ends the "
    "run. Below the coverage threshold the indicator is null with status 'unknown'."
)
_THRESHOLD_NOTE = "Threshold is a team-proposed default and is not expert-reviewed."
_WINDOW_NOTE = "caller-supplied window, inclusive of both dates"

INDICATOR_LINEAGE = [
    {
        "indicator_id": "gdd",
        "variables": ["T2M_MAX", "T2M_MIN"],
        "formula": (
            "sum over days of max(0, (clamp(T2M_MAX, base, cap) + clamp(T2M_MIN, base, cap)) / 2 - base), "
            f"base {GDD_BASE_C} C, cap {GDD_UPPER_CAP_C} C"
        ),
        "unit": "degree-days C",
        "evidence_type": "model_reanalysis",
        "source": _SOURCE,
        "source_url": _SOURCE_URL,
        "spatial_scale": _SCALE,
        "temporal_window": _WINDOW_NOTE,
        "missing_data_rule": _MISSING_RULE,
        "limitation": (
            f"{_THRESHOLD_NOTE} Base 10 C with a 30 C cap follows the common maize convention and is not a "
            "local calibration. Accumulated heat says nothing about when a crop was planted or harvested."
        ),
    },
    {
        "indicator_id": "heat_days",
        "variables": ["T2M_MAX"],
        "formula": f"count of days with T2M_MAX >= {HEAT_DAY_THRESHOLD_C} C",
        "unit": "days",
        "evidence_type": "model_reanalysis",
        "source": _SOURCE,
        "source_url": _SOURCE_URL,
        "spatial_scale": _SCALE,
        "temporal_window": _WINDOW_NOTE,
        "missing_data_rule": _MISSING_RULE,
        "limitation": (
            f"{_THRESHOLD_NOTE} A gridded daily maximum is smoother than a field's, so local extremes are "
            "under-represented."
        ),
    },
    {
        "indicator_id": "precipitation_total",
        "variables": ["PRECTOTCORR"],
        "formula": "sum of PRECTOTCORR over the window",
        "unit": "mm",
        "evidence_type": "model_reanalysis",
        "source": _SOURCE,
        "source_url": _SOURCE_URL,
        "spatial_scale": _SCALE,
        "temporal_window": _WINDOW_NOTE,
        "missing_data_rule": _MISSING_RULE,
        "limitation": (
            "PRECTOTCORR is a bias-corrected reanalysis product, not a rain-gauge reading. Convective "
            "rainfall varies far below the cell size."
        ),
    },
    {
        "indicator_id": "mean_temperature",
        "variables": ["T2M"],
        "formula": "mean of T2M over the window",
        "unit": "C",
        "evidence_type": "model_reanalysis",
        "source": _SOURCE,
        "source_url": _SOURCE_URL,
        "spatial_scale": _SCALE,
        "temporal_window": _WINDOW_NOTE,
        "missing_data_rule": _MISSING_RULE,
        "limitation": "A window mean hides the distribution; it is not a measure of heat or cold stress.",
    },
    {
        "indicator_id": "longest_dry_spell",
        "variables": ["PRECTOTCORR"],
        "formula": (
            f"longest run of consecutive days with PRECTOTCORR < {WET_DAY_THRESHOLD_MM} mm; an unknown day "
            "ends the run"
        ),
        "unit": "days",
        "evidence_type": "model_reanalysis",
        "source": _SOURCE,
        "source_url": _SOURCE_URL,
        "spatial_scale": _SCALE,
        "temporal_window": _WINDOW_NOTE,
        "missing_data_rule": _MISSING_RULE,
        "limitation": (
            f"{_THRESHOLD_NOTE} A rainfall dry spell is not agricultural drought: it ignores soil water "
            "storage, rooting depth and irrigation."
        ),
    },
    {
        "indicator_id": "dry_spell_count",
        "variables": ["PRECTOTCORR"],
        "formula": (
            f"count of dry runs of at least {DRY_SPELL_MIN_DAYS} days, dry being PRECTOTCORR < "
            f"{WET_DAY_THRESHOLD_MM} mm"
        ),
        "unit": "spells",
        "evidence_type": "model_reanalysis",
        "source": _SOURCE,
        "source_url": _SOURCE_URL,
        "spatial_scale": _SCALE,
        "temporal_window": _WINDOW_NOTE,
        "missing_data_rule": _MISSING_RULE,
        "limitation": (
            f"{_THRESHOLD_NOTE} Both the wet-day threshold and the minimum length change the count, so it is "
            "comparable only against the same settings."
        ),
    },
    {
        "indicator_id": "frost_window",
        "variables": ["T2M_MIN"],
        "formula": (
            f"last date with T2M_MIN <= {FROST_THRESHOLD_C} C on or before the season split, the first such "
            "date after it, and the days strictly between them"
        ),
        "unit": "date, date, days",
        "evidence_type": "model_reanalysis",
        "source": _SOURCE,
        "source_url": _SOURCE_URL,
        "spatial_scale": _SCALE,
        "temporal_window": "caller-supplied window, split into spring and autumn halves",
        "missing_data_rule": (
            f"{_MISSING_RULE} A window without a frost on both sides of the split yields 'unknown', never a "
            "span inferred from one side."
        ),
        "limitation": (
            f"{_THRESHOLD_NOTE} A 2 m gridded minimum misses frost hollows and radiative frost at crop "
            "height, so local frost risk is understated."
        ),
    },
    {
        "indicator_id": "reference_et_total",
        "variables": ["T2M_MAX", "T2M_MIN", "T2M", "RH2M", "ALLSKY_SFC_SW_DWN", "WS2M"],
        "formula": "sum of daily FAO-56 Penman-Monteith ET0 with soil heat flux zero at the daily step",
        "unit": "mm",
        "evidence_type": "model_reanalysis",
        "source": _SOURCE,
        "source_url": _SOURCE_URL,
        "spatial_scale": _SCALE,
        "temporal_window": _WINDOW_NOTE,
        "missing_data_rule": (
            f"{_MISSING_RULE} A day missing any of the six inputs is not estimated from the others."
        ),
        "limitation": (
            "Implemented from the published FAO-56 equations but NOT yet checked against a published worked "
            "example, so it is not independently validated and must not drive a conclusion until it is. "
            "Reference ET is grass-surface demand, not the water use of any crop in the rotation."
        ),
    },
]

LINEAGE_FIELDS = (
    "indicator_id",
    "variables",
    "formula",
    "unit",
    "evidence_type",
    "source",
    "source_url",
    "spatial_scale",
    "temporal_window",
    "missing_data_rule",
    "limitation",
)
