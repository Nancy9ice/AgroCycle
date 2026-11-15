import pandera.pandas as pa
import pytest

from common import schema_check
from transform.naip import build

T1, T2 = "ia_m_4209358_se_15_060_20250813", "ia_m_4109302_ne_15_060_20250805"


def _manifest(field="test-001", tiles=(T1,), flights=("2025-08-13",), **over):
    subset = {"kind": "field_chip", "field_id": field, "bbox": [-93.80, 42.00, -93.79, 42.01], "buffer_m": 50.0,
              "year": 2025, "bands": ["Red", "Green", "Blue", "NIR"], "tiles": list(tiles),
              "flight_dates": list(flights)}
    doc = {"subset": subset, "size_bytes": 2_000_000, "sha256": "a" * 64, "retrieval_date": "2026-11-15",
           "evidence_type": "observed"}
    return doc | over


def _key(field="test-001"):
    return f"raw/naip/naip-2025/2026-11-15/{field}_naip2025.tif.manifest.json"


def test_one_row_per_field_and_tile_with_the_flight_date_from_the_tile_name():
    frame = build.build({_key(): _manifest(),
                         _key("test-032"): _manifest("test-032", (T1, T2), ("2025-08-05", "2025-08-13"))})
    assert len(frame) == 3 and set(frame["field_id"]) == {"test-001", "test-032"}
    row = frame[(frame.field_id == "test-032") & (frame.tile_id == T2)].iloc[0]
    assert row["flight_date"].date().isoformat() == "2025-08-05" and row["resolution_m"] == 0.6
    assert row["s3_key"] == "raw/naip/naip-2025/2026-11-15/test-032_naip2025.tif"
    assert row["bands"] == "Red,Green,Blue,NIR"


def test_a_tile_date_not_in_the_manifest_is_refused():
    with pytest.raises(build.NaipBuildError, match="not among"):
        build.build({_key(): _manifest(flights=("2025-09-01",))})


def test_unknown_year_and_wrong_kind_and_empty_are_refused():
    bad_year = _manifest()
    bad_year["subset"]["year"] = 2023
    with pytest.raises(build.NaipBuildError, match="no known resolution"):
        build.build({_key(): bad_year})
    other = _manifest()
    other["subset"]["kind"] = "county"
    with pytest.raises(build.NaipBuildError, match="not a field chip"):
        build.build({_key(): other})
    with pytest.raises(build.NaipBuildError, match="no NAIP manifests"):
        build.build({})


def test_the_schema_rejects_a_box_outside_iowa_and_a_bad_checksum():
    with pytest.raises(pa.errors.SchemaError):
        bad = _manifest()
        bad["subset"]["bbox"] = [10.0, 42.00, 10.1, 42.01]
        build.build({_key(): bad})
    with pytest.raises(pa.errors.SchemaError):
        build.build({_key(): _manifest(sha256="xyz")})


def test_the_sql_names_the_schema_columns():
    assert schema_check.problems() == []
