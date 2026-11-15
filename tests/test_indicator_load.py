"""DS2's indicator CSVs: reading, the checks that refuse a load, and the schemas."""

import json
from pathlib import Path

import pandas as pd
import pandera.errors
import pytest

from common.schemas import FIELD_INDICATORS, INDICATOR_LINEAGE, SOIL_PROPERTIES
from transform.indicators import load as indicator_load
from transform.indicators import runner

SCHEMA_ERRORS = (pandera.errors.SchemaError, pandera.errors.SchemaErrors)
REAL = indicator_load.DEFAULT_DIR
FIELDS = {"primary-001", "test-001"}

INDICATOR_COLUMNS = ["field_id", "indicator_id", "category", "value", "unit", "status", "window_start",
                     "window_end", "valid_obs", "unknown_reason", "run_id"]
SOIL_COLUMNS = ["field_id", "mukey", "mu_name", "share_pct", "property", "value_num", "value_text", "unit",
                "indicator_id", "run_id"]


def write_files(directory: Path, indicators, soil, lineage=None):
    pd.DataFrame(indicators, columns=INDICATOR_COLUMNS).to_csv(directory / "field_indicators.csv", index=False)
    pd.DataFrame(soil, columns=SOIL_COLUMNS).to_csv(directory / "soil_properties.csv", index=False)
    lineage = lineage if lineage is not None else runner.lineage_rows("run-1")
    pd.DataFrame(lineage).to_csv(directory / "indicator_lineage.csv", index=False)


GDD = ["primary-001", "gdd", "climate", 1800.5, "degree-days C", "available", "2023-04-01", "2023-11-30", 244, "", "run-1"]
UNKNOWN = ["primary-001", "heat_days", "climate", "", "days", "unknown", "2024-04-01", "2024-11-30", 100,
           "fewer than 75 % of days", "run-1"]
SOIL_UNIT = ["primary-001", "2345", "Canisteo", 30.5, "map_unit_share", 30.5, "", "% of field area", "map_unit_share", "run-1"]
SOIL_CLASS = ["primary-001", "", "", 60.0, "drainagecl", 60.0, "Poorly drained", "% of field area", "drainagecl", "run-1"]
SOIL_OM = ["primary-001", "", "", "", "om_r", "", "", "%", "om_r_0_30cm", "run-1"]


@pytest.fixture
def folder(tmp_path):
    write_files(tmp_path, [GDD, UNKNOWN], [SOIL_UNIT, SOIL_CLASS], lineage_without("map_unit_share"))
    return tmp_path


def lineage_without(*ids):
    """DS2's runner lineage with some rows taken out: the incomplete file the loader must refuse."""
    return [r for r in runner.lineage_rows("run-1") if r["indicator_id"] not in ids]


def complete_lineage(*ids):
    """The runner's lineage, plus a row for any of `ids` it does not already hold (it now holds them all)."""
    rows = runner.lineage_rows("run-1")
    have = {r["indicator_id"] for r in rows}
    template = dict(rows[0])
    return rows + [{**template, "indicator_id": i, "label": i} for i in ids if i not in have]


def test_blank_cells_are_read_by_column_not_as_nan_text(folder):
    frames = indicator_load.read_frames(folder)
    fi, sp = frames["field_indicators"], frames["soil_properties"]
    assert pd.isna(fi.loc[1, "value"]) and fi.loc[0, "value"] == 1800.5
    assert fi["window_start"].dtype == "datetime64[ns]" and str(fi["valid_obs"].dtype) == "Int64"
    assert pd.isna(fi.loc[0, "unknown_reason"]) and fi.loc[1, "unknown_reason"].startswith("fewer")
    assert list(sp["mukey"]) == ["2345", ""]  # the class row keeps an empty mukey, not null
    assert pd.isna(sp.loc[0, "value_text"]) and sp.loc[1, "value_text"] == "Poorly drained"
    assert "nan" not in set(sp["mu_name"]) | set(sp["mukey"])


def test_a_clean_set_passes_every_schema_and_has_no_problems(tmp_path):
    write_files(tmp_path, [GDD, UNKNOWN], [SOIL_UNIT, SOIL_CLASS], complete_lineage("map_unit_share"))
    frames = indicator_load.read_frames(tmp_path)
    FIELD_INDICATORS.validate(frames["field_indicators"])
    SOIL_PROPERTIES.validate(frames["soil_properties"])
    INDICATOR_LINEAGE.validate(frames["indicator_lineage"])
    assert indicator_load.problems(frames, None, FIELDS) == []


def test_an_indicator_without_a_lineage_row_is_refused_and_named(folder):
    frames = indicator_load.read_frames(folder)
    found = indicator_load.problems(frames, None, FIELDS)
    assert len(found) == 1 and "1 indicators have no lineage row: map_unit_share" in found[0]


def test_unknown_fields_mixed_runs_and_manifest_mismatch_are_refused(tmp_path):
    other = [*GDD[:-1], "run-2"]
    write_files(tmp_path, [GDD, other], [SOIL_UNIT], complete_lineage("map_unit_share"))
    frames = indicator_load.read_frames(tmp_path)
    found = indicator_load.problems(frames, {"run_id": "run-9", "rows": {"field_indicators": 5}}, {"test-001"})
    assert any("not in fields.geojson" in p for p in found)
    assert any("2 runs" in p for p in found)
    assert any("manifest says 5" in p for p in found)
    assert any("run-9" in p for p in found)


