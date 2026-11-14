"""HLS raw data: per-field windowed clips of the original bands and the raw Fmask.

Follows DS1's sheet (specs/features/2026-11-14-ds1-hls-cdl-requirements/): HLS L30 and S30
v2.0, April to October, per-field windows with a 500 m buffer, bands Red, NIR (B05 for L30,
B8A for S30), SWIR1 and Fmask. Values are stored exactly as in the source (unmasked, unscaled):
DS1 applies the mask in Phase 5. The first pull is `primary-001` for 2023.

Login: the Earthdata user name and password are read from the environment by this program and
held in memory only. They are never printed or written to a file.
"""

import json
import math
import os
import shutil
import sys
import tempfile
import urllib.request
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime
from http.cookiejar import CookieJar
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import Affine
from rasterio.warp import transform_bounds

import common.config  # noqa: F401  (loads the local settings file into the environment)
from ingest.checks import CheckResult
from ingest.items import Item
from ingest.manifest import build_manifest
from ingest.subset import check_budget, field_bboxes, subset_record
from transform.field_schema import FIELDS_PATH

SOURCE = "hls"
VERSION = "v2.0"
BUDGET_BYTES = 3_000_000_000
STAC_SEARCH = "https://cmr.earthdata.nasa.gov/stac/LPCLOUD/search"
COLLECTIONS = {"l30": "HLSL30.v2.0", "s30": "HLSS30.v2.0"}
BANDS = {"l30": ("B04", "B05", "B06", "Fmask"), "s30": ("B04", "B8A", "B11", "Fmask")}
BUFFER_M = 500.0
TILE_CRS = "EPSG:32615"
FIRST_FIELD, FIRST_YEAR = "primary-001", 2023
WORKERS = 6
LICENCE = "NASA Earthdata: free for public use with an Earthdata Login (as stated in DS1's sheet)"
FMASK_NOTE = (
    "Fmask bits (HLS v2.0 User Guide, Table 9): 0 cirrus (unused), 1 cloud, 2 adjacent to "
    "cloud/shadow, 3 cloud shadow, 4 snow/ice, 5 water, 6-7 aerosol level."
)


@dataclass(frozen=True)
class Scene:
    sensor: str
    granule: str
    tile: str
    acquired: datetime
    cloud_cover: float | None
    hrefs: dict[str, str]


def default_dir() -> Path:
    return Path.home() / "agrocycle_hls"


GDAL_OPTIONS = {
    "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
    "GDAL_HTTP_MAX_RETRY": "3",
    "GDAL_HTTP_RETRY_DELAY": "2",
}


@contextmanager
def earthdata_session() -> Iterator[Callable[[str], str]]:
    """Log in to Earthdata (NASA's documented flow) and yield a function that turns a data URL
    into the short-lived signed address the file is actually served from.

    The user name and password stay in memory; no cookie or password file is written.
    """
    user, password = os.environ.get("EARTHDATA_USERNAME"), os.environ.get("EARTHDATA_PASSWORD")
    if not user or not password:
        raise RuntimeError("EARTHDATA_USERNAME and EARTHDATA_PASSWORD are not set (see .env.example)")
    manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    manager.add_password(None, "https://urs.earthdata.nasa.gov", user, password)
    opener = urllib.request.build_opener(
        urllib.request.HTTPBasicAuthHandler(manager),
        urllib.request.HTTPCookieProcessor(CookieJar()),
    )

    def resolve(href: str) -> str:
        request = urllib.request.Request(href, headers={"Range": "bytes=0-0"})
        with opener.open(request, timeout=90) as resp:
            return resp.geturl()

    yield resolve


def search_scenes(sensor: str, bbox: tuple[float, float, float, float], year: int) -> list[Scene]:
    """All HLS scenes that touch the bbox between 1 April and 31 October."""
    start, end = date(year, 4, 1), date(year, 10, 31)
    url = (
        f"{STAC_SEARCH}?collections={COLLECTIONS[sensor]}&bbox={','.join(map(str, bbox))}"
        f"&datetime={start}T00:00:00Z/{end}T23:59:59Z&limit=200"
    )
    scenes = []
    while url:
        with urllib.request.urlopen(url, timeout=120) as resp:
            page = json.load(resp)
        for feature in page["features"]:
            props, granule = feature["properties"], feature["id"]
            when = datetime.fromisoformat(props["datetime"])
            scenes.append(Scene(
                sensor, granule, granule.split(".")[2], when, props.get("eo:cloud_cover"),
                {b: feature["assets"][b]["href"] for b in BANDS[sensor]},
            ))
        url = next((link["href"] for link in page.get("links", []) if link.get("rel") == "next"), None)
    return sorted(scenes, key=lambda s: s.acquired)


