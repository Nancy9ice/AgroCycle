"""Shared fixtures: valid frames for each core table and a fake ClickHouse client."""

import pandas as pd
import pytest

SHA = "a" * 64


class FakeResult:
    def __init__(self, rows):
        self.result_rows = rows


class FakeClient:
    """Records every statement in order. `responses` maps a substring of a query to its rows
    (first match wins); any other query returns [(0,)]."""

    def __init__(self, responses=None):
        self.responses = responses or []
        self.calls: list[tuple[str, str]] = []  # (kind, text)
        self.inserted: dict[str, pd.DataFrame] = {}

    def command(self, sql):
        self.calls.append(("command", sql))

    def insert(self, table, data, column_names=None):
        self.calls.append(("insert", table))

    def insert_df(self, table, frame):
        self.calls.append(("insert_df", table))
        self.inserted[table] = frame

    def query(self, sql):
        self.calls.append(("query", sql))
        for needle, rows in self.responses:
            if needle in sql:
                return FakeResult(rows)
        return FakeResult([(0,)])

    def statements(self):
        return [text for _, text in self.calls]


@pytest.fixture
def data_sources_frame():
    return pd.DataFrame(
        {
            "source_id": ["cdl", "cdl"],
            "s3_key": ["raw/cdl/v1/2026-11-14/a.tif", "raw/cdl/v1/2026-11-14/b.tif"],
            "source_url": ["https://example.org/a", "https://example.org/b"],
            "product": ["CDL", "CDL"],
            "version": ["v1", "v1"],
            "retrieval_date": pd.to_datetime(["2026-11-14", "2026-11-14"]),
            "sha256": [SHA, SHA],
            "size_bytes": [10, 20],
            "licence": ["public domain", "public domain"],
            "subset": ['{"kind": "county"}', '{"kind": "county"}'],
            "evidence_type": ["classified", "classified"],
            "scale": ["30 m raster", "30 m raster"],
            "notes": ["", ""],
        }
    )


@pytest.fixture
def lineage_frame():
    return pd.DataFrame(
        {
            "indicator_id": ["gdd"],
            "label": ["gdd"],
            "source_ids": ['["NASA POWER"]'],
            "variables": ['["T2M"]'],
            "formula": ["sum of daily means above base"],
            "aggregation_window": ["growing season"],
            "spatial_support": ["POWER grid cell"],
            "scale": ["grid"],
            "resolution": ["about 50 km"],
            "evidence_type": ["model_reanalysis"],
            "missing_data_rule": ["unknown below 75 % coverage"],
            "interpretation": ["heat available to a crop"],
            "limitation": ["grid, not field"],
            "code_version": ["v1"],
            "run_id": ["run-1"],
        }
    )


@pytest.fixture
def fields_frame():
    return pd.DataFrame(
        {
            "field_id": ["primary-001", "test-001"],
            "role": ["primary", "test"],
            "boundary_source": ["demo", "demo"],
            "county": ["Story", "Boone"],
            "provenance": ["generated", "generated"],
            "domain_note": ["in-domain", "in-domain"],
            "cover_detail": ["", ""],
            "geometry_wkt": ["POLYGON ((0 0, 1 0, 1 1, 0 0))", "POLYGON ((0 0, 1 0, 1 1, 0 0))"],
        }
    )


@pytest.fixture
def crop_shares_frame():
    return pd.DataFrame(
        {
            "field_id": ["primary-001"] * 3,
            "year": [2015, 2015, 2016],
            "cdl_class_code": [5, 27, 1],
            "cdl_class_name": ["Soybeans", "Rye", "Corn"],
            "class_group": ["soybeans", "other_crop", "corn"],
            "flag": ["", "unlisted_code", ""],
            "pixels": [440, 44, 484],
            "share_pct": [90.909, 9.091, 100.0],
            "resolution_m": [30, 30, 30],
            "product_version": ["CDL 2015 (annual-30m-website-export)"] * 2 + ["CDL 2016 (annual-30m-website-export)"],
            "source_s3_key": ["raw/cdl/annual-30m-website-export/2026-11-14/CDL_2015_19169.tif"] * 2
            + ["raw/cdl/annual-30m-website-export/2026-11-14/CDL_2016_19169.tif"],
        }
    )


@pytest.fixture
def crop_history_frame():
    return pd.DataFrame(
        {
            "field_id": ["primary-001", "primary-001"],
            "year": [2015, 2016],
            "dominant_group": ["soybeans", "corn"],
            "status": ["ok", "ok"],
            "dominant_share_pct": [90.909, 100.0],
            "nodata_share_pct": [0.0, 0.0],
            "total_pixels": [484, 484],
            "rule_version": ["ds1-cdl-rules-v1.0"] * 2,
            "evidence_type": ["classified", "classified"],
        }
    )


@pytest.fixture
def crop_rotation_frame():
    return pd.DataFrame(
        {
            "field_id": ["primary-001"],
            "field_class": ["rotation"],
            "sequence": ["S C S C S C S C S C S"],
            "corn_years": [5],
            "soybean_years": [6],
            "pasture_hay_years": [0],
            "alternations": [10],
            "transitions_counted": [10],
            "rule_version": ["ds1-cdl-rules-v1.0"],
            "evidence_type": ["derived"],
            "limitation": ["Derived from the CDL, not ground truth."],
        }
    )
