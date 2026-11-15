"""Clean NASA POWER daily point responses (roadmap Phase 4, DE; rules from DS2's sheet, section 1).

    clean_point(document, point_id)   one point -> tidy rows, a gap report
    group_cells(points)               points with identical content share one cell

Rules: the fill value (-999, confirmed in the header) becomes null with qc_flag `fill`; a date missing
from the response becomes a null row with qc_flag `missing`; nothing is interpolated. DS2's hard checks
stop the run, his soft checks set a flag and keep the row. Units come from the response and are kept.
"""

import hashlib
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

VARIABLES = ("T2M_MAX", "T2M_MIN", "T2M", "PRECTOTCORR", "RH2M", "ALLSKY_SFC_SW_DWN", "WS2M")
EXPECTED_FILL = -999.0
TEMPERATURE_RANGE_C = (-50.0, 50.0)
CELL_ID_HEX = 12  # 48 bits of the content hash

QC_FILL, QC_MISSING, QC_NULL = "fill", "missing", "null"
QC_T_ORDER, QC_T_RANGE = "soft_t_order", "soft_t_range"

# variable: (lowest allowed, highest allowed) for the hard checks; None means unbounded on that side
HARD_LIMITS = {
    "PRECTOTCORR": (0.0, None),
    "ALLSKY_SFC_SW_DWN": (0.0, None),
    "WS2M": (0.0, None),
    "RH2M": (0.0, 100.0),
}


class HardCheckFailed(ValueError):
    pass


@dataclass
class PointResult:
    point_id: str
    latitude: float
    longitude: float
    elevation_m: float
    daily: pd.DataFrame  # point_id, variable, date, value, unit, qc_flag (one row per expected date)
    expected_days: int
    fill_dates: dict[str, list[str]] = field(default_factory=dict)  # variable -> dates that held the fill value
    missing_dates: dict[str, list[str]] = field(default_factory=dict)  # variable -> dates absent from the response
    null_dates: dict[str, list[str]] = field(default_factory=dict)  # variable -> dates present but null in the response
    soft_flags: dict[str, int] = field(default_factory=dict)  # flag -> rows


def _expected_dates(header: dict) -> pd.DatetimeIndex:
    return pd.date_range(pd.Timestamp(header["start"]), pd.Timestamp(header["end"]), freq="D")


def clean_point(document: dict, point_id: str) -> PointResult:
    header = document["header"]
    if "fill_value" not in header:
        raise ValueError(f"{point_id}: the header has no fill_value, so the fill rule cannot be confirmed")
    fill = float(header["fill_value"])
    if fill != EXPECTED_FILL:
        raise ValueError(f"{point_id}: fill value {fill} in the header, expected {EXPECTED_FILL}")
    parameters = document["properties"]["parameter"]
    units = {name: meta.get("units", "") for name, meta in document.get("parameters", {}).items()}
    absent = [v for v in VARIABLES if v not in parameters]
    if absent:
        raise ValueError(f"{point_id}: variables missing from the response: {absent}")
    longitude, latitude, elevation = document["geometry"]["coordinates"]
    dates = _expected_dates(header)

    frames, fill_dates, missing_dates, null_dates = [], {}, {}, {}
    for variable in VARIABLES:
        series = pd.to_numeric(pd.Series(parameters[variable]), errors="raise")  # a text value is an error
        series.index = pd.to_datetime(series.index, format="%Y%m%d")
        outside = series.index.difference(dates)
        if len(outside):
            raise ValueError(f"{point_id} {variable}: {len(outside)} dates outside {dates[0]:%Y-%m-%d} to {dates[-1]:%Y-%m-%d}")
        full = series.reindex(dates).astype("float64")
        flag = pd.Series("", index=dates)
        absent_mask = ~dates.isin(series.index)
        null_mask = dates.isin(series.index[series.isna()])  # a date that is there, with a null value
        filled_mask = (full == fill).fillna(False).to_numpy()
        flag[absent_mask] = QC_MISSING
        flag[null_mask] = QC_NULL
        flag[filled_mask] = QC_FILL
        full[filled_mask] = np.nan
        missing_dates[variable] = [d.strftime("%Y-%m-%d") for d in dates[absent_mask]]
        fill_dates[variable] = [d.strftime("%Y-%m-%d") for d in dates[filled_mask]]
        null_dates[variable] = [d.strftime("%Y-%m-%d") for d in dates[null_mask]]
        frames.append(pd.DataFrame({
            "point_id": point_id, "variable": variable, "date": dates, "value": full.to_numpy(),
            "unit": units.get(variable, ""), "qc_flag": flag.to_numpy(),
        }))
    daily = pd.concat(frames, ignore_index=True)
    _hard_checks(daily, point_id)
    soft = _soft_checks(daily)
    return PointResult(
        point_id, latitude, longitude, elevation, daily, len(dates), fill_dates, missing_dates, null_dates, soft
    )


