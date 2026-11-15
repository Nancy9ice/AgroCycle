import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pandera.errors
import pytest

from common import schema_check
from common.schemas import DATA_SOURCES, FIELDS, INDICATOR_LINEAGE, TABLES
from ingest.manifest import EVIDENCE_TYPES
from transform.indicators import runner

ROOT = Path(__file__).resolve().parent.parent


def test_valid_frames_pass(data_sources_frame, lineage_frame, fields_frame):
    DATA_SOURCES.validate(data_sources_frame)
    INDICATOR_LINEAGE.validate(lineage_frame)
    FIELDS.validate(fields_frame)


@pytest.mark.parametrize("bad", ["fire", "", "Observed"])
def test_unknown_evidence_type_is_rejected(lineage_frame, bad):
    lineage_frame["evidence_type"] = bad
    with pytest.raises(pandera.errors.SchemaError):
        INDICATOR_LINEAGE.validate(lineage_frame)


def test_null_and_empty_keys_are_rejected(lineage_frame, fields_frame):
    lineage_frame.loc[0, "indicator_id"] = None
    with pytest.raises(pandera.errors.SchemaError):
        INDICATOR_LINEAGE.validate(lineage_frame)
    fields_frame.loc[0, "field_id"] = ""
    with pytest.raises(pandera.errors.SchemaError):
        FIELDS.validate(fields_frame)


def test_duplicate_natural_key_is_rejected(fields_frame, data_sources_frame):
    fields_frame.loc[1, "field_id"] = "primary-001"
    with pytest.raises(pandera.errors.SchemaError):
        FIELDS.validate(fields_frame)
    data_sources_frame.loc[1, "source_id"] = data_sources_frame.loc[0, "source_id"]
    with pytest.raises(pandera.errors.SchemaError):
        DATA_SOURCES.validate(data_sources_frame)


def test_lineage_without_a_limitation_is_rejected(lineage_frame):
    lineage_frame["limitation"] = ""
    with pytest.raises(pandera.errors.SchemaError):
        INDICATOR_LINEAGE.validate(lineage_frame)


@pytest.mark.parametrize("column", ["provider", "url", "spatial_resolution", "temporal_resolution", "geographic_coverage",
                                    "historical_coverage", "licence", "processing_steps", "quality_flags",
                                    "known_limitations", "compiled_from"])
def test_a_source_missing_any_prd_field_is_rejected(data_sources_frame, column):
    with pytest.raises((pandera.errors.SchemaError, pandera.errors.SchemaErrors)):
        DATA_SOURCES.validate(data_sources_frame.assign(**{column: ""}))


@pytest.mark.parametrize("variables", ["", "[]", "not json", '["a", ""]', '"a string"', '{"a": 1}'])
def test_variables_must_be_a_non_empty_json_list_of_names(data_sources_frame, variables):
    with pytest.raises((pandera.errors.SchemaError, pandera.errors.SchemaErrors)):
        DATA_SOURCES.validate(data_sources_frame.assign(variables=variables))


def test_a_source_with_no_files_a_negative_size_or_an_unknown_prefix_is_rejected(data_sources_frame):
    for bad in (data_sources_frame.assign(file_count=0), data_sources_frame.assign(total_bytes=-1),
                data_sources_frame.assign(raw_s3_prefix="s3://elsewhere")):
        with pytest.raises((pandera.errors.SchemaError, pandera.errors.SchemaErrors)):
            DATA_SOURCES.validate(bad)


def test_links_pass_and_a_repeat_or_an_unknown_type_is_rejected(source_links_frame):
    from common.schemas import SOURCE_LINKS

    SOURCE_LINKS.validate(source_links_frame)
    with pytest.raises((pandera.errors.SchemaError, pandera.errors.SchemaErrors)):
        SOURCE_LINKS.validate(pd.concat([source_links_frame, source_links_frame.head(1)], ignore_index=True))
    with pytest.raises((pandera.errors.SchemaError, pandera.errors.SchemaErrors)):
        SOURCE_LINKS.validate(source_links_frame.assign(subject_type="column"))


def test_unexpected_column_is_rejected(fields_frame):
    with pytest.raises((pandera.errors.SchemaError, pandera.errors.SchemaErrors)):
        FIELDS.validate(fields_frame.assign(extra=1))


def test_sql_and_schemas_agree():
    assert schema_check.problems() == []


def test_schema_check_catches_a_missing_column(tmp_path):
    sql = (ROOT / "schema" / "006_data_sources.sql").read_text().replace("    provider String,\n", "")
    (tmp_path / "006_data_sources.sql").write_text(sql)
    assert any("data_sources" in p and "provider" in p for p in schema_check.problems(tmp_path))


def test_sql_enum_matches_manifest_labels():
    sql = (ROOT / "schema" / "001_core.sql").read_text()
    for name in EVIDENCE_TYPES:
        assert f"'{name}'" in sql


def test_registry_keys_are_schema_columns():
    for spec in TABLES.values():
        assert set(spec.key) <= set(spec.schema.columns)
        assert set(spec.text_keys) <= set(spec.key)


def test_ds2_lineage_rows_fit_the_table():
    """DS2's runner output is the contract: every row it writes must validate unchanged."""
    frame = pd.DataFrame(runner.lineage_rows("run-1"))
    assert len(frame) > 0
    INDICATOR_LINEAGE.validate(frame)


def test_the_45_demo_fields_fit_the_table():
    raw = json.loads((ROOT / "data" / "fields" / "fields.geojson").read_text())
    geo = gpd.GeoDataFrame.from_features(raw["features"], crs="EPSG:4326")
    frame = pd.DataFrame(geo.drop(columns="geometry"))
    frame["geometry_wkt"] = geo.geometry.to_wkt()
    frame["cover_detail"] = frame["cover_detail"].fillna("")
    assert len(FIELDS.validate(frame)) == 45


def test_a_time_of_day_in_retrieval_date_is_rejected(data_sources_frame):
    """The column is a Date: two timestamps on one day would collapse to one key in the database."""
    bad = data_sources_frame.assign(retrieval_date=pd.to_datetime(["2026-11-14 08:00", "2026-11-14 17:00"]))
    with pytest.raises((pandera.errors.SchemaError, pandera.errors.SchemaErrors)):
        DATA_SOURCES.validate(bad)


def test_schema_check_catches_an_enum_that_drifts_from_the_schema(tmp_path):
    sql = (ROOT / "schema" / "004_hls_valid_pixels.sql").read_text()
    (tmp_path / "004_hls_valid_pixels.sql").write_text(sql.replace("'no_data' = 2", "'no_data' = 2, 'partial' = 3"))
    assert any("hls_valid_pixels.status" in p for p in schema_check.problems(tmp_path))
