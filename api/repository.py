"""Where field facts come from. Two implementations behind one interface.

* `FileRepository` (default): the committed field data plus, if present, DS2's indicator outputs
  (`data/out/indicators/*.csv`). Runs anywhere, needs no database.
* `ClickHouseRepository`: the tables DE loaded (`fields`, `crop_rotation`, `field_indicators`,
  `soil_properties`). **Tested against a fake client only; it has not been run against the live database**
  (`python -m api.check_clickhouse` is the check for someone with credentials).

Both turn indicator rows into facts through the same function (`facts_from_rows`), so the file and database
paths apply identical rules.
"""
from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path
from typing import Any, Protocol

from .facts import FieldRecord, IndicatorFacts, SeasonalMean, SoilMeasure
from .profile import indicator_statuses

REPO_ROOT = Path(__file__).resolve().parents[1]
NOTES_PATH = REPO_ROOT / "data" / "fields" / "field_selection_notes.csv"
FIELDS_PATH = REPO_ROOT / "data" / "fields" / "fields.geojson"
INDICATORS_DIR = REPO_ROOT / "data" / "out" / "indicators"


class FieldRepository(Protocol):
    name: str

    def list_fields(self) -> list[FieldRecord]: ...

    def get_field(self, field_id: str) -> FieldRecord | None: ...

    def get_indicators(self, field_id: str) -> IndicatorFacts: ...


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class FileRepository:
    name = "files"

    def __init__(
        self,
        notes_path: Path = NOTES_PATH,
        fields_path: Path = FIELDS_PATH,
        indicators_dir: Path = INDICATORS_DIR,
    ) -> None:
        import json

        properties = {
            feature["properties"]["field_id"]: feature["properties"]
            for feature in json.loads(fields_path.read_text(encoding="utf-8"))["features"]
        }
        self._records: dict[str, FieldRecord] = {}
        for row in _read_csv(notes_path):
            props = properties[row["field_id"]]
            self._records[row["field_id"]] = FieldRecord(
                field_id=row["field_id"],
                county=row["county"],
                boundary_source=props["boundary_source"],
                role=props["role"],
                field_class=row["cdl_class"] or None,
                crop_sequence=row["crops_2015_2025"] or None,
                soil_series=row.get("soil_series") or None,
                soil_map_unit=row.get("soil_map_unit") or None,
            )
        self._indicators_dir = indicators_dir
        self._indicator_cache: dict[str, IndicatorFacts] | None = None

    def list_fields(self) -> list[FieldRecord]:
        return sorted(
            self._records.values(), key=lambda r: (r.role != "primary", r.field_id)
        )

    def get_field(self, field_id: str) -> FieldRecord | None:
        return self._records.get(field_id)

    def get_indicators(self, field_id: str) -> IndicatorFacts:
        if self._indicator_cache is None:
            self._indicator_cache = self._load_indicators()
        return self._indicator_cache.get(field_id, IndicatorFacts())

    def _load_indicators(self) -> dict[str, IndicatorFacts]:
        indicators_path = self._indicators_dir / "field_indicators.csv"
        if not indicators_path.exists():
            return {}
        rows = _read_csv(indicators_path)
        soil_path = self._indicators_dir / "soil_properties.csv"
        soil_rows = _read_csv(soil_path) if soil_path.exists() else []

        by_field: dict[str, list[dict[str, str]]] = {}
        for row in rows:
            by_field.setdefault(row["field_id"], []).append(row)
        return {
            field_id: facts_from_rows(field_rows, [r for r in soil_rows if r["field_id"] == field_id])
            for field_id, field_rows in by_field.items()
        }


