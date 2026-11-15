"""NAIP raw data: one small per-field image chip (red, green, blue, near-infrared) for one year.

Reference imagery for field inspection and boundary checks (PRD S11), never crop ground truth.
NAIP is read as cloud-optimised GeoTIFF from the Microsoft Planetary Computer catalogue, taking
only the pixels inside each field plus a small buffer, never the whole quarter-quad tile.
Settings follow docs/source_requirements/de_p1_layers_draft.md section 3 (DE draft, pending DS1
sign-off). The access token is anonymous, short-lived, held in memory and never written down.

Each chip keeps the pixel values and the grid of its source tile (no resampling, no colour
change). A field that straddles two tiles is cut from both and mosaicked only if neither tile
covers it alone; the manifest then lists every source tile and its own flight date.
"""

import json
import re
import time
import urllib.error
import urllib.request
from contextlib import ExitStack
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import geopandas as gpd
import rasterio
from rasterio.merge import merge

from ingest.checks import CheckResult
from ingest.hls import GDAL_OPTIONS, window_for
from ingest.items import Item
from ingest.manifest import build_manifest
from ingest.subset import check_budget, field_bboxes, subset_record
from transform.field_schema import FIELDS_PATH

SOURCE = "naip"
YEAR = 2025
BUFFER_M = 50.0
BUDGET_BYTES = 100_000_000
STAC_SEARCH = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
TOKEN_URL = "https://planetarycomputer.microsoft.com/api/sas/v1/token/naip"
COLLECTION = "naip"
BANDS = ("Red", "Green", "Blue", "NIR")
LICENCE = (
    "NAIP imagery is produced by the USDA Farm Service Agency (APFO) and served by Microsoft "
    "Planetary Computer. The catalogue gives no licence text; the terms were not confirmed from "
    "a source page, so check before redistributing."
)
SCALE = "0.3 to 1.0 m pixels depending on year (0.6 m in 2025); one flight date per tile; not crop ground truth"


@dataclass(frozen=True)
class Tile:
    item_id: str
    href: str
    flown: date
    bbox: tuple[float, float, float, float]  # lon/lat, from the catalogue


_TILE_DATE = re.compile(r"_(\d{8})$")
TILES_RECORD = ".tiles.json"  # beside each chip: the tile ids it was cut from


def flight_date_from_id(tile_id: str) -> date:
    """The flight date is the last part of a NAIP item id (YYYYMMDD)."""
    match = _TILE_DATE.search(tile_id)
    if not match:
        raise ValueError(f"tile {tile_id!r} has no flight date in its name")
    text = match.group(1)
    return date(int(text[:4]), int(text[4:6]), int(text[6:]))


def default_dir() -> Path:
    return Path.home() / "agrocycle_naip"


def _get(url: str, body: dict | None = None, retries: int = 4) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=120) as resp:
                return json.load(resp)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as err:
            temporary = not isinstance(err, urllib.error.HTTPError) or err.code >= 500 or err.code == 429
            if not temporary or attempt == retries - 1:
                raise RuntimeError(f"NAIP catalogue request failed: {type(err).__name__}") from None
            time.sleep(4 * (attempt + 1))
    raise AssertionError("unreachable")


def access_token() -> str:
    return _get(TOKEN_URL)["token"]


def search_tiles(bbox: tuple[float, float, float, float], year: int = YEAR) -> list[Tile]:
    """Every NAIP tile of `year` that touches the bbox (lon/lat)."""
    page = _get(STAC_SEARCH, {"collections": [COLLECTION], "bbox": list(bbox),
                              "datetime": f"{year}-01-01/{year}-12-31", "limit": 50})
    return [
        Tile(f["id"], f["assets"]["image"]["href"],
             datetime.fromisoformat(f["properties"]["datetime"]).date(),
             tuple(f["bbox"]))
        for f in page["features"]
    ]


def _covers(src, bbox) -> bool:
    """True if the raster's extent holds the whole bbox."""
    from rasterio.warp import transform_bounds

    left, bottom, right, top = transform_bounds("EPSG:4326", src.crs, *bbox)
    b = src.bounds
    return b.left <= left and b.bottom <= bottom and b.right >= right and b.top >= top


def clip_chip(tiles: list[Tile], bbox, dest: Path, token: str) -> dict:
    """Cut the bbox from the first tile (in id order) that covers it, else mosaic the tiles that touch it.

    Tiles are opened one at a time, so a field inside one tile costs one header read, not one per candidate.
    """
    tiles = sorted(tiles, key=lambda t: t.item_id)
    with rasterio.Env(**GDAL_OPTIONS), ExitStack() as stack:
        opened, whole = [], None
        for tile in tiles:
            src = stack.enter_context(rasterio.open(f"{tile.href}?{token}" if token else tile.href))
            opened.append((tile, src))
            if _covers(src, bbox):
                whole = (tile, src)
                break
        used = [whole] if whole else opened
        pieces = []
        for tile, src in used:
            window, _ = window_for(src, bbox)
            try:  # only the part of the window that lies inside this tile
                inside = window.intersection(rasterio.windows.Window(0, 0, src.width, src.height))
            except rasterio.errors.WindowError:
                continue  # the tile touches the search box but not the field box
            pieces.append((src.read(window=inside), src.window_transform(inside), src, tile))
        if not pieces:
            raise RuntimeError("no tile holds any pixel of the requested box")
        first = pieces[0][2]
        profile = {"driver": "GTiff", "count": first.count, "dtype": first.dtypes[0], "crs": first.crs,
                   "compress": "deflate", "predictor": 2, "tiled": True, "blockxsize": 256,
                   "blockysize": 256}
        dest.parent.mkdir(parents=True, exist_ok=True)
        part = dest.with_name(dest.name + ".part")
        if len(pieces) == 1:
            data, transform, _, _ = pieces[0]
            with rasterio.open(part, "w", height=data.shape[1], width=data.shape[2],
                               transform=transform, **profile) as out:
                out.write(data)
        else:  # the field straddles tiles: mosaic only the clipped windows
            with ExitStack() as inner:
                datasets = []
                for data, transform, _, _ in pieces:
                    memory = inner.enter_context(rasterio.MemoryFile())
                    with memory.open(driver="GTiff", count=data.shape[0], dtype=data.dtype, crs=first.crs,
                                     height=data.shape[1], width=data.shape[2], transform=transform) as w:
                        w.write(data)
                    datasets.append(inner.enter_context(memory.open()))
                mosaic, transform = merge(datasets)
            with rasterio.open(part, "w", height=mosaic.shape[1], width=mosaic.shape[2],
                               transform=transform, **profile) as out:
                out.write(mosaic)
        part.rename(dest)
        return {"tiles": [piece[3].item_id for piece in pieces]}


