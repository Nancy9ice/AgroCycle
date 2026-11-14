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
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
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
from ingest.subset import check_budget, field_bboxes, subset_record, union_bbox
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


def _get_json(url: str, retries: int = 5) -> dict:
    """GET a JSON page, retrying server errors (NASA's search sometimes answers 502 or 503)."""
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=120) as resp:
                return json.load(resp)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as err:
            temporary = not isinstance(err, urllib.error.HTTPError) or err.code >= 500
            if not temporary or attempt == retries - 1:
                raise
            time.sleep(5 * (attempt + 1))
    raise AssertionError("unreachable")


def search_scenes(sensor: str, bbox: tuple[float, float, float, float], year: int) -> list[Scene]:
    """All HLS scenes that touch the bbox between 1 April and 31 October."""
    start, end = date(year, 4, 1), date(year, 10, 31)
    url = (
        f"{STAC_SEARCH}?collections={COLLECTIONS[sensor]}&bbox={','.join(map(str, bbox))}"
        f"&datetime={start}T00:00:00Z/{end}T23:59:59Z&limit=200"
    )
    scenes = []
    while url:
        page = _get_json(url)
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


# ---- full run: one read of each scene, windows for every field, stacked files -----------------
FULL_YEARS = (2023, 2024, 2025)
SCENE_WORKERS = 12  # a scene is mostly waiting on the network, so more in parallel helps
STACK_NOTE = (
    "Four bands in this order: {order}. All stored as int16 so they can share one file: Fmask is "
    "uint8 in the source and its values (0-255, fill 255) are unchanged. Reflectance scale 0.0001, "
    "fill -9999. Unmasked: DS1 applies the mask in Phase 5. "
)


def stack_name(sensor: str) -> str:
    return "stack_" + "_".join(b.lower() for b in BANDS[sensor]) + ".tif"


def stack_path(base: Path, sensor: str, field_id: str, day: str) -> Path:
    return base / "stacks" / sensor / field_id / day / stack_name(sensor)


def window_for(src, bbox: tuple[float, float, float, float]):
    """The pixel window (and its transform) covering bbox (lon/lat) on this raster's grid."""
    left, bottom, right, top = transform_bounds("EPSG:4326", src.crs, *bbox)
    res = src.res[0]
    col0 = math.floor((left - src.transform.c) / res)
    row0 = math.floor((src.transform.f - top) / res)
    cols = math.ceil((right - src.transform.c) / res) - col0
    rows = math.ceil((src.transform.f - bottom) / res) - row0
    transform = Affine(res, 0, src.transform.c + col0 * res, 0, -res, src.transform.f - row0 * res)
    return rasterio.windows.Window(col0, row0, cols, rows), transform


def covers(bounds: tuple[float, float, float, float], bbox: tuple[float, float, float, float]) -> bool:
    left, bottom, right, top = transform_bounds("EPSG:4326", TILE_CRS, *bbox)
    return bounds[0] <= left and bounds[1] <= bottom and bounds[2] >= right and bounds[3] >= top


def assign_tiles(windows: dict[str, tuple], bounds: dict[str, tuple]) -> dict[str, str]:
    """One tile per field: the tile that covers the most fields, else one that covers this field."""
    covered = {t: {f for f, frame in windows.items() if covers(bounds[t], frame)} for t in bounds}
    order = sorted(bounds, key=lambda t: (-len(covered[t]), t))
    assignment = {}
    for field_id in windows:
        tile = next((t for t in order if field_id in covered[t]), None)
        if tile is None:
            raise RuntimeError(f"{field_id}: no single HLS tile covers its window")
        assignment[field_id] = tile
    return assignment


def scene_bounds(scene: Scene, resolve) -> tuple[float, float, float, float]:
    with rasterio.Env(**GDAL_OPTIONS), rasterio.open(resolve(scene.hrefs["B04"])) as src:
        return tuple(src.bounds)


