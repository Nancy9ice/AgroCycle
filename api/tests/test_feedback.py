import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from api.settings import Settings

VALID = {"role": "farmer", "usefulness": 4, "clarity": 5}


class FeedbackRepo:
    """The file repository plus an in-memory stand-in for the feedback table."""

    def __init__(self, repository, recent=0):
        self._base, self.rows, self.recent = repository, [], recent

    def __getattr__(self, name):
        return getattr(self._base, name)

    def save_feedback(self, row):
        self.rows.append(row)

    def count_recent_feedback(self, hours):
        return self.recent


@pytest.fixture()
def repo(repository):
    return FeedbackRepo(repository)


@pytest.fixture()
def api(repo):
    return TestClient(create_app(Settings(), repo))


def post(api, **body):
    return api.post("/api/v1/feedback", json={**VALID, **body})


def test_minimal_feedback_is_saved_and_says_what_it_can_and_cannot_speak_to(api, repo):
    response = post(api)
    assert response.status_code == 200
    body = response.json()
    assert body["feedback_id"].startswith("fb_") and "saved" in body["message"]
    assert "not whether its Iowa agronomy is right" in body["iowa_note"]
    (row,) = repo.rows
    assert (row["role"], row["usefulness"], row["clarity"]) == ("farmer", 4, 5)
    # Skipped optional answers are stored as empty, which means "not provided", never "no".
    assert row["would_use"] == "" and row["what_was_missing"] == "" and row["contact"] == ""


def test_the_whole_form_is_kept_including_where_it_came_from(api, repo):
    post(
        api, farming_context="Nigerian farmer, usability review", what_was_missing="A clearer map",
        would_use="maybe", field_id="primary-001", analysis_id="a_123abc",
    )
    row = repo.rows[0]
    assert row["farming_context"] == "Nigerian farmer, usability review"
    assert (row["would_use"], row["field_id"], row["analysis_id"]) == ("maybe", "primary-001", "a_123abc")


def test_contact_details_are_kept_only_with_consent(api, repo):
    assert post(api, contact="me@example.com").status_code == 422  # no consent: refused, not silently dropped
    assert repo.rows == []
    post(api, contact="me@example.com", contact_consent=True)
    assert repo.rows[0]["contact"] == "me@example.com" and repo.rows[0]["contact_consent"] == 1


def test_consent_without_contact_stores_nothing_to_consent_to(api, repo):
    post(api, contact_consent=True)
    assert repo.rows[0]["contact"] == "" and repo.rows[0]["contact_consent"] == 0


@pytest.mark.parametrize(
    "bad",
    [
        {"usefulness": 0}, {"usefulness": 6}, {"clarity": 0}, {"role": "robot"}, {"would_use": "definitely"},
        {"what_was_missing": "x" * 1001}, {"farming_context": "x" * 121}, {"unknown_field": 1},
        {"usefulness": "4"},
    ],
)
def test_invalid_feedback_is_refused_and_not_saved(api, repo, bad):
    assert post(api, **bad).status_code in (422,)
    assert repo.rows == []


def test_the_ratings_and_role_are_required(api):
    assert api.post("/api/v1/feedback", json={"role": "farmer"}).status_code == 422


def test_feedback_is_capped_per_hour(repository):
    api = TestClient(create_app(Settings(), FeedbackRepo(repository, recent=200)))
    assert post(api).status_code == 429


def test_without_the_database_it_says_so(client):
    assert post(client).status_code == 503


def test_text_is_trimmed(api, repo):
    post(api, what_was_missing="  more soil detail  ")
    assert repo.rows[0]["what_was_missing"] == "more soil detail"


def test_a_validation_error_is_a_clean_422_that_never_echoes_what_was_submitted(api, repo):
    response = post(api, contact="me@example.com")  # contact without consent
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["details"]["errors"][0]["msg"] == "Tick the consent box if you want us to keep your contact details."
    assert "me@example.com" not in response.text  # personal data is not sent back


def test_the_log_of_a_validation_error_leaves_out_the_values(api, caplog):
    import logging

    with caplog.at_level(logging.WARNING, logger="agrocycle"):
        post(api, contact="me@example.com")
    assert "me@example.com" not in caplog.text