def _hard_checks(daily: pd.DataFrame, point_id: str) -> None:
    problems = []
    for variable, (low, high) in HARD_LIMITS.items():
        values = daily.loc[daily["variable"] == variable, "value"].dropna()
        if low is not None and (values < low).any():
            problems.append(f"{variable}: {int((values < low).sum())} values below {low}")
        if high is not None and (values > high).any():
            problems.append(f"{variable}: {int((values > high).sum())} values above {high}")
    if problems:
        raise HardCheckFailed(f"{point_id}: " + "; ".join(problems))


def _soft_checks(daily: pd.DataFrame) -> dict[str, int]:
    """Flag, never drop. A flag already set (fill or missing) is kept; the first soft flag wins."""
    counts = {QC_T_ORDER: 0, QC_T_RANGE: 0}
    wide = daily.pivot(index="date", columns="variable", values="value")
    order_bad = ((wide["T2M_MIN"] > wide["T2M"]) | (wide["T2M"] > wide["T2M_MAX"]) | (wide["T2M_MIN"] > wide["T2M_MAX"]))
    for variable in ("T2M_MAX", "T2M_MIN", "T2M"):
        rows = daily["variable"].eq(variable) & daily["date"].isin(wide.index[order_bad]) & daily["qc_flag"].eq("")
        daily.loc[rows, "qc_flag"] = QC_T_ORDER
        counts[QC_T_ORDER] += int(rows.sum())
        low, high = TEMPERATURE_RANGE_C
        rows = daily["variable"].eq(variable) & ((daily["value"] < low) | (daily["value"] > high)) & daily["qc_flag"].eq("")
        daily.loc[rows, "qc_flag"] = QC_T_RANGE
        counts[QC_T_RANGE] += int(rows.sum())
    return counts


def series_fingerprint(daily: pd.DataFrame) -> str:
    """A hash of every value and flag of every variable (nulls included), identical for identical content."""
    ordered = daily.sort_values(["variable", "date"])
    values = ordered["value"].to_numpy(dtype="float64")
    values = np.where(np.isnan(values), -1e300, values)
    digest = hashlib.sha256()
    digest.update(",".join(ordered["variable"].unique()).encode())
    digest.update(values.tobytes())
    digest.update("|".join(ordered["qc_flag"]).encode())  # a fill and a gap are different histories
    digest.update(f"{ordered['date'].min():%Y%m%d}-{ordered['date'].max():%Y%m%d}".encode())
    digest.update("|".join(ordered.groupby("variable", sort=False)["unit"].first()).encode())
    return digest.hexdigest()


def group_cells(points: list[PointResult]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Points whose content is identical across all variables share one cell: returns the
    `climate_points` frame and the `climate_daily` frame (one copy of each cell's series).

    The API returns the coordinates it was sent, not a grid-cell centre, so cells are found by content.
    """
    cell_of, first, full = {}, {}, {}
    for point in points:
        fingerprint = series_fingerprint(point.daily)
        cell_id = "cell-" + fingerprint[:CELL_ID_HEX]
        if full.setdefault(cell_id, fingerprint) != fingerprint:
            raise ValueError(f"{point.point_id}: a different series got the same cell id {cell_id}")
        cell_of[point.point_id] = cell_id
        first.setdefault(cell_id, point)
    table = pd.DataFrame([
        {"point_id": p.point_id, "cell_id": cell_of[p.point_id], "latitude": p.latitude,
         "longitude": p.longitude, "elevation_m": p.elevation_m}
        for p in points
    ])
    daily = pd.concat(
        [p.daily.assign(cell_id=cell).drop(columns="point_id") for cell, p in first.items()], ignore_index=True
    )[["cell_id", "variable", "date", "value", "unit", "qc_flag"]]
    return table, daily