def facts_from_rows(
    indicator_rows: list[dict[str, str]], soil_rows: list[dict[str, str]]
) -> IndicatorFacts:
    """Reduce one field's indicator and soil rows to what the engine and profile read.

    Rows are dicts of strings, as DS2's CSVs read them; the ClickHouse repository converts to the same
    shape, so the rules below apply to both sources and cannot drift apart.
    """
    return IndicatorFacts(
        gdd_season_difference_vs_marsden=_single_value(
            indicator_rows, "gdd_season_difference_vs_marsden"
        ),
        frost_free_days=_mean_days(indicator_rows, "frost_free_days"),
        dominant_drainage_class=_dominant_class(soil_rows, "drainagecl"),
        statuses=indicator_statuses(indicator_rows),
        seasonal=seasonal_means(indicator_rows),
        soil=soil_measures(indicator_rows),
        drainage_shares=_class_shares(soil_rows, "drainagecl"),
    )


# The weather indicators the profile screen shows (runner ids).
PROFILE_WEATHER_INDICATORS = ("precipitation_total", "heat_days", "dry_spell_count", "gdd")


def seasonal_means(rows: list[dict[str, str]]) -> dict[str, SeasonalMean]:
    """Mean of each profile indicator over its `available` seasons. No available season, no entry."""
    result: dict[str, SeasonalMean] = {}
    for indicator_id in PROFILE_WEATHER_INDICATORS:
        seasons = [row for row in rows if row["indicator_id"] == indicator_id]
        # A season counts only if it is available, has a value, and states the dates it covers: without
        # dates the period cannot be described, so it is left out (and still counted in seasons_total).
        used = [
            (row, value)
            for row in seasons
            if row["status"] == "available"
            and (value := _number(row["value"])) is not None
            and len(row["window_start"]) >= 10
            and len(row["window_end"]) >= 10
        ]
        if not used:
            continue
        starts = sorted(row["window_start"] for row, _ in used)
        ends = sorted(row["window_end"] for row, _ in used)
        result[indicator_id] = SeasonalMean(
            indicator_id=indicator_id,
            mean=sum(value for _, value in used) / len(used),
            unit=used[0][0]["unit"],
            seasons_used=len(used),
            seasons_total=len(seasons),
            first_year=int(starts[0][:4]),
            last_year=int(ends[-1][:4]),
            start_month=int(starts[0][5:7]),
            end_month=int(ends[0][5:7]),
        )
    return result


# The soil survey measures the profile screen shows (runner ids).
PROFILE_SOIL_MEASURES = (
    "om_r_0_30cm",
    "claytotal_r_0_30cm",
    "silttotal_r_0_30cm",
    "sandtotal_r_0_30cm",
    "ph1to1h2o_r_0_30cm",
    "available_water_storage_0_100cm",
)


def soil_measures(rows: list[dict[str, str]]) -> dict[str, SoilMeasure]:
    """Soil values with a number and a usable status. `partial` is kept (with DS2's coverage note) because
    it is real and says what it covers; `unknown` or empty is left out, never shown as zero."""
    result: dict[str, SoilMeasure] = {}
    for row in rows:
        indicator_id = row["indicator_id"]
        if indicator_id not in PROFILE_SOIL_MEASURES or row["status"] not in ("available", "partial"):
            continue
        value = _number(row["value"])
        if value is None:
            continue
        result[indicator_id] = SoilMeasure(
            indicator_id=indicator_id,
            value=value,
            unit=row.get("unit", ""),
            coverage_note=row.get("unknown_reason", "") if row["status"] == "partial" else "",
        )
    return result


def _class_shares(rows: list[dict[str, str]], prop: str) -> tuple[tuple[str, float], ...]:
    shares = [
        (row["value_text"], share)
        for row in rows
        if row["property"] == prop
        and row["value_text"]
        and (share := _number(row["share_pct"])) is not None
    ]
    return tuple(sorted(shares, key=lambda item: -item[1]))


def _number(value: str) -> float | None:
    try:
        return float(value) if value not in ("", None) else None
    except ValueError:
        return None


def _single_value(rows: list[dict[str, str]], indicator_id: str) -> float | None:
    for row in rows:
        if row["indicator_id"] == indicator_id and row["status"] == "available":
            return _number(row["value"])
    return None


