import hashlib
import struct
from datetime import date

import numpy as np
import pytest
from fastapi.testclient import TestClient

from api.core.imagery import ChipRecord, ImageryError, encode_png, render_chip
from api.db.imagery import CHIP_PREFIX, ClickHouseS3Imagery, NoImagery
from api.main import create_app
from api.settings import Settings

rasterio = pytest.importorskip("rasterio")
from rasterio.io import MemoryFile
from rasterio.transform import from_origin


def make_chip(width=40, height=30, count=4, dtype="uint8", crs="EPSG:26915", nodata_corner=True) -> bytes:
    """A small synthetic NAIP-like chip in UTM 15N near Ames, Iowa: red on the left half, green on the right."""
    data = np.zeros((count, height, width), dtype=dtype)
    data[0, :, : width // 2] = 200
    if count > 1:
        data[1, :, width // 2 :] = 200
    if count > 3:
        data[3] = 90
    mask_alpha = np.full((height, width), 255, dtype="uint8")
    if nodata_corner:
        mask_alpha[:3, :3] = 0
    profile = {
        "driver": "GTiff", "width": width, "height": height, "count": count, "dtype": dtype, "crs": crs,
        "transform": from_origin(447000, 4650000, 0.6, 0.6),
    }
    with MemoryFile() as memory:
        with memory.open(**profile) as dst:
            dst.write(data)
            if nodata_corner:
                dst.write_mask(mask_alpha)
        return memory.read()


def record(field_id="primary-001", key=CHIP_PREFIX + "naip-2025/x/primary-001.tif", sha="0" * 64, tile="t1"):
    return ChipRecord(
        field_id=field_id, year=2025, tile_id=tile, flight_date=date(2025, 8, 5), resolution_m=0.6,
        bbox=(-93.65, 42.0, -93.64, 42.01), buffer_m=50.0, bands="Red,Green,Blue,NIR", s3_key=key,
        size_bytes=1, sha256=sha, evidence_type="observed", source_id="naip_2025",
    )


def png_size(png: bytes) -> tuple[int, int]:
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", png[16:24])


class TestRender:
    def test_warps_to_longitude_latitude_near_the_site(self):
        out = render_chip(make_chip())
        west, south, east, north = out.bounds
        assert -94.0 < west < east < -93.0 and 41.0 < south < north < 43.0  # Story County, Iowa
        assert png_size(out.png) == (out.width, out.height)

    def test_keeps_colours_and_leaves_empty_corners_transparent(self):
        out = render_chip(make_chip())
        with MemoryFile(out.png) as memory, memory.open() as image:
            rgba = image.read()
        h, w = rgba.shape[1:]
        left, right = rgba[:, h // 2, w // 4], rgba[:, h // 2, 3 * w // 4]
        assert left[0] > 150 and left[1] < 60  # red half stays red
        assert right[1] > 150 and right[0] < 60  # green half stays green
        assert left[3] == 255
        assert rgba[3, 0, 0] == 0  # nothing flown there, so nothing drawn

    def test_a_large_chip_is_shrunk_to_the_limit(self):
        out = render_chip(make_chip(width=400, height=300), max_pixels=100)
        assert max(out.width, out.height) <= 105

    def test_refuses_a_chip_without_colour_bands(self):
        with pytest.raises(ImageryError, match="bands"):
            render_chip(make_chip(count=1))

    def test_refuses_sixteen_bit_data_instead_of_rescaling_it(self):
        with pytest.raises(ImageryError, match="8-bit"):
            render_chip(make_chip(dtype="uint16", nodata_corner=False))

    def test_refuses_bytes_that_are_not_a_geotiff(self):
        with pytest.raises(ImageryError, match="readable"):
            render_chip(b"not a tiff")


def test_encode_png_rejects_the_wrong_channel_count():
    with pytest.raises(ImageryError):
        encode_png(np.zeros((2, 2, 3), dtype="uint8"))


class FakeResult:
    def __init__(self, rows):
        self.result_rows = rows


class FakeClickHouse:
    def __init__(self, rows):
        self.rows, self.calls = rows, []

    def query(self, sql, parameters=None):
        self.calls.append((sql, parameters))
        return FakeResult(self.rows)


class FakeS3:
    def __init__(self, objects):
        self.objects, self.reads = objects, []

    def get_object(self, Bucket, Key):
        self.reads.append(Key)
        if Key not in self.objects:
            raise KeyError(Key)

        class Body:
            def read(inner):
                return self.objects[Key]
        return {"Body": Body()}


def row(rec: ChipRecord, sha=None):
    return (rec.field_id, rec.year, rec.tile_id, rec.flight_date, rec.resolution_m, *rec.bbox, rec.buffer_m,
            rec.bands, rec.s3_key, rec.size_bytes, sha or rec.sha256, rec.evidence_type, rec.source_id)


class TestClickHouseS3Imagery:
    def source(self, chip: bytes, claimed_sha=None, key=CHIP_PREFIX + "naip-2025/x/primary-001.tif"):
        good = hashlib.sha256(chip).hexdigest()
        rec = record(key=key, sha=claimed_sha or good)
        return ClickHouseS3Imagery(FakeClickHouse([row(rec)]), FakeS3({key: chip}), "bucket"), rec

    def test_reads_the_index_with_a_parameter_not_string_building(self):
        source, _ = self.source(make_chip())
        got = source.records("primary-001")
        assert got[0].flight_date == date(2025, 8, 5)
        assert source._client.calls[0][1] == {"field_id": "primary-001"}

    def test_returns_a_chip_whose_checksum_matches(self):
        chip = make_chip()
        source, rec = self.source(chip)
        assert source.chip(rec) == chip

    def test_refuses_a_chip_that_does_not_match_its_checksum(self):
        source, rec = self.source(make_chip(), claimed_sha="f" * 64)
        with pytest.raises(ImageryError, match="checksum"):
            source.chip(rec)

    def test_never_reads_outside_the_naip_folder(self):
        source, rec = self.source(make_chip(), key="raw/other/secret.tif")
        with pytest.raises(ImageryError, match="refusing"):
            source.chip(rec)
        assert source._s3.reads == []

    def test_a_missing_object_is_an_imagery_error(self):
        source, rec = self.source(make_chip())
        source._s3.objects.clear()
        with pytest.raises(ImageryError, match="S3"):
            source.chip(rec)

    def test_accepts_a_checksum_returned_as_padded_bytes(self):
        chip = make_chip()
        sha = hashlib.sha256(chip).hexdigest()
        rec = record(sha=sha)
        source = ClickHouseS3Imagery(FakeClickHouse([row(rec, sha=sha.encode())]), FakeS3({rec.s3_key: chip}), "b")
        assert source.records("primary-001")[0].sha256 == sha


class OneChip:
    def __init__(self, chip: bytes, tiles=1):
        self.chip_bytes, self.tiles = chip, tiles

    def records(self, field_id):
        return [record(field_id=field_id, tile=f"t{i}") for i in range(self.tiles)] if field_id == "primary-001" else []

    def chip(self, rec):
        return self.chip_bytes


@pytest.fixture()
def api(repository):
    def make(imagery):
        return TestClient(create_app(Settings(), repository, imagery))
    return make


class TestRoutes:
    def test_metadata_for_a_field_with_a_photo(self, api):
        body = api(OneChip(make_chip(), tiles=2)).get("/api/v1/fields/primary-001/imagery").json()
        assert body["available"] is True and body["year"] == 2025
        assert [t["flight_date"] for t in body["tiles"]] == ["2025-08-05", "2025-08-05"]
        assert len(body["bounds"]) == 4 and body["evidence_type"] == "observed"
        assert "not a crop map" in body["note"] and "NAIP" in body["attribution"]

    def test_image_is_a_png(self, api):
        response = api(OneChip(make_chip())).get("/api/v1/fields/primary-001/imagery/image.png")
        assert response.status_code == 200 and response.headers["content-type"] == "image/png"
        png_size(response.content)

    def test_a_field_without_a_photo_says_so_and_has_no_image(self, api):
        client = api(OneChip(make_chip()))
        assert client.get("/api/v1/fields/test-001/imagery").json() == {
            "field_id": "test-001", "available": False, "year": None, "tiles": [], "resolution_m": None,
            "bounds": None, "evidence_type": None, "attribution": None, "note": None,
        }
        assert client.get("/api/v1/fields/test-001/imagery/image.png").status_code == 404

    def test_unknown_field_is_not_found(self, api):
        assert api(OneChip(make_chip())).get("/api/v1/fields/nope/imagery").status_code == 404

    def test_no_imagery_configured_means_no_photos_never_a_made_up_one(self, api):
        client = api(NoImagery())
        assert client.get("/api/v1/fields/primary-001/imagery").json()["available"] is False
        assert client.get("/api/v1/fields/primary-001/imagery/image.png").status_code == 404

    def test_a_bad_chip_is_a_visible_error_not_a_blank_picture(self, api):
        response = api(OneChip(b"garbage")).get("/api/v1/fields/primary-001/imagery")
        assert response.status_code == 503 and "readable" in response.json()["error"]["message"]

    def test_the_same_routes_exist_under_api_v1(self, api):
        assert api(OneChip(make_chip())).get("/api/v1/fields/primary-001/imagery").status_code == 200


class CountingChip(OneChip):
    def __init__(self, chip: bytes):
        super().__init__(chip)
        self.fetches = 0

    def chip(self, rec):
        self.fetches += 1
        return self.chip_bytes


class TestRenderIsCached:
    def test_a_chip_is_fetched_and_rendered_once_across_both_endpoints_and_repeat_visits(self, api):
        source = CountingChip(make_chip())
        client = api(source)
        for _ in range(3):
            assert client.get("/api/v1/fields/primary-001/imagery").status_code == 200
            assert client.get("/api/v1/fields/primary-001/imagery/image.png").status_code == 200
        assert source.fetches == 1  # was 6: one S3 download per call

    def test_a_failure_is_not_remembered(self, api):
        source = OneChip(b"garbage")
        client = api(source)
        assert client.get("/api/v1/fields/primary-001/imagery").status_code == 503
        source.chip_bytes = make_chip()
        assert client.get("/api/v1/fields/primary-001/imagery").status_code == 200

    def test_simultaneous_first_requests_share_one_fetch(self):
        import threading
        import time

        from api.core.imagery import RenderCache

        calls, cache = [], RenderCache()

        def slow():
            calls.append(1)
            time.sleep(0.2)
            return "rendered"

        results = []
        threads = [
            threading.Thread(target=lambda: results.append(cache.get(record(), slow))) for _ in range(8)
        ]
        [t.start() for t in threads]
        [t.join() for t in threads]
        assert results == ["rendered"] * 8 and len(calls) == 1

    def test_a_replaced_chip_is_not_served_from_the_old_render(self):
        from dataclasses import replace

        from api.core.imagery import RenderCache

        cache = RenderCache()
        first = cache.get(record(), lambda: "old")
        second = cache.get(replace(record(), sha256="f" * 64), lambda: "new")
        assert (first, second) == ("old", "new")


def test_ttl_cache_runs_a_lookup_once_per_window_and_never_caches_a_failure():
    from api.db.cache import ttl_cached

    class Repo:
        calls = 0

        @ttl_cached(ttl=60)
        def lookup(self, key):
            Repo.calls += 1
            if key == "bad":
                raise RuntimeError("down")
            return [key]

    repo = Repo()
    assert repo.lookup("a") == repo.lookup("a") == ["a"] and Repo.calls == 1
    repo.lookup("b")
    assert Repo.calls == 2
    for _ in range(2):
        with pytest.raises(RuntimeError):
            repo.lookup("bad")
    assert Repo.calls == 4  # the failure ran both times
    assert Repo().lookup("a") == ["a"] and Repo.calls == 5  # a new instance does not share the cache
