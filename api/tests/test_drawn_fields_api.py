import pytest
from fastapi.testclient import TestClient

from api.db.facts import DRAWN_PREFIX, FieldRecord
from api.main import create_app
from api.settings import Settings

STORY_SQUARE = {
    "type": "Polygon",
    "coordinates": [[[-93.5, 42.0], [-93.49, 42.0], [-93.49, 42.01], [-93.5, 42.01], [-93.5, 42.0]]],
}
OUTSIDE = {
    "type": "Polygon",
    "coordinates": [[[-90.0, 40.0], [-89.99, 40.0], [-89.99, 40.01], [-90.0, 40.01], [-90.0, 40.0]]],
}
ROTATION = ["corn", "soybeans"] * 5 + ["corn"]


class DrawnRepo:
    """The file repository plus an in-memory stand-in for the drawn_fields table."""

    def __init__(self, repository, recent=0):
        self._base, self.rows, self.recent = repository, {}, recent

    def __getattr__(self, name):
        return getattr(self._base, name)

    def save_drawn_field(self, field_id, name, county, area_ha, geometry):
        self.rows[field_id] = {
            "field_id": field_id, "name": name, "county": county, "area_ha": area_ha, "geometry": geometry,
            "crop_sequence": "", "field_class": "",
        }

    def get_drawn_field(self, field_id):
        return self.rows.get(field_id)

    def set_drawn_crop_history(self, field_id, crop_sequence, field_class):
        if field_id not in self.rows:
            return False
        self.rows[field_id].update(crop_sequence=crop_sequence, field_class=field_class)
        return True

    def count_recent_drawn_fields(self, hours):
        return self.recent

    def get_field(self, field_id):
        if field_id.startswith(DRAWN_PREFIX):
            row = self.rows.get(field_id)
            return row and FieldRecord(
                field_id, row["county"], "drawn", "drawn", row["field_class"] or None, row["crop_sequence"] or None
            )
        return self._base.get_field(field_id)


@pytest.fixture()
def repo(repository):
    return DrawnRepo(repository)


@pytest.fixture()
def api(repo):
    return TestClient(create_app(Settings(), repo))


def save(api, geometry=STORY_SQUARE, **extra):
    return api.post("/api/v1/fields/drawn", json={"geometry": geometry, **extra})


def test_a_valid_boundary_is_kept_and_the_farmer_can_carry_on(api, repo):
    body = save(api, name="North 80").json()
    assert body["valid"] and body["field_id"].startswith("drawn-") and body["field_id"] in repo.rows
    assert (body["can_continue"], body["can_compare"], body["is_preprocessed"]) == (True, False, False)
    assert body["name"] == "North 80" and body["county"] == "Story"
    assert {c["source_id"] for c in body["coverage"]} == {"cdl", "power", "ssurgo", "hls"}
    assert all(c["status"] == "not_assessed" for c in body["coverage"])


def test_an_invalid_boundary_is_not_kept(api, repo):
    body = save(api, OUTSIDE).json()
    assert body["valid"] is False and body["can_continue"] is False and repo.rows == {}
    assert body["errors"][0]["code"] == "outside_pilot_area"


def test_only_a_single_polygon_is_accepted(api, repo):
    multi = {"type": "MultiPolygon", "coordinates": [STORY_SQUARE["coordinates"]]}
    body = save(api, multi).json()
    assert body["valid"] is False and body["errors"][0]["code"] == "not_a_polygon" and repo.rows == {}


def test_saving_is_capped_per_hour(repository):
    api = TestClient(create_app(Settings(), DrawnRepo(repository, recent=300)))
    assert save(api).status_code == 429


def test_without_the_database_saving_says_so(client):
    assert save(client).status_code == 503  # file mode has nowhere to keep it


def test_the_detail_endpoint_serves_the_drawn_boundary_and_demo_fields(api):
    field_id = save(api).json()["field_id"]
    drawn = api.get(f"/api/v1/fields/{field_id}/detail").json()
    assert drawn["role"] == "drawn" and drawn["boundary_source"] == "drawn" and drawn["geometry"] == STORY_SQUARE
    assert drawn["field_class"] is None and -94 < drawn["centroid"][0] < -93
    assert api.get("/api/v1/fields/primary-001/detail").json()["role"] == "primary"
    assert api.get("/api/v1/fields/drawn-nothere/detail").status_code == 404


