from fastapi.testclient import TestClient

from api.core.season_summary import INDICATORS, build_season_summary
from api.main import create_app
from api.settings import Settings


def row(indicator_id, year, value, status="available", reason=""):
    return {
        "field_id": "f", "indicator_id": indicator_id, "value": str(value), "unit": "u", "status": status,
        "window_start": f"{year}-04-01", "window_end": f"{year}-10-31", "unknown_reason": reason,
    }


def rows():
    out = []
    for year, heat in ((2017, 54.0), (2015, 18.0), (2019, 9.0), (2021, 73.0), (2022, 73.0)):
        out.append(row("heat_days", year, heat))
    out += [row("gdd", 2015, 2500.0), row("precipitation_total", 2015, 600.0)]
    return out


def test_no_rows_says_so_and_invents_nothing():
    out = build_season_summary("f", [], "dv")
    assert out.indicators == [] and out.period == "not loaded"
    assert "No weather indicators have been loaded" in out.caveats[0]


def test_seasons_are_in_year_order_with_the_extremes_and_earliest_wins_a_tie():
    out = build_season_summary("f", rows(), "dv")
    heat = next(i for i in out.indicators if i.indicator_id == "heat_days")
    assert [s.year for s in heat.seasons] == [2015, 2017, 2019, 2021, 2022]
    assert (heat.highest.year, heat.highest.value) == (2021, 73.0)  # 2021 and 2022 tie; earliest
    assert (heat.lowest.year, heat.lowest.value) == (2019, 9.0)
    assert heat.seasons_used == heat.seasons_total == 5 and heat.scale == "grid"
    assert out.period == "2015-2022"


def test_indicators_come_in_a_fixed_order_and_carry_lineage():
    out = build_season_summary("f", rows(), "dv")
    ids = [i.indicator_id for i in out.indicators]
    assert ids == [i for i in INDICATORS if i in ids] == ["heat_days", "precipitation_total", "gdd"]
    heat = out.indicators[0]
    assert "30" in heat.label and heat.unit == "days"
    assert "team-proposed" in heat.limitation and heat.evidence_type == "model_reanalysis"


def test_an_unknown_season_is_never_read_as_zero_and_does_not_count_toward_the_extremes():
    data = [row("heat_days", 2015, 12.0), row("heat_days", 2016, "nan", status="unknown", reason="too few days")]
    heat = build_season_summary("f", data, "dv").indicators[0]
    unknown = next(s for s in heat.seasons if s.year == 2016)
    assert unknown.value is None and unknown.unknown_reason == "too few days"
    assert (heat.seasons_used, heat.seasons_total) == (1, 2)
    assert heat.lowest.year == heat.highest.year == 2015


def test_the_caveats_say_it_is_not_a_crop_phase_test_or_a_prediction():
    text = " ".join(build_season_summary("f", rows(), "dv").caveats)
    assert "not a prediction of yield or loss" in text
    assert "when in the season" in text and "No agronomist has reviewed" in text


def _client(repository, indicator_rows):
    class Repo:
        def __getattr__(self, name):
            return getattr(repository, name)

        def get_indicator_rows(self, field_id):
            return indicator_rows

    return TestClient(create_app(Settings(), Repo()))


def test_endpoint_serves_the_summary_and_404s_an_unknown_field(repository):
    client = _client(repository, rows())
    body = client.get("/api/v1/fields/primary-001/season-summary").json()
    assert body["field_id"] == "primary-001" and body["indicators"][0]["indicator_id"] == "heat_days"
    assert client.get("/api/v1/fields/nope/season-summary").status_code == 404


def test_endpoint_with_nothing_loaded_is_200_and_empty(client):
    body = client.get("/api/v1/fields/primary-001/season-summary").json()  # file mode, no indicator CSV
    assert body["indicators"] == [] and body["period"] == "not loaded"


THRESHOLDS = {
    "heat_days": {
        "what_it_counts": "Days the daily maximum temperature reached the threshold or more",
        "threshold": ">= 30", "unit": "degrees C", "evidence_basis": "team_proposed",
        "review": "not_expert_reviewed", "limitation": "The weather the field had across the whole season.",
        "code_version": "2026-11-15.5",
    },
    "precipitation_total": {
        "what_it_counts": "Total rainfall over the season", "threshold": "none: a total, not a count", "unit": "mm",
        "evidence_basis": "team_proposed", "review": "not_expert_reviewed", "limitation": "Not a rain gauge.",
        "code_version": "2026-11-15.5",
    },
}


def test_each_indicator_carries_ds2s_threshold_record_when_there_is_one():
    out = build_season_summary("f", rows(), "dv", THRESHOLDS)
    by_id = {i.indicator_id: i for i in out.indicators}
    heat = by_id["heat_days"].threshold
    assert (heat.threshold, heat.unit, heat.evidence_basis, heat.review) == (">= 30", "degrees C", "team_proposed", "not_expert_reviewed")
    assert by_id["precipitation_total"].threshold.threshold.startswith("none")
    assert by_id["gdd"].threshold is None  # DS2's table has no row for it here: nothing is invented


def test_without_the_thresholds_table_the_summary_still_works_and_says_nothing_about_them():
    out = build_season_summary("f", rows(), "dv")
    assert all(i.threshold is None for i in out.indicators)


def test_the_review_caveat_follows_ds2s_table_and_never_claims_a_review_that_did_not_happen():
    unreviewed = " ".join(build_season_summary("f", rows(), "dv", THRESHOLDS).caveats)
    assert "No agronomist has reviewed them" in unreviewed
    reviewed = {k: {**v, "review": "expert_reviewed"} for k, v in THRESHOLDS.items()}
    assert "An agronomist has reviewed them" in " ".join(build_season_summary("f", rows(), "dv", reviewed).caveats)
    assert "No agronomist" not in " ".join(build_season_summary("f", rows(), "dv", reviewed).caveats)
    # An empty table is not a review.
    assert "No agronomist has reviewed them" in " ".join(build_season_summary("f", rows(), "dv", {}).caveats)


def test_season_mean_temperature_and_reference_et_are_included_in_a_fixed_place():
    data = rows() + [row("reference_et_total", 2015, 650.0), row("mean_temperature", 2015, 14.2)]
    ids = [i.indicator_id for i in build_season_summary("f", data, "dv").indicators]
    assert ids == ["heat_days", "precipitation_total", "gdd", "mean_temperature", "reference_et_total"]
    labels = {i.indicator_id: i.label for i in build_season_summary("f", data, "dv").indicators}
    assert "not any crop's water use" in labels["reference_et_total"]  # said in the label, not only the footnote


def test_endpoint_serves_the_thresholds(repository):
    class Repo:
        def __getattr__(self, name):
            return getattr(repository, name)

        def get_indicator_rows(self, field_id):
            return rows()

        def get_season_thresholds(self):
            return THRESHOLDS

    body = TestClient(create_app(Settings(), Repo())).get("/api/v1/fields/primary-001/season-summary").json()
    assert body["indicators"][0]["threshold"]["threshold"] == ">= 30"