def check_chip(path: Path, bbox) -> CheckResult:
    result = CheckResult()
    try:
        with rasterio.open(path) as src:
            if src.count != 4 or src.dtypes[0] != "uint8":
                result.problems.append(f"{path.name}: expected 4 uint8 bands, got {src.count} {src.dtypes[0]}")
            if src.crs is None:
                result.problems.append(f"{path.name}: no CRS")
            if not _covers(src, bbox):
                result.problems.append(f"{path.name}: chip does not cover the requested box")
            data = src.read()
            if not data.any():
                result.problems.append(f"{path.name}: every pixel is 0 (no imagery)")
            elif (data == 0).all(axis=0).mean() > 0.02:
                result.problems.append(f"{path.name}: over 2 % of pixels are 0 in all bands (edge of tile?)")
            if src.width * src.height < 100:
                result.problems.append(f"{path.name}: chip is only {src.width} x {src.height} pixels")
    except (OSError, rasterio.errors.RasterioError) as err:
        result.problems.append(f"{path.name}: cannot be opened ({type(err).__name__})")
    return result


def _saved_tiles(path: Path) -> list[Tile] | None:
    """The tiles a saved chip was cut from, from its record. None if the chip or its record is missing."""
    record = path.with_name(path.name + TILES_RECORD)
    if not (path.exists() and record.exists()):
        return None
    return [Tile(i, "", flight_date_from_id(i), ()) for i in json.loads(record.read_text())]


def plan(base: Path | None = None, searcher=search_tiles, clipper=clip_chip, token=None,
         fields: gpd.GeoDataFrame | None = None, year: int = YEAR) -> list[Item]:
    """One chip per field for `year`. A saved chip with its tile record is reused, with no network call.

    A chip saved without its record is cut again, so the manifest always names the tiles the pixels came from.
    The access token is fetched only when a chip has to be cut.
    """
    base = Path(base) if base else default_dir()
    base.mkdir(parents=True, exist_ok=True)
    fields = fields if fields is not None else gpd.read_file(FIELDS_PATH)
    items = []
    for field_id, bbox in field_bboxes(fields, BUFFER_M).items():
        path = base / f"{field_id}_naip{year}.tif"
        chosen = _saved_tiles(path)
        if chosen is None:
            tiles = searcher(bbox, year)
            if not tiles:
                items.append(_failed(path.name, f"no NAIP {year} tile covers {field_id}"))
                continue
            if token is None:
                token = access_token()
            used = clipper(tiles, bbox, path, token)["tiles"]
            path.with_name(path.name + TILES_RECORD).write_text(json.dumps(sorted(used)) + "\n")
            chosen = [t for t in tiles if t.item_id in used]
        checks = check_chip(path, bbox)
        items.append(Item(path, _manifest(path, field_id, bbox, chosen, year), checks, SOURCE))
    check_budget(SOURCE, sum(i.manifest.size_bytes for i in items), BUDGET_BYTES)
    return items


def _failed(name: str, problem: str) -> Item:
    from ingest.manifest import Manifest

    placeholder = Manifest(
        source_url="n/a", product="n/a", version="n/a", retrieval_date=date.today().isoformat(),
        sha256="0" * 64, size_bytes=0, licence="n/a", subset={}, evidence_type="assumption",
        scale="n/a", notes="no chip made",
    )
    return Item(Path(name), placeholder, CheckResult([problem]), SOURCE)


def _manifest(path: Path, field_id: str, bbox, tiles: list[Tile], year: int):
    flights = sorted({t.flown.isoformat() for t in tiles})
    return build_manifest(
        path,
        source_url=f"{STAC_SEARCH} (collection {COLLECTION}, item {', '.join(t.item_id for t in tiles)})",
        product="USDA NAIP aerial imagery, 4-band (red, green, blue, near-infrared), via Microsoft Planetary Computer",
        version=f"naip-{year}",
        retrieval_date=date.fromtimestamp(path.stat().st_mtime).isoformat(),
        licence=LICENCE,
        subset=subset_record(
            "field_chip", field_id=field_id, bbox=list(bbox), buffer_m=BUFFER_M, year=year,
            bands=list(BANDS), tiles=[t.item_id for t in tiles], flight_dates=flights,
        ),
        evidence_type="observed",
        scale=SCALE,
        notes=(
            f"Pixels cut from the source tile unchanged (no resampling or colour change); flown {', '.join(flights)}. "
            "A single date, so it shows the field at that moment only. Reference imagery for inspection "
            "and boundary checks, not crop ground truth. The access token is not recorded."
        ),
    )
