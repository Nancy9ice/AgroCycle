"""The batch step that prepares weather and soil for a drawn boundary. Its load writes to shared tables, so the
guards are what matter: it must only ever append rows for one drawn field."""
import json

import pandas as pd
import pytest

from transform.indicators import drawn

SQUARE = {
    "type": "Polygon",
    "coordinates": [[[-93.5, 42.0], [-93.49, 42.0], [-93.49, 42.01], [-93.5, 42.01], [-93.5, 42.0]]],
}


class FakeClient:
    """Records every statement, answers the few queries the loader makes."""

    def __init__(self, existing=0, lineage=("gdd", "om_r_0_30cm", "precipitation_total")):
        self.existing, self.lineage = existing, lineage
        self.commands, self.queries, self.inserted = [], [], []

    def query(self, sql, parameters=None):
        self.queries.append((sql, parameters))
        rows = [(n,) for n in self.lineage] if "indicator_lineage" in sql else [(self.existing,)]
        return type("R", (), {"result_rows": rows})()

    def command(self, sql, parameters=None):
        self.commands.append((sql, parameters))

    def insert_df(self, table, frame):
        self.inserted.append((table, frame))


def write_csvs(folder, field_id="drawn-ab12cd34", extra_field=None):
    folder.mkdir(parents=True, exist_ok=True)
    indicators = [
        {"field_id": field_id, "indicator_id": "gdd", "category": "climate", "value": "2100.5", "unit": "degree-days C",
         "status": "available", "window_start": "2024-04-01", "window_end": "2024-11-30", "valid_obs": "244",
         "unknown_reason": "", "run_id": "r1"},
        {"field_id": field_id, "indicator_id": "om_r_0_30cm", "category": "soil", "value": "4.1", "unit": "%",
         "status": "available", "window_start": "", "window_end": "", "valid_obs": "", "unknown_reason": "", "run_id": "r1"},
    ]
    if extra_field:
        indicators.append({**indicators[0], "field_id": extra_field})
    soil = [{"field_id": field_id, "mukey": "1", "mu_name": "Clarion loam", "share_pct": "34.2", "property": "map_unit_share",
             "value_num": "", "value_text": "", "unit": "%", "indicator_id": "om_r_0_30cm", "run_id": "r1"}]
    pd.DataFrame(indicators).to_csv(folder / "field_indicators.csv", index=False)
    pd.DataFrame(soil).to_csv(folder / "soil_properties.csv", index=False)


class TestBoundary:
    def test_centroid_and_wkt_of_a_polygon(self):
        lat, lon, wkt = drawn.centroid_and_wkt(SQUARE)
        assert (lat, lon) == (42.005, -93.495) and wkt.startswith("POLYGON")

    def test_only_a_single_polygon_is_accepted(self):
        with pytest.raises(drawn.EnrichError, match="one Polygon"):
            drawn.centroid_and_wkt({"type": "MultiPolygon", "coordinates": [SQUARE["coordinates"]]})


class TestFetch:
    def test_a_demonstration_field_id_is_refused_before_anything_is_fetched(self, tmp_path):
        def explode(*a, **k):
            raise AssertionError("must not fetch")

        with pytest.raises(drawn.EnrichError, match="not a drawn field id"):
            drawn.fetch_raw("primary-001", SQUARE, tmp_path, fetcher=explode, poster=explode)

    def test_an_unusable_power_response_stops_the_run_and_soil_is_never_asked(self, tmp_path):
        def poster(*a, **k):
            raise AssertionError("soil must not be asked after POWER failed")

        with pytest.raises(drawn.EnrichError, match="POWER did not return a usable series"):
            drawn.fetch_raw("drawn-ab12cd34", SQUARE, tmp_path, fetcher=lambda url: b"{}", poster=poster)


