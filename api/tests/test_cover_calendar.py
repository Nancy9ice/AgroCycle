from datetime import date

from fastapi.testclient import TestClient

from api.core.cover_calendar import build_cover_calendar
from api.main import create_app
from api.settings import Settings


def images(year, month, count, share=0.9, ndvi=0.6):
    return [
        {"acquired": date(year, month, 3 + i * 6), "ndvi_mean": ndvi, "valid_share": share} for i in range(count)
    ]


def window(start, end, days, confidence="high"):
    return {"start": start, "end": end, "bare_days": days, "confidence": confidence}


def state(out, year, month):
    return next(m for y in out.years if y.year == year for m in y.months if m.month == month)


def test_a_field_with_no_images_has_no_calendar():
    assert build_cover_calendar("f", [], [], "dv") is None


def test_green_bare_likely_bare_and_unknown_are_told_apart():
    ndvi = (
        images(2024, 5, 3)            # green: images, no window
        + images(2024, 6, 3, ndvi=0.1)  # bare: images, inside a window
        + images(2024, 7, 1)          # one image: too few to say
    )
    windows = [window(date(2024, 6, 1), date(2024, 6, 30), 30), window(date(2024, 9, 1), date(2024, 9, 30), 30)]
    out = build_cover_calendar("f", ndvi, windows, "dv")
    assert state(out, 2024, 5).state == "green"
    assert state(out, 2024, 6).state == "bare"
    assert state(out, 2024, 7).state == "unknown"       # one image is not enough, and it is never guessed
    assert state(out, 2024, 9).state == "likely_bare"   # inside a window but no image that month: inferred
    assert state(out, 2024, 1).state == "unknown"       # no imagery in winter


def test_a_month_needs_half_its_days_in_a_window_to_be_bare():
    ndvi = images(2024, 6, 3)
    out = build_cover_calendar("f", ndvi, [window(date(2024, 6, 1), date(2024, 6, 10), 10)], "dv")
    assert state(out, 2024, 6).state == "green"  # 10 of 30 days
    out = build_cover_calendar("f", ndvi, [window(date(2024, 6, 1), date(2024, 6, 15), 15)], "dv")
    assert state(out, 2024, 6).state == "bare"   # exactly half


def test_cloudy_images_do_not_count():
    cloudy = images(2024, 6, 4, share=0.2)  # under half the field clear
    out = build_cover_calendar("f", cloudy + images(2024, 7, 3), [], "dv")
    assert state(out, 2024, 6).state == "unknown" and state(out, 2024, 6).usable_images == 0
    assert state(out, 2024, 7).state == "green"


def test_an_image_with_no_ndvi_does_not_count():
    broken = [{"acquired": date(2024, 6, 3), "ndvi_mean": None, "valid_share": 0.9}] * 3
    assert state(build_cover_calendar("f", broken + images(2024, 7, 3), [], "dv"), 2024, 6).state == "unknown"


def test_a_winter_window_across_the_new_year_marks_months_without_images_as_likely_bare():
    ndvi = images(2024, 10, 3) + images(2025, 4, 3)
    out = build_cover_calendar("f", ndvi, [window(date(2024, 10, 27), date(2025, 4, 23), 178)], "dv")
    assert state(out, 2025, 1).state == "likely_bare" and state(out, 2025, 2).state == "likely_bare"
    assert state(out, 2024, 10).state == "green"  # only 5 of its 31 days are in the window
    (w,) = out.bare_windows
    assert w.seen_in_images is False  # it crosses months with no usable image, so it is partly inferred


def test_a_window_backed_by_images_in_every_month_it_crosses_is_marked_seen():
    ndvi = images(2024, 5, 3) + images(2024, 6, 3)
    out = build_cover_calendar("f", ndvi, [window(date(2024, 5, 10), date(2024, 6, 20), 41)], "dv")
    assert out.bare_windows[0].seen_in_images is True


def test_the_summary_counts_bare_months_and_months_with_images_per_year():
    ndvi = images(2024, 5, 3) + images(2024, 6, 3) + images(2024, 7, 3)
    out = build_cover_calendar("f", ndvi, [window(date(2024, 6, 1), date(2024, 6, 30), 30)], "dv")
    (year,) = out.years
    assert (year.year, year.bare_months, year.months_with_images) == (2024, 1, 3)


def test_only_years_with_images_get_a_row_and_the_caveats_do_not_overclaim():
    out = build_cover_calendar("f", images(2023, 6, 3) + images(2025, 6, 3), [], "dv")
    assert [y.year for y in out.years] == [2023, 2025]
    text = " ".join(out.caveats)
    assert "nothing about which crop" in text and "not soil health" in text
    assert "no sourced timing" in text  # no expected cover for B and C is invented
    assert set(out.legend) == {"bare", "likely_bare", "green", "unknown"}


def _client(repository, rows):
    class Repo:
        def __getattr__(self, name):
            return getattr(repository, name)

        def get_cover_rows(self, field_id):
            return rows

    return TestClient(create_app(Settings(), Repo()))


def test_endpoint_serves_the_calendar_and_404s_without_images_or_an_unknown_field(repository):
    rows = {"ndvi": images(2024, 6, 3), "bare_windows": []}
    client = _client(repository, rows)
    body = client.get("/api/v1/fields/primary-001/cover-calendar").json()
    assert body["years"][0]["year"] == 2024 and body["evidence_type"] == "derived" and body["scale"] == "field"
    assert client.get("/api/v1/fields/nope/cover-calendar").status_code == 404
    empty = _client(repository, {"ndvi": [], "bare_windows": []})
    assert empty.get("/api/v1/fields/primary-001/cover-calendar").status_code == 404
