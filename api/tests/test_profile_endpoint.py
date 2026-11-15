import pytest
from fastapi.testclient import TestClient

from api.core.crop_summary import describe_sequence
from api.core.lineage import lineage_by_indicator
from api.db.repository import PROFILE_WEATHER_INDICATORS, FileRepository
from api.main import create_app
from api.settings import Settings

from .conftest import indicator_row, write_csv

F = "primary-001"


def season(indicator_id, year, value, status="available", unit="mm"):
    row = indicator_row(F, indicator_id, value, status)
    row.update(unit=unit, window_start=f"{year}-04-01", window_end=f"{year}-11-30")
    return row


@pytest.fixture()
def weather_client(tmp_path):
    rows = [
        season("precipitation_total", 2015, "600"),
        season("precipitation_total", 2016, "700"),
        season("precipitation_total", 2017, "100", status="partial"),  # must not enter the mean
        season("gdd", 2015, "1500", unit="degree-days C"),
        season("gdd", 2016, "1700", unit="degree-days C"),
        season("dry_spell_count", 2015, "2", unit="spells"),
        season("heat_days", 2015, "", status="unknown", unit="days"),  # nothing usable: omitted
        season("heat_days", 2016, "", status="unknown", unit="days"),
    ]
    write_csv(tmp_path / "field_indicators.csv", rows)
    repo = FileRepository(indicators_dir=tmp_path)
    return TestClient(create_app(Settings(), repo))


def profile(client, field_id=F):
    return client.get(f"/api/v1/fields/{field_id}/profile").json()


def test_unknown_field_is_404(client):
    assert client.get("/api/v1/fields/nope/profile").status_code == 404


def test_all_45_fields_return_a_valid_profile_with_no_sample_data(client):
    for field in client.get("/api/v1/fields").json():
        body = profile(client, field["field_id"])
        statuses = {body[s]["status"] for s in ("cropHistory", "climate", "vegetation", "soil")}
        assert statuses <= {"available", "not_loaded"}
        assert body["vegetation"] == {"status": "not_loaded", "data": None, "provenance": None}
        assert body["cropHistory"]["status"] == "available"
        assert body["soil"]["status"] == "available"


def test_crop_history_has_eleven_years_the_summary_and_cdl_provenance(client):
    section = profile(client)["cropHistory"]
    years = section["data"]["years"]
    assert [y["year"] for y in years] == list(range(2015, 2026))
    assert "".join(y["code"] for y in years) == "SCSCSCSCSCS"
    assert section["data"]["summary"] == describe_sequence("SCSCSCSCSCS", 2015)
    assert section["data"]["repeatedYears"] == []
    assert section["provenance"]["technical"]["evidenceType"] == "classified"


def test_repeated_years_are_listed_for_a_field_that_repeats_a_crop(client):
    body = profile(client, "test-033")  # grass or pasture in every year
    assert body["cropHistory"]["data"]["repeatedYears"] == list(range(2016, 2026))
    # test-027 is mostly corn with one soybean year: the repeats skip the year after the change.
    mixed = profile(client, "test-027")["cropHistory"]["data"]["repeatedYears"]
    assert 2022 not in mixed and 2023 not in mixed and 2024 in mixed


def test_soil_comes_from_the_field_notes_with_survey_provenance(client):
    section = profile(client)["soil"]
    assert section["data"]["series"] == "Nicollet"
    assert "Nicollet loam" in section["data"]["mapUnit"]
    assert "Organic matter" in section["data"]["notLoaded"]
    assert section["provenance"]["technical"]["evidenceType"] == "survey"


def test_weather_is_not_loaded_when_there_are_no_indicator_outputs(client):
    climate = profile(client)["climate"]
    assert climate == {"status": "not_loaded", "data": None, "provenance": None}


def test_weather_is_the_mean_of_available_seasons_only(weather_client):
    climate = profile(weather_client)["climate"]
    assert climate["status"] == "available"
    cards = {c["id"]: c for c in climate["data"]["indicators"]}
    assert cards["gs-rain"]["value"] == "650 mm"  # (600 + 700) / 2; the partial 100 is left out
    assert "2 of 3 seasons" in cards["gs-rain"]["context"]
    assert cards["gdd"]["value"] == "1,600"
    assert cards["dry-spells"]["value"] == "2.0 a season"
    assert "1 of 3 seasons were left out" in cards["gs-rain"]["provenance"]["gaps"]


def test_an_indicator_with_no_available_season_is_omitted_not_shown_as_zero(weather_client):
    ids = {c["id"] for c in profile(weather_client)["climate"]["data"]["indicators"]}
    assert "hot-days" not in ids


def test_the_period_and_window_are_read_from_the_data(weather_client):
    climate = profile(weather_client)["climate"]["data"]
    assert climate["periodLabel"] == "Averages over the seasons 2015 to 2016"
    rain = next(c for c in climate["indicators"] if c["id"] == "gs-rain")
    assert rain["label"] == "Rain from April to November"


def test_weather_provenance_comes_from_ds2s_lineage(weather_client):
    rain = next(
        c for c in profile(weather_client)["climate"]["data"]["indicators"] if c["id"] == "gs-rain"
    )
    lineage = lineage_by_indicator()["precipitation_total"]
    technical = rain["provenance"]["technical"]
    assert technical["indicatorId"] == "precipitation_total"
    assert technical["evidenceType"] == lineage["evidence_type"] == "model_reanalysis"
    assert rain["provenance"]["source"] == lineage["source"]
    assert lineage["limitation"] in rain["provenance"]["precision"]
    assert "50 km" in rain["provenance"]["precision"]