class TestAppendOnlyLoad:
    def test_it_appends_rows_for_the_one_field_with_a_load_id_and_real_types(self, tmp_path):
        write_csvs(tmp_path)
        client = FakeClient()
        assert drawn.append_rows(client, tmp_path, "drawn-ab12cd34") == {"field_indicators": 2, "soil_properties": 1}
        assert client.commands == []  # nothing deleted
        tables = {t: f for t, f in client.inserted}
        ind = tables["field_indicators"]
        assert set(ind["load_id"]) == {"drawn-r1"}
        assert ind["value"].tolist() == [2100.5, 4.1]  # numbers, not text
        assert ind["unknown_reason"].isna().all()       # blank is null, never the text "nan"
        assert ind["window_start"].iloc[1] is None      # a soil row has no window

    def test_it_never_loads_a_demonstration_field(self, tmp_path):
        write_csvs(tmp_path, field_id="primary-001")
        client = FakeClient()
        with pytest.raises(drawn.EnrichError, match="only drawn fields"):
            drawn.append_rows(client, tmp_path, "primary-001")
        assert client.inserted == [] and client.commands == []

    def test_it_refuses_a_file_that_holds_another_fields_rows(self, tmp_path):
        write_csvs(tmp_path, extra_field="test-001")
        client = FakeClient()
        with pytest.raises(drawn.EnrichError, match="refusing to load anything but"):
            drawn.append_rows(client, tmp_path, "drawn-ab12cd34")
        assert client.inserted == []

    def test_it_refuses_a_field_that_already_has_rows_unless_asked_to_redo_it(self, tmp_path):
        write_csvs(tmp_path)
        client = FakeClient(existing=98)
        with pytest.raises(drawn.EnrichError, match="already has rows"):
            drawn.append_rows(client, tmp_path, "drawn-ab12cd34")
        assert client.inserted == [] and client.commands == []

    def test_redoing_a_field_deletes_only_that_fields_rows(self, tmp_path):
        write_csvs(tmp_path)
        client = FakeClient(existing=98)
        drawn.append_rows(client, tmp_path, "drawn-ab12cd34", replace=True)
        assert len(client.commands) == 2
        for sql, params in client.commands:
            assert "DELETE WHERE field_id = {f:String}" in sql and params == {"f": "drawn-ab12cd34"}
        touched = {sql.split()[2] for sql, _ in client.commands}
        assert touched == {"field_indicators", "soil_properties"}  # never the lineage table

    def test_it_refuses_indicators_with_no_lineage_row_and_loads_nothing(self, tmp_path):
        write_csvs(tmp_path)
        client = FakeClient(lineage=("gdd",))  # om_r_0_30cm has no lineage
        with pytest.raises(drawn.EnrichError, match="no lineage row.*om_r_0_30cm"):
            drawn.append_rows(client, tmp_path, "drawn-ab12cd34")
        assert client.inserted == []

    def test_it_refuses_empty_output(self, tmp_path):
        write_csvs(tmp_path)
        pd.DataFrame(columns=["field_id"]).to_csv(tmp_path / "soil_properties.csv", index=False)
        with pytest.raises(drawn.EnrichError, match="no rows"):
            drawn.append_rows(FakeClient(), tmp_path, "drawn-ab12cd34")

    def test_the_standard_loader_is_never_imported(self):
        # It replaces the whole table (one partition each) and would wipe the demonstration fields.
        with open(drawn.__file__, encoding="utf-8") as handle:
            imports = [line for line in handle.read().splitlines() if line.startswith(("import ", "from "))]
        assert imports, "expected to find the module's imports"
        assert not any("common.load" in line or "indicators.load" in line or line.endswith(" load") for line in imports)


class TestPending:
    def test_it_lists_drawn_fields_without_indicators(self):
        client = FakeClient()
        client.query = lambda sql, parameters=None: type(
            "R", (), {"result_rows": [("drawn-aaaaaaaa", json.dumps(SQUARE))]}
        )()
        assert drawn.pending(client) == [("drawn-aaaaaaaa", SQUARE)]
