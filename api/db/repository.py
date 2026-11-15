"""Where field facts come from. Two implementations behind one interface.

* `FileRepository` (default): the committed field data plus, if present, DS2's indicator outputs
  (`data/out/indicators/*.csv`). Runs anywhere, needs no database.
* `ClickHouseRepository`: the tables DE loaded (`fields`, `crop_rotation`, `field_indicators`,
  `soil_properties`). Run against the live database on 2026-11-15: for the same indicator data it gives the same crop history and
  outcome as `FileRepository` for all 45 fields. `python -m api.check_clickhouse` repeats the basic check.

Both turn indicator rows into facts through the same function (`facts_from_rows`), so the file and database
paths apply identical rules.
"""
from __future__ import annotations

import csv
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC
from pathlib import Path
from typing import Any, ClassVar, Protocol

from api.db.cache import ttl_cached
from api.db.facts import DRAWN_PREFIX, FieldRecord, IndicatorFacts, SeasonalMean, SoilMeasure

# Runner indicator id -> the id the engine requires.
# Kept here (not in api.core.profile) so that api.db has no dependency on api.core.
RUNNER_TO_ENGINE_INDICATOR = {
    "gdd": "gdd",
    "precipitation_total": "precipitation_total",
    "frost_free_days": "frost_window",
    "om_r_0_30cm": "om_r_0_30cm",
}


def indicator_statuses(rows) -> dict[str, str]:
    """Collapse per-season runner rows into the engine's one status per required indicator."""
    seen: dict[str, list[bool]] = {}
    for row in rows:
        engine_id = RUNNER_TO_ENGINE_INDICATOR.get(row["indicator_id"])
        if engine_id is not None:
            seen.setdefault(engine_id, []).append(row["status"] == "available")
    return {
        engine_id: "ok" if all(flags) else "unknown" for engine_id, flags in seen.items()
    }

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTES_PATH = REPO_ROOT / "data" / "fields" / "field_selection_notes.csv"
FIELDS_PATH = REPO_ROOT / "data" / "fields" / "fields.geojson"
INDICATORS_DIR = REPO_ROOT / "data" / "out" / "indicators"

# Module-level in-memory store for file-mode analyses
_ANALYSIS_STORE: dict[str, dict] = {}