def clip_to_file(href: str, bbox: tuple[float, float, float, float], dest: Path, resolve) -> dict:
    """Read the window covering bbox (lon/lat) from a remote band and save it, values unchanged."""
    with rasterio.Env(**GDAL_OPTIONS), rasterio.open(resolve(href)) as src:
        left, bottom, right, top = transform_bounds("EPSG:4326", src.crs, *bbox)
        res = src.res[0]
        col0 = math.floor((left - src.transform.c) / res)
        row0 = math.floor((src.transform.f - top) / res)
        cols = math.ceil((right - src.transform.c) / res) - col0
        rows = math.ceil((src.transform.f - bottom) / res) - row0
        window = rasterio.windows.Window(col0, row0, cols, rows)
        data = src.read(1, window=window)
        profile = {
            "driver": "GTiff", "height": rows, "width": cols, "count": 1, "dtype": data.dtype,
            "crs": src.crs, "nodata": src.nodata, "compress": "deflate",
            "transform": Affine(res, 0, src.transform.c + col0 * res, 0, -res, src.transform.f - row0 * res),
        }
        tags = src.tags()
        dest.parent.mkdir(parents=True, exist_ok=True)
        part = dest.with_name(dest.name + ".part")
        with rasterio.open(part, "w", **profile) as out:
            out.write(data, 1)
            out.update_tags(**tags)
        part.rename(dest)
    return {"cols": cols, "rows": rows}


def local_path(base: Path, scene: Scene, field_id: str, band: str) -> Path:
    return base / scene.sensor / field_id / f"{scene.acquired:%Y%m%d}" / f"{band.lower()}.tif"


def pull(base: Path, field_id: str, bbox, year: int, searcher=search_scenes, clipper=clip_to_file):
    """Clip every needed band of every scene. Files already on disk are not read again."""
    scenes = [s for sensor in COLLECTIONS for s in searcher(sensor, bbox, year)]
    seen: dict[tuple, str] = {}
    for s in scenes:  # two granules on one day would collide on the DS1 key layout
        key = (s.sensor, s.tile, f"{s.acquired:%Y%m%d}")
        if key in seen:
            raise RuntimeError(f"two granules on one date: {seen[key]} and {s.granule}")
        seen[key] = s.granule
    jobs = [(s, b) for s in scenes for b in BANDS[s.sensor] if not local_path(base, s, field_id, b).exists()]
    failures = []
    with earthdata_session() as resolve, ThreadPoolExecutor(WORKERS) as pool:
        futures = {pool.submit(clipper, s.hrefs[b], bbox, local_path(base, s, field_id, b), resolve): (s, b)
                   for s, b in jobs}
        for future, (s, b) in futures.items():
            try:
                future.result()
            except (OSError, ValueError, rasterio.errors.RasterioError) as err:  # report all, stop on none
                failures.append(f"{s.granule} {b}: {type(err).__name__}: {str(err)[:120]}")
    if failures:
        raise RuntimeError(f"{len(failures)} of {len(jobs)} clips failed (rerun to retry):\n- " + "\n- ".join(failures[:10]))
    return scenes


def check_clip(path: Path, band: str, field_box, season: tuple[date, date], acquired: datetime) -> CheckResult:
    result = CheckResult()
    try:
        with rasterio.open(path) as src:
            data = src.read(1)
            if src.crs.to_string() != TILE_CRS:
                result.problems.append(f"{path.name}: CRS {src.crs.to_string()}, expected {TILE_CRS}")
            left, bottom, right, top = transform_bounds("EPSG:4326", src.crs, *field_box)
            if not (src.bounds.left <= left and src.bounds.bottom <= bottom
                    and src.bounds.right >= right and src.bounds.top >= top):
                result.problems.append(f"{path.name}: does not cover the field")
            expected = "uint8" if band == "Fmask" else "int16"
            if src.dtypes[0] != expected:
                result.problems.append(f"{path.name}: dtype {src.dtypes[0]}, expected {expected}")
            if src.nodata is not None and bool(np.all(data == src.nodata)):
                result.problems.append(f"{path.name}: every pixel is fill")
    except (OSError, rasterio.errors.RasterioError) as err:
        result.problems.append(f"{path.name}: cannot be opened ({err})")
    if not season[0] <= acquired.date() <= season[1]:
        result.problems.append(f"{path.name}: date {acquired.date()} outside April to October")
    return result