def test_a_null_value_cannot_be_available(folder):
    frames = indicator_load.read_frames(folder)
    bad = frames["field_indicators"].copy()
    bad.loc[1, "status"] = "available"
    with pytest.raises(SCHEMA_ERRORS):
        FIELD_INDICATORS.validate(bad)


def test_the_same_indicator_in_two_seasons_is_not_a_duplicate_but_the_same_season_twice_is(tmp_path):
    season_two = [*GDD[:6], "2024-04-01", "2024-11-30", *GDD[8:]]
    write_files(tmp_path, [GDD, season_two], [SOIL_UNIT], complete_lineage("map_unit_share"))
    FIELD_INDICATORS.validate(indicator_load.read_frames(tmp_path)["field_indicators"])
    write_files(tmp_path, [GDD, GDD], [SOIL_UNIT], complete_lineage("map_unit_share"))
    with pytest.raises(SCHEMA_ERRORS):
        FIELD_INDICATORS.validate(indicator_load.read_frames(tmp_path)["field_indicators"])


def test_soil_indicators_have_no_window_and_two_of_them_do_not_collide(tmp_path):
    soil_a = ["primary-001", "", "", 50.0, "slope", "", "", "%", "slope_r", "run-1"]
    soil_indicator = ["primary-001", "slope_r", "soil", 3.2, "%", "available", "", "", "", "", "run-1"]
    other_indicator = [*soil_indicator]
    other_indicator[1] = "om_r_0_30cm"
    write_files(tmp_path, [soil_indicator, other_indicator], [soil_a], complete_lineage("slope_r", "om_r_0_30cm"))
    frames = indicator_load.read_frames(tmp_path)
    FIELD_INDICATORS.validate(frames["field_indicators"])
    assert frames["field_indicators"]["window_start"].isna().all()


def test_main_refuses_without_touching_the_database(folder, monkeypatch, capsys):
    monkeypatch.setattr(indicator_load, "load_all", lambda frames: pytest.fail("the database must not be touched"))
    monkeypatch.setattr(indicator_load, "load_fields", lambda: pd.DataFrame({"field_id": sorted(FIELDS)}))
    assert indicator_load.main(["--dir", str(folder), "--load"]) == 1
    assert "REFUSED" in capsys.readouterr().out


def test_main_dry_run_passes_a_clean_set_and_loads_nothing(tmp_path, monkeypatch, capsys):
    write_files(tmp_path, [GDD], [SOIL_UNIT], complete_lineage("map_unit_share"))
    monkeypatch.setattr(indicator_load, "load_all", lambda frames: pytest.fail("a dry run must not load"))
    monkeypatch.setattr(indicator_load, "load_fields", lambda: pd.DataFrame({"field_id": sorted(FIELDS)}))
    assert indicator_load.main(["--dir", str(tmp_path)]) == 0
    assert "dry run" in capsys.readouterr().out


def test_a_missing_folder_is_reported_cleanly(tmp_path, capsys):
    assert indicator_load.main(["--dir", str(tmp_path / "nowhere")]) == 1
    assert "indicator load:" in capsys.readouterr().out


@pytest.mark.skipif(not (REAL / "field_indicators.csv").exists(), reason="DS2's CSVs are not in data/out/indicators")
def test_ds2s_real_files_fit_the_schemas_and_match_their_manifest():
    frames = indicator_load.read_frames(REAL)
    FIELD_INDICATORS.validate(frames["field_indicators"])
    SOIL_PROPERTIES.validate(frames["soil_properties"])
    INDICATOR_LINEAGE.validate(frames["indicator_lineage"])
    manifest_path = REAL / "run_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        assert {n: len(frames[n]) for n in indicator_load.FILES} == manifest["rows"]


def test_a_manifest_without_rows_and_an_empty_file_are_reported_not_crashes(tmp_path, capsys, monkeypatch):
    write_files(tmp_path, [GDD], [SOIL_UNIT], complete_lineage("map_unit_share"))
    frames = indicator_load.read_frames(tmp_path)
    found = indicator_load.problems(frames, {"run_id": "run-1"}, FIELDS)
    assert any("manifest says None" in p for p in found)
    (tmp_path / "soil_properties.csv").write_text("")
    monkeypatch.setattr(indicator_load, "load_all", lambda frames: pytest.fail("nothing may load"))
    assert indicator_load.main(["--dir", str(tmp_path), "--load"]) == 1
    assert "indicator load:" in capsys.readouterr().out


def test_an_empty_frame_is_refused_before_any_table_is_loaded(tmp_path):
    write_files(tmp_path, [GDD], [], complete_lineage("map_unit_share"))
    frames = indicator_load.read_frames(tmp_path)
    assert "soil_properties is empty" in indicator_load.problems(frames, None, FIELDS)


def test_share_rounding_over_100_is_tolerated_and_empty_value_text_is_not(tmp_path):
    over = [*SOIL_UNIT]
    over[3] = 100.00000000000001
    write_files(tmp_path, [GDD], [over], complete_lineage("map_unit_share"))
    SOIL_PROPERTIES.validate(indicator_load.read_frames(tmp_path)["soil_properties"])
    frame = indicator_load.read_frames(tmp_path)["soil_properties"].assign(value_text="")
    with pytest.raises(SCHEMA_ERRORS):
        SOIL_PROPERTIES.validate(frame)
