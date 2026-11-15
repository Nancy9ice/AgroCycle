"""Where field facts come from. Two implementations behind one interface.

* `FileRepository` (default): the committed field data plus, if present, DS2's indicator outputs
  (`data/out/indicators/*.csv`). Runs anywhere, needs no database.
* `ClickHouseRepository`: the `fields` and `crop_rotation` tables DE loaded. **Tested against a fake
  client only; it has not been run against the live database.** The `field_indicators` table does not
  exist in `schema/` yet, so it reports every indicator as unknown until DE adds it.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Protocol

from .facts import FieldRecord, IndicatorFacts
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

        facts: dict[str, IndicatorFacts] = {}
        for field_id, field_rows in by_field.items():
            facts[field_id] = IndicatorFacts(
                gdd_season_difference_vs_marsden=_single_value(
                    field_rows, "gdd_season_difference_vs_marsden"
                ),
                frost_free_days=_mean_days(field_rows, "frost_free_days"),
                dominant_drainage_class=_dominant_class(soil_rows, field_id, "drainagecl"),
                statuses=indicator_statuses(field_rows),
            )
        return facts


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


def _dominant_class(rows: list[dict[str, str]], field_id: str, prop: str) -> str | None:
    """The class with the largest share of the field's mapped area."""
    candidates = [
        (share, row["value_text"])
        for row in rows
        if row["field_id"] == field_id
        and row["property"] == prop
        and row["value_text"]
        and (share := _number(row["share_pct"])) is not None
    ]
    return max(candidates)[1] if candidates else None


class ClickHouseRepository:
    name = "clickhouse"

    _FIELDS_SQL = (
        "SELECT f.field_id, f.role, f.boundary_source, f.county, r.field_class, r.sequence "
        "FROM fields AS f LEFT JOIN crop_rotation AS r ON f.field_id = r.field_id"
    )

    def __init__(self, client: Any) -> None:
        self._client = client

    @staticmethod
    def _record(row: tuple) -> FieldRecord:
        field_id, role, boundary_source, county, field_class, sequence = row
        return FieldRecord(
            field_id=field_id,
            county=county,
            boundary_source=str(boundary_source),
            role=str(role),
            field_class=str(field_class) if field_class else None,
            crop_sequence=sequence or None,
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
        # `field_indicators` is not in schema/ yet. Until DE adds it, nothing is known.
        return IndicatorFacts()