def plan_field(field_id: str, year: int, base: Path | None = None, searcher=search_scenes,
               clipper=clip_to_file) -> list[Item]:
    base = Path(base) if base else default_dir()
    fields = gpd.read_file(FIELDS_PATH)
    field = fields[fields.field_id == field_id]
    plain = field_bboxes(field)[field_id]
    window_box = field_bboxes(field, BUFFER_M)[field_id]
    scenes = pull(base, field_id, window_box, year, searcher, clipper)
    season = (date(year, 4, 1), date(year, 10, 31))
    items = []
    for s in scenes:
        for band in BANDS[s.sensor]:
            path = local_path(base, s, field_id, band)
            when = f"{s.acquired:%Y%m%d}"
            manifest = build_manifest(
                path,
                source_url=s.hrefs[band],
                product=f"NASA HLS {s.sensor.upper()} v2.0 surface reflectance",
                version=VERSION,
                retrieval_date=datetime.fromtimestamp(path.stat().st_mtime).date().isoformat(),
                licence=LICENCE,
                subset=subset_record(
                    "window", field_id=field_id, buffer_m=BUFFER_M, bbox_lonlat=list(window_box),
                    granule=s.granule, tile=s.tile, band=band, acquired=s.acquired.isoformat(),
                    cloud_cover=s.cloud_cover, crs=TILE_CRS,
                ),
                evidence_type="observed",
                scale="30 m raster",
                notes=(
                    "Window clip of the original band; values unmasked and unscaled (reflectance "
                    "scale 0.0001, fill -9999; Fmask uint8, fill 255). DS1 applies the mask in Phase 5. "
                    + (FMASK_NOTE if band == "Fmask" else "")
                ),
            )
            check = check_clip(path, band, plain, season, s.acquired)
            items.append(Item(path, manifest, check, f"{SOURCE}/{s.sensor}", f"{field_id}/{when}/{band.lower()}.tif"))
    check_budget(SOURCE, sum(i.manifest.size_bytes for i in items), BUDGET_BYTES)
    return items


def plan_first_pull(base: Path | None = None) -> list[Item]:
    return plan_field(FIRST_FIELD, FIRST_YEAR, base)


def probe() -> int:
    """Read one small window from one band, to prove the login works. Prints no secrets."""
    fields = gpd.read_file(FIELDS_PATH)
    bbox = field_bboxes(fields[fields.field_id == FIRST_FIELD], BUFFER_M)[FIRST_FIELD]
    scene = search_scenes("l30", bbox, FIRST_YEAR)[0]
    dest = Path(tempfile.mkdtemp(prefix="hls-probe-")) / "b04.tif"
    try:
        with earthdata_session() as resolve:
            info = clip_to_file(scene.hrefs["B04"], bbox, dest, resolve)
        with rasterio.open(dest) as src:
            data = src.read(1)
            print(f"OK: {scene.granule} B04 window {info['cols']}x{info['rows']} px, {src.crs}, "
                  f"dtype {src.dtypes[0]}, nodata {src.nodata}, values {int(data.min())}..{int(data.max())}")
        return 0
    except (OSError, ValueError, KeyError, IndexError, rasterio.errors.RasterioError) as err:
        password = os.environ.get("EARTHDATA_PASSWORD", "")
        message = f"{type(err).__name__}: {err}"
        print("FAILED:", message.replace(password, "***") if password else message)
        return 1
    finally:
        shutil.rmtree(dest.parent, ignore_errors=True)


def diagnose() -> int:
    """Follow NASA's documented Earthdata login flow for one band and say what comes back."""
    import re
    import urllib.error
    from http.cookiejar import CookieJar
    from urllib.parse import urlparse

    fields = gpd.read_file(FIELDS_PATH)
    bbox = field_bboxes(fields[fields.field_id == FIRST_FIELD], BUFFER_M)[FIRST_FIELD]
    href = search_scenes("l30", bbox, FIRST_YEAR)[0].hrefs["B04"]
    user, password = os.environ.get("EARTHDATA_USERNAME", ""), os.environ.get("EARTHDATA_PASSWORD", "")
    manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    manager.add_password(None, "https://urs.earthdata.nasa.gov", user, password)
    opener = urllib.request.build_opener(
        urllib.request.HTTPBasicAuthHandler(manager),
        urllib.request.HTTPCookieProcessor(CookieJar()),
    )
    request = urllib.request.Request(href, headers={"Range": "bytes=0-1023"})
    try:
        with opener.open(request, timeout=60) as resp:
            head = resp.read(1024)
            where = urlparse(resp.geturl())
            print(f"status {resp.status}, final host {where.netloc}, type {resp.headers.get('Content-Type')}")
            if head[:4] in (b"II*\x00", b"MM\x00*"):
                print("got TIFF bytes: the login works over plain HTTP")
            else:
                text = re.sub(r"\s+", " ", head.decode("utf-8", "replace"))
                print("not a TIFF; first bytes:", text[:300])
        return 0
    except urllib.error.HTTPError as err:
        print(f"HTTP {err.code} from {urlparse(err.geturl()).netloc}: {err.reason}")
        return 1
    except (urllib.error.URLError, OSError) as err:
        print(f"{type(err).__name__}: {err}")
        return 1


if __name__ == "__main__":
    command = sys.argv[1] if sys.argv[1:] else ""
    sys.exit({"probe": probe, "diagnose": diagnose}.get(command, lambda: 2)())
