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

    def query(self, sql, parameters=None):
        self.calls.append(("query", sql))
        self.parameters = parameters
        for needle, rows in self.responses:
            if needle in sql:
                return FakeResult(rows)
        return FakeResult([(0,)])

    def statements(self):
        return [text for _, text in self.calls]


@pytest.fixture
def data_sources_frame():
    """Two sources with every PRD 6.1 field, shaped like the eight real rows."""
    def row(source_id, product, evidence, prefix):
        return {
            "source_id": source_id, "provider": "A data provider", "product": product, "product_version": "v1",
            "url": "https://example.org/" + source_id, "variables": '["variable one", "variable two"]',
            "spatial_resolution": "30 m", "temporal_resolution": "annual", "geographic_coverage": "Story and Boone Counties, Iowa",
            "historical_coverage": "2015-2025", "retrieval_date": pd.Timestamp("2026-11-14"), "licence": "public domain",
            "processing_steps": "stored unchanged, then clipped", "quality_flags": "none in the product",
            "known_limitations": "a classified product, not ground truth", "evidence_type": evidence,
            "raw_s3_prefix": prefix, "file_count": 44, "total_bytes": 41_000_000,
            "compiled_from": "manifests and the DS source sheets, compiled by the DE",
        }
    return pd.DataFrame([row("cdl", "Cropland Data Layer", "classified", "raw/cdl/v/2026-11-14/"),
                         row("power", "POWER daily point", "model_reanalysis", "raw/power/v/2026-11-14/")])


@pytest.fixture
def source_links_frame():
    return pd.DataFrame({
        "subject_type": ["indicator", "table", "table"],
        "subject_id": ["gdd", "climate_daily", "crop_history"],
        "source_id": ["power", "power", "cdl"],
    })


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


@pytest.fixture
def hls_frame():
    return pd.DataFrame(
        {
            "field_id": ["primary-001", "primary-001", "primary-001"],
            "sensor": ["l30", "s30", "l30"],
            "acquired": pd.to_datetime(["2023-04-05", "2023-04-06", "2023-04-14"]),
            "sensing_time": ["T165930", "T170001", "T165311"],
            "status": ["observed", "observed", "no_data"],
            "total_pixels": [484, 484, 484],
            "fill_pixels": [0, 4, 484],
            "flagged_pixels": [100, 80, 0],
            "valid_pixels": [384, 400, 0],
            "valid_share": [384 / 484, 400 / 484, 0.0],
            "mask_rule": ["Fmask & 0b00111110 == 0; Fmask 255 and reflectance -9999 are fill"] * 3,
            "source_s3_key": ["raw/hls/l30/v2.0/2026-11-14/primary-001/20230405/T165930_stack_b04_b05_b06_fmask.tif",
                              "raw/hls/s30/v2.0/2026-11-14/primary-001/20230406/T170001_stack_b04_b8a_b11_fmask.tif",
                              "raw/hls/no-data/v2.0/2026-11-14/skipped_no_data.csv"],
        }
    )


@pytest.fixture
def marsden_outputs():
    """Synthetic outputs shaped like DS2's, consistent with DS2's schemas: 3 rotations x 9 seasons."""
    from transform.marsden_load import INDICATORS, Outputs

    rows = []
    for rotation, base_n, manure, herb in (("2-yr", 70.0, 0.0, 1.9), ("3-yr", 16.0, 40.0, 0.25), ("4-yr", 10.0, 30.0, 0.2)):
        for i, year in enumerate(range(2003, 2012)):
            m, u = base_n + i, manure
            rows.append({"rotation": rotation, "year": year, "manufactured_n": m, "manure_n": u,
                         "applied_n": m + u, "herbicide": herb + i / 100})
    by_year = pd.DataFrame(rows)
    summary = by_year.groupby("rotation")[["manufactured_n", "manure_n", "applied_n", "herbicide"]].mean().reset_index()
    summary["n_years"] = 9
    statuses = ["MATCH"] * 17 + ["WITHIN_SEM", "UNRECONCILED", "INFO"]
    reconciliation = pd.DataFrame({
        "quantity": [f"check_{i}" for i in range(20)], "rotation": ["2-yr"] * 20,
        "computed": [1.0] * 20, "reference": [1.0] * 20,
        "source": ["PRD s7.4 / roadmap Phase 6"] * 12 + ["Davis 2012 Results text"] * 8,
        "rule": ["within half of last digit (0.05)"] * 20, "status": statuses,
        "note": [""] * 18 + ["Table S3 gives 74.5, the text gives 80"] + [""],
    })
    units = {"marsden_manufactured_n_kg_ha_yr": "kg N ha-1 yr-1", "marsden_manure_n_kg_ha_yr": "kg N ha-1 yr-1",
             "marsden_applied_n_kg_ha_yr": "kg N ha-1 yr-1", "marsden_herbicide_kg_ai_ha_yr": "kg ai ha-1 yr-1"}
    lineage = [{
        "indicator_id": indicator, "variables": f"Table S3 and S4 values for {metric}", "formula": "mean over 2003-2011",
        "unit": units[indicator], "source": "Marsden Farm supplementary data, Davis et al. (2012) PLOS ONE",
        "source_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC3468434/", "product_version": "PLOS ONE 7(10), Oct 2012",
        "spatial_scale": "single experimental site (Marsden Farm, Boone Co., Iowa)",
        "temporal_window": "annual, 2003-2011 (9 seasons)", "missing_data_rule": "none permitted",
        "evidence_type": "experimental", "limitation": "Treatment-level table values, not plot-level records; one site.",
    } for metric, indicator in INDICATORS.items()]
    manifest = {"script": "marsden_repro.py", "script_sha256": "2f2eb2dfd2185bf2a6d20d6c66dcf29de781ede0faef981df4de56a1ea3b6648",
                "inputs": {"pone.0047149.s004.docx": "a" * 64, "pone.0047149.s005.docx": "b" * 64},
                "run_utc": "2026-11-15T05:48:36+00:00"}
    return Outputs(by_year, summary, reconciliation, lineage, manifest)