def test_plain_text_uses_the_thresholds_the_code_uses(weather_client, tmp_path):
    from api.core.lineage import thresholds

    rows = [season("heat_days", 2015, "9", unit="days")]
    write_csv(tmp_path / "field_indicators.csv", rows)
    client = TestClient(create_app(Settings(), FileRepository(indicators_dir=tmp_path)))
    card = profile(client)["climate"]["data"]["indicators"][0]
    assert f"{thresholds()['heat_day_c']:g} °C" in card["label"]


def test_every_indicator_the_profile_shows_is_documented_in_the_lineage():
    assert set(PROFILE_WEATHER_INDICATORS) <= set(lineage_by_indicator())


def test_the_profile_has_no_score_rank_or_winner(weather_client):
    def keys(value):
        if isinstance(value, dict):
            for key, item in value.items():
                yield key
                yield from keys(item)
        elif isinstance(value, list):
            for item in value:
                yield from keys(item)

    names = {k.lower() for k in keys(profile(weather_client))}
    for banned in ("score", "rank", "winner", "best", "recommendation"):
        assert not [n for n in names if banned in n]


def soil_season(indicator_id, value, status="available", unit="% by weight", reason=""):
    row = indicator_row(F, indicator_id, value, status)
    row.update(unit=unit, window_start="", window_end="", unknown_reason=reason)
    return row


@pytest.fixture()
def soil_client(tmp_path):
    from .conftest import soil_row

    write_csv(
        tmp_path / "field_indicators.csv",
        [
            soil_season("om_r_0_30cm", "5.33"),
            soil_season("claytotal_r_0_30cm", "27.0"),
            soil_season("silttotal_r_0_30cm", "41.3"),
            soil_season(
                "sandtotal_r_0_30cm",
                "31.7",
                status="partial",
                reason="computed over 96.72% of the field's mapped area, depth 96.72%",
            ),
            soil_season("ph1to1h2o_r_0_30cm", "6.81", unit="pH"),
            soil_season("available_water_storage_0_100cm", "18.55", unit="cm"),
        ],
    )
    write_csv(
        tmp_path / "soil_properties.csv",
        [
            soil_row(F, "drainagecl", "Poorly drained", "47.1"),
            soil_row(F, "drainagecl", "Somewhat poorly drained", "25.9"),
            soil_row(F, "drainagecl", "Well drained", "21.6"),
            soil_row(F, "drainagecl", "Very poorly drained", "4.4"),
            soil_row(F, "drainagecl", "Moderately well drained", "1.0"),
        ],
    )
    return TestClient(create_app(Settings(), FileRepository(indicators_dir=tmp_path)))


def test_without_indicator_outputs_soil_has_no_measures_and_still_says_what_is_not_loaded(client):
    section = profile(client)["soil"]
    assert section["data"]["measures"] == []
    assert section["data"]["notLoaded"] == ["How well it drains", "Organic matter", "Soil texture"]
    assert "not loaded yet" in section["provenance"]["gaps"]


def test_soil_measures_are_real_values_with_plain_notes(soil_client):
    soil = profile(soil_client)["soil"]["data"]
    by_label = {m["label"]: m for m in soil["measures"]}
    assert by_label["Organic matter, top 30 cm"]["value"] == "5.3 %"
    assert by_label["Acidity, top 30 cm"]["value"] == "pH 6.8"
    assert by_label["Water the soil can store for plants, top 100 cm"]["value"] == "18.6 cm"
    assert soil["notLoaded"] == []  # everything the screen lists is now present


def test_a_partial_soil_value_is_shown_with_what_it_covers(soil_client):
    texture = next(
        m for m in profile(soil_client)["soil"]["data"]["measures"] if m["label"].startswith("Texture")
    )
    assert texture["value"] == "clay 27 %, silt 41 %, sand 32 %"
    assert "96.72%" in texture["note"] and "Partial" in texture["note"]
    assert "may not add up to exactly 100 %" in texture["note"]


def test_drainage_shows_the_mix_not_just_the_biggest_class(soil_client):
    drainage = next(
        m for m in profile(soil_client)["soil"]["data"]["measures"] if m["label"] == "Drainage"
    )
    assert drainage["value"] == (
        "Poorly drained 47 %, somewhat poorly drained 26 %, well drained 22 %, other 5 %"
    )
    assert "does not record drainage tiles" in drainage["note"]


def test_soil_provenance_describes_area_weighting_once_there_are_measures(soil_client):
    provenance = profile(soil_client)["soil"]["provenance"]
    assert "averages over the mapped soil units" in provenance["precision"]
    assert provenance["technical"]["evidenceType"] == "survey"


def test_an_unknown_soil_value_stays_on_the_not_loaded_list(tmp_path):
    write_csv(tmp_path / "field_indicators.csv", [soil_season("om_r_0_30cm", "", status="unknown")])
    client = TestClient(create_app(Settings(), FileRepository(indicators_dir=tmp_path)))
    assert "Organic matter" in profile(client)["soil"]["data"]["notLoaded"]