def test_the_profile_shows_everything_as_not_loaded_until_the_farmer_answers(api):
    field_id = save(api).json()["field_id"]
    profile = api.get(f"/api/v1/fields/{field_id}/profile").json()
    assert {profile[s]["status"] for s in ("cropHistory", "climate", "soil", "vegetation")} == {"not_loaded"}


def test_the_farmers_crop_history_is_classified_and_labelled_as_their_input(api):
    field_id = save(api).json()["field_id"]
    answer = api.post(f"/api/v1/fields/{field_id}/crop-history", json={"crops": ROTATION})
    assert answer.status_code == 200
    body = answer.json()
    assert body["field_class"] == "rotation" and body["crop_sequence"] == "CSCSCSCSCSC"
    assert "not as data" in body["evidence_note"]

    profile = api.get(f"/api/v1/fields/{field_id}/profile").json()
    section = profile["cropHistory"]
    assert section["status"] == "available" and len(section["data"]["years"]) == 11
    assert section["provenance"]["source"] == "Your own answers"
    assert section["provenance"]["technical"]["evidenceType"] == "assumption"  # never "classified" (CDL)
    assert profile["versions"]["cropHistorySource"] == "Your own answers"
    assert profile["climate"]["status"] == profile["soil"]["status"] == "not_loaded"


def test_the_comparison_never_says_worth_exploring_without_weather_and_soil(api):
    field_id = save(api).json()["field_id"]
    before = api.post(f"/api/v1/fields/{field_id}/compare", json={}).json()["decision"]
    assert before["outcome"] == "abstention"

    api.post(f"/api/v1/fields/{field_id}/crop-history", json={"crops": ROTATION})
    after = api.post(f"/api/v1/fields/{field_id}/compare", json={
        "manure_access": True, "forage_use_or_buyer": True, "oat_use_or_buyer": True,
        "small_grain_equipment_or_contractor": True,
    }).json()
    assert after["decision"]["outcome"] == "abstention"
    assert after["field"]["role"] == "drawn"
    rules = {f["rule_id"] for o in after["decision"]["outcomes"] for f in o["findings"]}
    assert "applicability_indicator_coverage" in rules  # abstains because the indicators are missing...
    assert "applicability_crop_history_unknown" not in rules  # ...not because of the crop history


def test_crop_history_is_refused_for_demo_fields_wrong_lengths_and_unknown_crops(api):
    field_id = save(api).json()["field_id"]
    assert api.post("/api/v1/fields/primary-001/crop-history", json={"crops": ROTATION}).status_code == 422
    assert api.post(f"/api/v1/fields/{field_id}/crop-history", json={"crops": ["corn"] * 10}).status_code == 422
    assert api.post(f"/api/v1/fields/{field_id}/crop-history", json={"crops": ["wheat"] * 11}).status_code == 422
    assert api.post("/api/v1/fields/drawn-missing/crop-history", json={"crops": ROTATION}).status_code == 404


def test_a_drawn_fields_soil_measures_show_even_without_a_soil_type_read_at_a_centre_point():
    from api.core.profile_view import _soil
    from api.db.facts import IndicatorFacts, SoilMeasure

    record = FieldRecord("drawn-ab12cd34", "Story", "drawn", "drawn", None, None)  # no soil series or map unit
    measures = IndicatorFacts(soil={"om_r_0_30cm": SoilMeasure("om_r_0_30cm", 4.1, "%")})
    section = _soil(record, measures)
    assert section.status == "available"
    assert section.data.series == "Several soil types"
    assert "No single soil type is named" in section.data.map_unit
    assert "averaged by area" in section.data.sampling_note
    # With no measures at all there is still nothing to show, and it is not made up.
    assert _soil(record, IndicatorFacts()).status == "not_loaded"