def cut_scene(scene: Scene, jobs: list[tuple], resolve) -> int:
    """Open the scene's four bands once and write one stacked file per field window."""
    names = BANDS[scene.sensor]
    with rasterio.Env(**GDAL_OPTIONS):
        sources = [rasterio.open(resolve(scene.hrefs[b])) for b in names]
        try:
            ref = sources[0]
            if any(s.transform != ref.transform or s.shape != ref.shape for s in sources):
                raise RuntimeError(f"{scene.granule}: bands are on different grids")
            # One read per band of the region that covers every requested window, then slice in
            # memory: far fewer round trips than one remote read per field and band.
            cuts = [window_for(ref, bbox) for bbox, _ in jobs]
            row0, col0 = min(w.row_off for w, _ in cuts), min(w.col_off for w, _ in cuts)
            row1 = max(w.row_off + w.height for w, _ in cuts)
            col1 = max(w.col_off + w.width for w, _ in cuts)
            region = rasterio.windows.Window(col0, row0, col1 - col0, row1 - row0)
            frames = [s.read(1, window=region).astype("int16") for s in sources]
            for (_, dest), (window, transform) in zip(jobs, cuts, strict=True):
                r, c = window.row_off - row0, window.col_off - col0
                arrays = [f[r : r + window.height, c : c + window.width] for f in frames]
                dest.parent.mkdir(parents=True, exist_ok=True)
                part = dest.with_name(dest.name + ".part")
                with rasterio.open(part, "w", driver="GTiff", height=window.height, width=window.width,
                                   count=len(arrays), dtype="int16", crs=ref.crs, transform=transform,
                                   compress="deflate") as out:
                    for i, (name, data) in enumerate(zip(names, arrays, strict=True), 1):
                        out.write(data, i)
                        out.set_band_description(i, name)
                    out.update_tags(granule=scene.granule, sensor=scene.sensor, tile=scene.tile,
                                    acquired=scene.acquired.isoformat(), bands=",".join(names))
                part.rename(dest)
        finally:
            for s in sources:
                s.close()
    return len(jobs)


def pull_full(base: Path, fields: gpd.GeoDataFrame, years=FULL_YEARS, searcher=search_scenes,
              cutter=cut_scene, bounds_reader=scene_bounds):
    """Cut every field's stack from every scene, reading each scene once."""
    windows = field_bboxes(fields, BUFFER_M)
    union = union_bbox(fields, BUFFER_M)
    scenes = [s for sensor in COLLECTIONS for y in years for s in searcher(sensor, union, y)]
    seen: dict[tuple, str] = {}
    for s in scenes:
        slot = (s.sensor, s.tile, f"{s.acquired:%Y%m%d}")
        if slot in seen:
            raise RuntimeError(f"two granules on one date: {seen[slot]} and {s.granule}")
        seen[slot] = s.granule
    with earthdata_session() as resolve:
        first: dict[str, Scene] = {}
        for s in scenes:
            first.setdefault(s.tile, s)
        found = {t: bounds_reader(sc, resolve) for t, sc in first.items()}
        assignment = assign_tiles(windows, found)
        work = []
        for s in scenes:
            jobs = [(windows[f], stack_path(base, s.sensor, f, f"{s.acquired:%Y%m%d}"))
                    for f, tile in assignment.items() if tile == s.tile]
            jobs = [(frame, dest) for frame, dest in jobs if not dest.exists()]
            if jobs:
                work.append((s, jobs))
        print(f"{len(scenes)} scenes, {len(assignment)} fields; {len(work)} scenes still to cut", flush=True)
        failures, started = [], time.time()
        with ThreadPoolExecutor(SCENE_WORKERS) as pool:
            futures = {pool.submit(cutter, s, jobs, resolve): s for s, jobs in work}
            for n, future in enumerate(as_completed(futures), 1):
                try:
                    future.result()
                except (OSError, ValueError, RuntimeError, rasterio.errors.RasterioError) as err:
                    failures.append(f"{futures[future].granule}: {type(err).__name__}: {str(err)[:120]}")
                if n % 25 == 0 or n == len(work):
                    print(f"  cut {n} of {len(work)} scenes ({time.time() - started:.0f} s)", flush=True)
    if failures:
        raise RuntimeError(f"{len(failures)} scenes failed (rerun to retry):\n- " + "\n- ".join(failures[:10]))
    return scenes, assignment, windows