def _mean_days(rows: list[dict[str, str]], indicator_id: str) -> int | None:
    """Mean over the seasons that have a value, rounded to whole days; unknown if none do."""
    values = [
        v
        for row in rows
        if row["indicator_id"] == indicator_id and (v := _number(row["value"])) is not None
    ]
    return round(sum(values) / len(values)) if values else None


def _dominant_class(rows: list[dict[str, str]], prop: str) -> str | None:
    """The class with the largest share of the field's mapped area (rows are already one field's)."""
    candidates = [
        (share, row["value_text"])
        for row in rows
        if row["property"] == prop
        and row["value_text"]
        and (share := _number(row["share_pct"])) is not None
    ]
    return max(candidates)[1] if candidates else None


def _text(value: Any) -> str:
    """A ClickHouse cell as the string DS2's CSVs would hold: null and absent become empty."""
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


class ClickHouseRepository:
    """Field facts from the tables DE loaded.

    The field class and the indicators come from ClickHouse. The crop sequence and soil series come from the
    committed field notes (`notes`), because `crop_rotation.sequence` is space-separated tokens in DS1's
    vocabulary (`L` = low confidence; `P`, `N`, `M` unknown to the web app, whose `L` means clover) and passing
    it through would crash or mislabel crops. One vocabulary has to be chosen first.
    """

    name = "clickhouse"

    _FIELDS_SQL = (
        "SELECT f.field_id, f.role, f.boundary_source, f.county, r.field_class "
        "FROM fields AS f LEFT JOIN crop_rotation AS r ON f.field_id = r.field_id"
    )
    _INDICATORS_SQL = (
        "SELECT field_id, indicator_id, value, unit, status, window_start, window_end, unknown_reason "
        "FROM field_indicators WHERE field_id = {field_id:String}"
    )
    _SOIL_SQL = (
        "SELECT field_id, property, value_text, share_pct "
        "FROM soil_properties WHERE field_id = {field_id:String} AND property = 'drainagecl'"
    )

    def __init__(self, client: Any, notes: FieldRepository | None = None) -> None:
        self._client = client
        self._notes = notes

    def _record(self, row: tuple) -> FieldRecord:
        field_id, role, boundary_source, county, field_class = row
        base = FieldRecord(
            field_id=field_id,
            county=county,
            boundary_source=str(boundary_source),
            role=str(role),
            field_class=str(field_class) if field_class else None,
            crop_sequence=None,
        )
        noted = self._notes.get_field(field_id) if self._notes else None
        if noted is None:
            return base
        return replace(
            base,
            crop_sequence=noted.crop_sequence,
            soil_series=noted.soil_series,
            soil_map_unit=noted.soil_map_unit,
        )

    def list_fields(self) -> list[FieldRecord]:
        rows = self._client.query(self._FIELDS_SQL).result_rows
        return sorted(
            (self._record(row) for row in rows), key=lambda r: (r.role != "primary", r.field_id)
        )

    def get_field(self, field_id: str) -> FieldRecord | None:
        rows = self._client.query(
            f"{self._FIELDS_SQL} WHERE f.field_id = {{field_id:String}}",
            parameters={"field_id": field_id},
        ).result_rows
        return self._record(rows[0]) if rows else None

    def get_indicators(self, field_id: str) -> IndicatorFacts:
        parameters = {"field_id": field_id}
        indicator_rows = [
            {
                "field_id": r[0],
                "indicator_id": r[1],
                "value": _text(r[2]),
                "unit": _text(r[3]),
                "status": _text(r[4]),
                "window_start": _text(r[5]),
                "window_end": _text(r[6]),
                "unknown_reason": _text(r[7]),
            }
            for r in self._client.query(self._INDICATORS_SQL, parameters=parameters).result_rows
        ]
        soil_rows = [
            {
                "field_id": r[0],
                "property": r[1],
                "value_text": _text(r[2]),
                "share_pct": _text(r[3]),
            }
            for r in self._client.query(self._SOIL_SQL, parameters=parameters).result_rows
        ]
        return facts_from_rows(indicator_rows, soil_rows)