class FieldRepository(Protocol):
    name: str

    def list_fields(self) -> list[FieldRecord]: ...

    def get_field(self, field_id: str) -> FieldRecord | None: ...

    def get_indicators(self, field_id: str) -> IndicatorFacts: ...

    @property
    def data_version(self) -> str: ...

    def store_analysis(self, analysis_id: str, field_id: str, engine_version: str, data_version: str, response_json: str) -> None: ...

    def get_analysis(self, analysis_id: str) -> dict | None: ...

    def get_marsden_means(self) -> list[dict]: ...

    def get_lineage_row(self, indicator_id: str) -> dict | None: ...

    def get_all_lineage(self) -> list[dict]: ...

    def get_all_sources(self) -> list[dict]: ...

    def get_climate_timeseries(self, field_id: str, from_date: str, to_date: str, max_points: int) -> list[dict]: ...

    def get_ndvi_timeseries(self, field_id: str, from_date: str, to_date: str) -> list[dict]: ...

    def list_demo_fields_with_geometry(self) -> list[dict]: ...

    def get_test_set_rows(self) -> list[dict]: ...

    def get_expected_outcomes(self) -> dict | None: ...

    def get_indicator_rows(self, field_id: str) -> list[dict]: ...

    def get_rule_register(self) -> dict | None: ...

    def save_feedback(self, row: dict) -> None: ...

    def count_recent_feedback(self, hours: int) -> int: ...

    def save_drawn_field(self, field_id: str, name: str, county: str, area_ha: float, geometry: dict) -> None: ...

    def get_drawn_field(self, field_id: str) -> dict | None: ...

    def set_drawn_crop_history(self, field_id: str, crop_sequence: str, field_class: str) -> bool: ...

    def count_recent_drawn_fields(self, hours: int) -> int: ...

    def log_ask(
        self,
        log_id: str,
        context_type: str,
        context_id: str,
        field_id: str,
        question: str,
        answer: str,
        citations: list[str],
        refused: bool,
        audience: str,
        model: str,
    ) -> None: ...


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class FileRepository:
    name = "files"
    durable_analyses = False  # the analysis store is in memory

    def __init__(
        self,
        notes_path: Path = NOTES_PATH,
        fields_path: Path = FIELDS_PATH,
        indicators_dir: Path = INDICATORS_DIR,
    ) -> None:
        import json

        self._fields_path = fields_path
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

    @property
    def data_version(self) -> str:
        return "files"

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

    def get_indicator_rows(self, field_id: str) -> list[dict]:
        """The field's raw indicator rows, one per indicator and season."""
        path = self._indicators_dir / "field_indicators.csv"
        if not path.exists():
            return []
        return [row for row in _read_csv(path) if row["field_id"] == field_id]

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

    def store_analysis(self, analysis_id: str, field_id: str, engine_version: str, data_version: str, response_json: str) -> None:
        _ANALYSIS_STORE[analysis_id] = {
            "analysis_id": analysis_id,
            "field_id": field_id,
            "engine_version": engine_version,
            "data_version": data_version,
            "response_json": response_json,
        }

    def get_analysis(self, analysis_id: str) -> dict | None:
        return _ANALYSIS_STORE.get(analysis_id)

    def get_marsden_means(self) -> list[dict]:
        return []

    def get_lineage_row(self, indicator_id: str) -> dict | None:
        return None

    def get_all_lineage(self) -> list[dict]:
        return []

    def get_all_sources(self) -> list[dict]:
        return []

    def get_climate_timeseries(self, field_id: str, from_date: str, to_date: str, max_points: int) -> list[dict]:
        return []

    def get_ndvi_timeseries(self, field_id: str, from_date: str, to_date: str) -> list[dict]:
        return []

    def get_test_set_rows(self) -> list[dict]:
        # The audit is computed offline by DS and lives only in ClickHouse.
        return []

    def get_expected_outcomes(self) -> dict | None:
        return None

    def get_rule_register(self) -> dict | None:
        # DS2 loads the register into ClickHouse; file mode has none.
        return None

    def save_feedback(self, row: dict) -> None:
        raise RuntimeError("Feedback is kept in the database, which this API is not connected to.")

    def count_recent_feedback(self, hours: int) -> int:
        return 0

    # Boundaries a farmer draws are kept in the database; file mode has nowhere to keep them.
    def save_drawn_field(self, field_id: str, name: str, county: str, area_ha: float, geometry: dict) -> None:
        raise RuntimeError("Drawn boundaries need the database, which this API is not connected to.")

    def get_drawn_field(self, field_id: str) -> dict | None:
        return None

    def set_drawn_crop_history(self, field_id: str, crop_sequence: str, field_class: str) -> bool:
        return False

    def count_recent_drawn_fields(self, hours: int) -> int:
        return 0

    def log_ask(self, log_id: str, context_type: str, context_id: str, field_id: str, question: str, answer: str, citations: list[str], refused: bool, audience: str, model: str) -> None:
        # In file mode, log to the in-memory store (not persisted across restarts).
        _ANALYSIS_STORE[f"ask:{log_id}"] = {
            "log_id": log_id, "context_type": context_type, "context_id": context_id,
            "field_id": field_id, "question": question, "answer": answer,
            "citations": citations, "refused": refused, "audience": audience, "model": model,
        }

    def list_demo_fields_with_geometry(self) -> list[dict]:
        import json as _json
        geojson = _json.loads(self._fields_path.read_text(encoding="utf-8"))
        result = []
        for feat in geojson["features"]:
            props = feat["properties"]
            field_id = props["field_id"]
            record = self._records.get(field_id)
            if record is None:
                continue
            from pyproj import Transformer
            from shapely.geometry import shape
            from shapely.ops import transform as shp_transform
            shp = shape(feat["geometry"])
            transformer = Transformer.from_crs("EPSG:4326", "EPSG:32615", always_xy=True)
            projected = shp_transform(transformer.transform, shp)
            area_ha = round(projected.area / 10000, 1)
            result.append({
                "field_id": field_id,
                "county": record.county,
                "role": record.role,
                "boundary_source": record.boundary_source,
                "is_demo": True,
                "area_ha": area_ha,
                "geometry": feat["geometry"],
            })
        return sorted(result, key=lambda x: (x["role"] != "primary", x["field_id"]))


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
            end_month=int(ends[-1][5:7]),
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
    """Mean over available seasons only, rounded to whole days. Partial/unknown rows are excluded,
    consistent with how seasonal_means and indicator_statuses treat non-available rows."""
    values = [
        v
        for row in rows
        if row["indicator_id"] == indicator_id
        and row.get("status") == "available"
        and (v := _number(row["value"])) is not None
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
    vocabulary. `L` now means clover in both (a low-confidence year is `U`), but `P`, `N`, `M` and the spacing
    still differ from the web app's, so passing it through would crash or mislabel crops.
    """

    name = "clickhouse"
    durable_analyses = True

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
        self._data_version: str | None = None

    @property
    def data_version(self) -> str:
        if self._data_version is None:
            rows = self._client.query(
                "SELECT max(load_id) FROM field_indicators LIMIT 1"
            ).result_rows
            self._data_version = str(rows[0][0]) if rows and rows[0][0] else "unknown"
        return self._data_version

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

    @ttl_cached()
    def list_fields(self) -> list[FieldRecord]:
        rows = self._client.query(self._FIELDS_SQL).result_rows
        return sorted(
            (self._record(row) for row in rows), key=lambda r: (r.role != "primary", r.field_id)
        )

    def get_field(self, field_id: str) -> FieldRecord | None:
        if field_id.startswith(DRAWN_PREFIX):
            # Never cached: a farmer's answers change the record, and they must see the change at once.
            return self._drawn_record(self.get_drawn_field(field_id))
        return self._get_stored_field(field_id)

    @ttl_cached()
    def _get_stored_field(self, field_id: str) -> FieldRecord | None:
        rows = self._client.query(
            f"{self._FIELDS_SQL} WHERE f.field_id = {{field_id:String}}",
            parameters={"field_id": field_id},
        ).result_rows
        return self._record(rows[0]) if rows else None

    @staticmethod
    def _drawn_record(row: dict | None) -> FieldRecord | None:
        if row is None:
            return None
        return FieldRecord(
            field_id=row["field_id"],
            county=row["county"],
            boundary_source="drawn",
            role="drawn",
            field_class=row["field_class"] or None,
            crop_sequence=row["crop_sequence"] or None,
        )

    _DRAWN_COLUMNS = "field_id, name, county, area_ha, geometry, crop_sequence, field_class, created_at"

    def save_drawn_field(self, field_id: str, name: str, county: str, area_ha: float, geometry: dict) -> None:
        import json as _json

        self._client.insert(
            "drawn_fields",
            [[field_id, name, county, area_ha, _json.dumps(geometry), "", ""]],
            column_names=["field_id", "name", "county", "area_ha", "geometry", "crop_sequence", "field_class"],
        )

    def get_drawn_field(self, field_id: str) -> dict | None:
        import json as _json

        rows = self._client.query(
            f"SELECT {self._DRAWN_COLUMNS} FROM drawn_fields FINAL WHERE field_id = {{field_id:String}}",
            parameters={"field_id": field_id},
        ).result_rows
        if not rows:
            return None
        r = rows[0]
        return {
            "field_id": _text(r[0]), "name": _text(r[1]), "county": _text(r[2]), "area_ha": float(r[3]),
            "geometry": _json.loads(_text(r[4])), "crop_sequence": _text(r[5]), "field_class": _text(r[6]),
            "created_at": r[7],
        }

    def set_drawn_crop_history(self, field_id: str, crop_sequence: str, field_class: str) -> bool:
        import json as _json

        row = self.get_drawn_field(field_id)
        if row is None:
            return False
        # A newer row replaces the old one (ReplacingMergeTree on updated_at, read with FINAL).
        self._client.insert(
            "drawn_fields",
            [[row["field_id"], row["name"], row["county"], row["area_ha"], _json.dumps(row["geometry"]),
              crop_sequence, field_class, row["created_at"]]],
            column_names=["field_id", "name", "county", "area_ha", "geometry", "crop_sequence", "field_class",
                          "created_at"],
        )
        return True

    def count_recent_drawn_fields(self, hours: int) -> int:
        return int(
            self._client.query(
                "SELECT uniqExact(field_id) FROM drawn_fields WHERE created_at > now() - INTERVAL {h:UInt32} HOUR",
                parameters={"h": hours},
            ).result_rows[0][0]
        )

    @ttl_cached()
    def get_indicator_rows(self, field_id: str) -> list[dict]:
        return [
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
            for r in self._client.query(self._INDICATORS_SQL, parameters={"field_id": field_id}).result_rows
        ]

    @ttl_cached()
    def get_indicators(self, field_id: str) -> IndicatorFacts:
        parameters = {"field_id": field_id}
        indicator_rows = self.get_indicator_rows(field_id)
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

    def store_analysis(self, analysis_id: str, field_id: str, engine_version: str, data_version: str, response_json: str) -> None:
        from datetime import datetime
        created_at = datetime.now(UTC)
        self._client.insert(
            "analyses",
            [[analysis_id, field_id, created_at, engine_version, data_version, response_json, "api"]],
            column_names=["analysis_id", "field_id", "created_at", "engine_version", "data_version", "response_json", "load_id"],
        )

    def get_analysis(self, analysis_id: str) -> dict | None:
        rows = self._client.query(
            "SELECT analysis_id, field_id, created_at, engine_version, data_version, response_json "
            "FROM analyses WHERE analysis_id = {analysis_id:String} LIMIT 1",
            parameters={"analysis_id": analysis_id},
        ).result_rows
        if not rows:
            return None
        r = rows[0]
        return {
            "analysis_id": r[0],
            "field_id": r[1],
            "created_at": r[2].isoformat() if hasattr(r[2], "isoformat") else str(r[2]),
            "engine_version": r[3],
            "data_version": r[4],
            "response_json": r[5],
        }

    @ttl_cached()
    def get_marsden_means(self) -> list[dict]:
        """Nine-year mean rows from marsden_management."""
        rows = self._client.query(
            "SELECT rotation, metric, value, unit, evidence_type, source_id "
            "FROM marsden_management "
            "WHERE first_year = 2003 AND last_year = 2011 "
            "ORDER BY rotation, metric"
        ).result_rows
        return [{"rotation": str(r[0]), "metric": r[1], "value": float(r[2]), "unit": r[3], "evidence_type": str(r[4]), "source_id": r[5]} for r in rows]

    @ttl_cached()
    def get_lineage_row(self, indicator_id: str) -> dict | None:
        rows = self._client.query(
            "SELECT indicator_id, label, source_ids, variables, formula, aggregation_window, "
            "spatial_support, scale, resolution, evidence_type, missing_data_rule, interpretation, limitation, code_version "
            "FROM indicator_lineage WHERE indicator_id = {indicator_id:String} LIMIT 1",
            parameters={"indicator_id": indicator_id},
        ).result_rows
        if not rows:
            return None
        r = rows[0]
        import json as _json
        return {"indicator_id": r[0], "label": r[1], "source_ids": _json.loads(r[2]) if r[2] else [], "variables": _json.loads(r[3]) if r[3] else [], "formula": r[4], "aggregation_window": r[5], "spatial_support": r[6], "scale": r[7], "resolution": r[8], "evidence_type": str(r[9]), "missing_data_rule": r[10], "interpretation": r[11], "limitation": r[12], "code_version": r[13]}

    @ttl_cached()
    def get_all_lineage(self) -> list[dict]:
        rows = self._client.query(
            "SELECT indicator_id, label, formula, aggregation_window, scale, resolution, evidence_type, limitation "
            "FROM indicator_lineage ORDER BY indicator_id"
        ).result_rows
        return [{"indicator_id": r[0], "label": r[1], "formula": r[2], "aggregation_window": r[3], "scale": r[4], "resolution": r[5], "evidence_type": str(r[6]), "limitation": r[7]} for r in rows]

    @ttl_cached()
    def get_all_sources(self) -> list[dict]:
        rows = self._client.query(
            "SELECT source_id, provider, product, product_version, url, spatial_resolution, "
            "temporal_resolution, geographic_coverage, historical_coverage, retrieval_date, "
            "licence, known_limitations, evidence_type, file_count, total_bytes "
            "FROM data_sources ORDER BY source_id"
        ).result_rows
        return [{"source_id": r[0], "provider": r[1], "product": r[2], "product_version": r[3], "url": r[4], "spatial_resolution": r[5], "temporal_resolution": r[6], "geographic_coverage": r[7], "historical_coverage": r[8], "retrieval_date": r[9].isoformat() if hasattr(r[9], "isoformat") else str(r[9]), "licence": r[10], "known_limitations": r[11], "evidence_type": str(r[12]), "file_count": r[13], "total_bytes": r[14]} for r in rows]

    def get_climate_timeseries(self, field_id: str, from_date: str, to_date: str, max_points: int) -> list[dict]:
        """POWER daily climate for a field, downsampled."""
        cell_rows = self._client.query(
            "SELECT cell_id FROM climate_points WHERE point_id = {point_id:String} LIMIT 1",
            parameters={"point_id": field_id},
        ).result_rows
        if not cell_rows:
            return []
        cell_id = cell_rows[0][0]
        # count total rows to pick interval
        count_rows = self._client.query(
            "SELECT count() FROM climate_daily WHERE cell_id = {cell_id:String} AND date BETWEEN {from_date:Date} AND {to_date:Date}",
            parameters={"cell_id": cell_id, "from_date": from_date, "to_date": to_date},
        ).result_rows
        total = count_rows[0][0] if count_rows else 0
        variables = ["T2M_MAX", "T2M_MIN", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN"]
        var_count = len(variables)
        total_dates = total // var_count if var_count else total
        interval_days = max(1, (total_dates + max_points - 1) // max_points)
        rows = self._client.query(
            "SELECT toDate(toStartOfInterval(date, INTERVAL {interval_days:UInt32} DAY)) AS bucket, "
            "variable, round(avg(value), 2) AS mean_value, any(unit) AS unit, count() AS obs "  # not `AS value`: it would shadow the column in WHERE
            
            "FROM climate_daily "
            "WHERE cell_id = {cell_id:String} "
            "AND variable IN ('T2M_MAX', 'T2M_MIN', 'PRECTOTCORR', 'ALLSKY_SFC_SW_DWN') "
            "AND date BETWEEN {from_date:Date} AND {to_date:Date} "
            "AND value IS NOT NULL "
            "GROUP BY bucket, variable "
            "ORDER BY bucket, variable",
            parameters={"cell_id": cell_id, "from_date": from_date, "to_date": to_date, "interval_days": interval_days},
        ).result_rows
        return [{"date": r[0].isoformat() if hasattr(r[0], "isoformat") else str(r[0]), "variable": r[1], "value": r[2], "unit": r[3], "obs": r[4]} for r in rows]

    def get_ndvi_timeseries(self, field_id: str, from_date: str, to_date: str) -> list[dict]:
        """NDVI time series from hls_ndvi. Returns empty list until DS1 runs Phase 5."""
        try:
            rows = self._client.query(
                "SELECT toDate(acquired) AS date, 'ndvi_mean' AS variable, "
                "round(ndvi_mean, 4) AS value, '' AS unit, ndvi_valid_pixels AS obs "
                "FROM hls_ndvi "
                "WHERE field_id = {field_id:String} "
                "AND toDate(acquired) BETWEEN {from_date:Date} AND {to_date:Date} "
                "AND ndvi_mean IS NOT NULL "
                "ORDER BY date",
                parameters={"field_id": field_id, "from_date": from_date, "to_date": to_date},
            ).result_rows
        except Exception:
            # hls_ndvi doesn't exist yet (Phase 5 not yet run); return empty gracefully.
            return []
        return [{"date": r[0].isoformat() if hasattr(r[0], "isoformat") else str(r[0]), "variable": r[1], "value": r[2], "unit": r[3], "obs": r[4]} for r in rows]

    _TEST_SET_SQL = (
        "SELECT e.field_id, e.scenario, toString(e.outcome), e.crop_history_summary, e.rules_version, "
        "e.run_id, toString(f.role), f.county, toString(r.field_class) "
        "FROM engine_test_set AS e "
        "LEFT JOIN fields AS f ON e.field_id = f.field_id "
        "LEFT JOIN crop_rotation AS r ON e.field_id = r.field_id "
        # The newest ENGINE run by load time (run_ids are random, so max(run_id) would pick an arbitrary one).
        # Rows with scenario 'expected' are DS1's expected outcomes, not an engine run, and must never be taken for one:
        # when they were the newest rows, the audit came back empty.
        "WHERE e.scenario != 'expected' AND e.run_id = "
        "(SELECT argMax(run_id, loaded_at) FROM engine_test_set WHERE scenario != 'expected') "
        "ORDER BY e.field_id, e.scenario"
    )
    _EXPECTED_SQL = (
        "SELECT field_id, toString(outcome), run_id, rules_version FROM engine_test_set "
        "WHERE scenario = 'expected' AND run_id = "
        "(SELECT argMax(run_id, loaded_at) FROM engine_test_set WHERE scenario = 'expected')"
    )

    def get_expected_outcomes(self) -> dict | None:
        """DS1's expected outcome per field (the newest 'expected' load), or None when there is none."""
        rows = self._client.query(self._EXPECTED_SQL).result_rows
        if not rows:
            return None
        return {"run_id": str(rows[0][2]), "rules_version": str(rows[0][3]), "by_field": {str(r[0]): str(r[1]) for r in rows}}

    def get_test_set_rows(self) -> list[dict]:
        """DS's engine test-set audit (newest run), one row per field and scenario.

        `selection_label` is the team's label from when the field was chosen (the committed notes);
        `field_class` is DS1's classification of the CDL history. Both are CDL-derived.
        """
        keys = ("field_id", "scenario", "outcome", "crop_history_summary", "rules_version",
                "run_id", "role", "county", "field_class")
        rows = [dict(zip(keys, row)) for row in self._client.query(self._TEST_SET_SQL).result_rows]
        for row in rows:
            noted = self._notes.get_field(row["field_id"]) if self._notes else None
            row["selection_label"] = noted.field_class if noted else None
        return rows

    _REGISTER_TABLES: ClassVar[dict[str, tuple[str, str, tuple[str, ...]]]] = {
        "rules": (
            "engine_rules",
            (
                "rule_id, applies_to, context_key, operator, value, toString(effect), condition_text, rationale, "
                "toString(evidence_basis), toString(review)"
            ),
            ("rule_id", "applies_to", "context_key", "operator", "value", "effect", "condition_text", "rationale",
             "evidence_basis", "review"),
        ),
        "crop_claims": (
            "engine_crop_claims",
            "claim_id, crop, claim, toString(status), evidence_type, source, note",
            ("claim_id", "crop", "claim", "status", "evidence_type", "source", "note"),
        ),
        "outcomes": (
            "engine_outcomes",
            "outcome_id, label, claimable, evidence_type, source, statement, caution, caution_reference",
            ("outcome_id", "label", "claimable", "evidence_type", "source", "statement", "caution",
             "caution_reference"),
        ),
        "strategies": (
            "engine_strategies",
            "strategy_id, label, rotation, phases, why_included, operational_requirements, evidence_anchor",
            ("strategy_id", "label", "rotation", "phases", "why_included", "operational_requirements",
             "evidence_anchor"),
        ),
    }

    @ttl_cached()
    def get_rule_register(self) -> dict | None:
        """DS2's rule register (newest rules_version, by load time), or None when nothing is loaded."""
        version_rows = self._client.query(
            "SELECT argMax(rules_version, loaded_at) FROM engine_rules"
        ).result_rows
        version = version_rows[0][0] if version_rows else ""
        if not version:
            return None

        def read(spec: tuple[str, str, tuple[str, ...]]) -> list[dict]:
            table, columns, names = spec
            rows = self._client.query(
                f"SELECT {columns} FROM {table} WHERE rules_version = {{v:String}} ORDER BY 1",
                parameters={"v": version},
            ).result_rows
            return [dict(zip(names, row)) for row in rows]

        # Four independent reads; the database is remote, so run them side by side (the client is thread-safe).
        with ThreadPoolExecutor(max_workers=len(self._REGISTER_TABLES)) as pool:
            tables = dict(zip(self._REGISTER_TABLES, pool.map(read, self._REGISTER_TABLES.values())))
        return {"rules_version": str(version), **tables}

    _FEEDBACK_COLUMNS = (
        "feedback_id", "role", "farming_context", "usefulness", "clarity", "what_was_missing", "would_use",
        "contact", "contact_consent", "field_id", "analysis_id",
    )

    def save_feedback(self, row: dict) -> None:
        self._client.insert(
            "feedback",
            [[row[c] for c in self._FEEDBACK_COLUMNS]],
            column_names=list(self._FEEDBACK_COLUMNS),
        )

    def count_recent_feedback(self, hours: int) -> int:
        return int(
            self._client.query(
                "SELECT count() FROM feedback WHERE created_at > now() - INTERVAL {h:UInt32} HOUR",
                parameters={"h": hours},
            ).result_rows[0][0]
        )

    @ttl_cached()
    def list_demo_fields_with_geometry(self) -> list[dict]:
        """All fields with their geometry from the GeoJSON file."""
        import json as _json
        from pathlib import Path as _Path
        fields_path = _Path(__file__).resolve().parents[2] / "data" / "fields" / "fields.geojson"
        geojson = _json.loads(fields_path.read_text(encoding="utf-8"))
        geom_by_id = {f["properties"]["field_id"]: f["geometry"] for f in geojson["features"]}

        # Get field data from ClickHouse
        rows = self._client.query(self._FIELDS_SQL).result_rows
        from pyproj import Transformer
        from shapely.geometry import shape
        from shapely.ops import transform as shp_transform
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:32615", always_xy=True)
        result = []
        for row in rows:
            field_id, role, boundary_source, county, _field_class = row
            geom = geom_by_id.get(field_id)
            if geom is None:
                continue
            shp = shape(geom)
            projected = shp_transform(transformer.transform, shp)
            area_ha = round(projected.area / 10000, 1)
            result.append({
                "field_id": field_id,
                "county": county,
                "role": str(role),
                "boundary_source": str(boundary_source),
                "is_demo": True,
                "area_ha": area_ha,
                "geometry": geom,
            })
        return sorted(result, key=lambda x: (x["role"] != "primary", x["field_id"]))

    def log_ask(
        self,
        log_id: str,
        context_type: str,
        context_id: str,
        field_id: str,
        question: str,
        answer: str,
        citations: list[str],
        refused: bool,
        audience: str,
        model: str,
    ) -> None:
        from datetime import datetime
        self._client.insert(
            "ask_log",
            [[
                log_id, context_type, context_id, field_id,
                question, answer, citations, int(refused),
                audience, model, datetime.now(UTC), "api",
            ]],
            column_names=[
                "log_id", "context_type", "context_id", "field_id",
                "question", "answer", "citations", "refused",
                "audience", "model", "created_at", "load_id",
            ],
        )