def check_stack(path: Path, field_box, season: tuple[date, date], acquired: datetime, n_bands: int) -> CheckResult:
    result = CheckResult()
    try:
        with rasterio.open(path) as src:
            data = src.read()
            if src.crs.to_string() != TILE_CRS:
                result.problems.append(f"{path.name}: CRS {src.crs.to_string()}, expected {TILE_CRS}")
            if src.count != n_bands or src.dtypes[0] != "int16":
                result.problems.append(f"{path.name}: {src.count} bands of {src.dtypes[0]}, expected {n_bands} of int16")
            left, bottom, right, top = transform_bounds("EPSG:4326", src.crs, *field_box)
            if not (src.bounds.left <= left and src.bounds.bottom <= bottom
                    and src.bounds.right >= right and src.bounds.top >= top):
                result.problems.append(f"{path.name}: does not cover the field")
            if bool(np.all(data[:-1] == -9999)):
                result.problems.append(f"{path.name}: every reflectance pixel is fill")
            if data[-1].min() < 0 or data[-1].max() > 255:
                result.problems.append(f"{path.name}: Fmask values outside 0-255")
    except (OSError, rasterio.errors.RasterioError) as err:
        result.problems.append(f"{path.name}: cannot be opened ({err})")
    if not season[0] <= acquired.date() <= season[1]:
        result.problems.append(f"{path.name}: date {acquired.date()} outside April to October")
    return result


def plan_full(base: Path | None = None, years=FULL_YEARS, searcher=search_scenes, cutter=cut_scene,
              bounds_reader=scene_bounds) -> list[Item]:
    """All fields, all scenes, 2023-2025, one stacked file per field per date per sensor."""
    base = Path(base) if base else default_dir()
    fields = gpd.read_file(FIELDS_PATH)
    scenes, assignment, windows = pull_full(base, fields, years, searcher, cutter, bounds_reader)
    plain = field_bboxes(fields)
    items = []
    for s in scenes:
        names, day = BANDS[s.sensor], f"{s.acquired:%Y%m%d}"
        season = (date(s.acquired.year, 4, 1), date(s.acquired.year, 10, 31))
        for field_id, tile in assignment.items():
            if tile != s.tile:
                continue
            path = stack_path(base, s.sensor, field_id, day)
            manifest = build_manifest(
                path,
                source_url=s.hrefs[names[0]],
                product=f"NASA HLS {s.sensor.upper()} v2.0 surface reflectance, stacked window",
                version=VERSION,
                retrieval_date=datetime.fromtimestamp(path.stat().st_mtime).date().isoformat(),
                licence=LICENCE,
                subset=subset_record(
                    "window-stack", field_id=field_id, buffer_m=BUFFER_M, bbox_lonlat=list(windows[field_id]),
                    granule=s.granule, tile=s.tile, bands=list(names), source_hrefs=[s.hrefs[b] for b in names],
                    acquired=s.acquired.isoformat(), cloud_cover=s.cloud_cover, crs=TILE_CRS,
                ),
                evidence_type="observed",
                scale="30 m raster",
                notes=STACK_NOTE.format(order=", ".join(names)) + FMASK_NOTE,
            )
            check = check_stack(path, plain[field_id], season, s.acquired, len(names))
            name = stack_name(s.sensor)
            items.append(Item(path, manifest, check, f"{SOURCE}/{s.sensor}", f"{field_id}/{day}/{name}"))
    check_budget(SOURCE, sum(i.manifest.size_bytes for i in items), BUDGET_BYTES)
    return items


def bench() -> int:
    """Time one scene cut for every field, to show what the full run will cost."""
    fields = gpd.read_file(FIELDS_PATH)
    windows = field_bboxes(fields, BUFFER_M)
    union = union_bbox(fields, BUFFER_M)
    scene = next(s for s in search_scenes("l30", union, FIRST_YEAR) if s.tile == "T15TVG")
    folder = Path(tempfile.mkdtemp(prefix="hls-bench-"))
    try:
        jobs = [(frame, stack_path(folder, "l30", f, f"{scene.acquired:%Y%m%d}")) for f, frame in windows.items()]
        started = time.time()
        with earthdata_session() as resolve:
            count = cut_scene(scene, jobs, resolve)
        seconds = time.time() - started
        size = sum(dest.stat().st_size for _, dest in jobs)
        print(f"one scene ({scene.granule}): {count} field stacks in {seconds:.1f} s, {size / 1e3:.0f} KB")
        return 0
    finally:
        shutil.rmtree(folder, ignore_errors=True)


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
    sys.exit({"probe": probe, "diagnose": diagnose, "bench": bench}.get(command, lambda: 2)())
