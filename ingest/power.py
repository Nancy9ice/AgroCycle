"""NASA POWER raw data: daily point responses stored exactly as the API returns them.

Phase 1 stores the response verbatim (the -999 fill value is kept; conversion to null is
Phase 4). The first pull is the Marsden site for 2003-2011, which DS2 reviews before the
full run. Settings follow docs/source_requirements/ds2_source_requirements.md section 1.
"""

import json
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

import geopandas as gpd

from ingest.checks import CheckResult
from ingest.items import Item
from ingest.manifest import build_manifest
from ingest.subset import check_budget, field_points, subset_record
from transform.field_schema import FIELDS_PATH

SOURCE = "power"
BUDGET_BYTES = 100_000_000
BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
COMMUNITY = "AG"
VARIABLES = (
    "T2M_MAX", "T2M_MIN", "T2M", "PRECTOTCORR", "RH2M", "ALLSKY_SFC_SW_DWN", "WS2M",
)
MARSDEN_SITE = {"name": "marsden-site", "lat": 42.0167, "lon": -93.7833}  # Text S1
FIRST_PULL = (date(2003, 1, 1), date(2011, 12, 31))
FULL_PERIOD = (date(1991, 1, 1), date(2025, 12, 31))
LICENCE = (
    "NASA POWER data are freely available. Publications must include POWER's Reference and "
    "Data Reference (https://power.larc.nasa.gov/docs/referencing/)."
)
SCALE = "grid cell (MERRA-2 about 0.5 x 0.625 degrees, about 50 km; some variables coarser), not field"


def default_dir() -> Path:
    return Path.home() / "agrocycle_power"


def request_url(lat: float, lon: float, start: date, end: date, variables=VARIABLES) -> str:
    return (
        f"{BASE_URL}?parameters={','.join(variables)}&community={COMMUNITY}"
        f"&longitude={lon}&latitude={lat}&start={start:%Y%m%d}&end={end:%Y%m%d}&format=JSON"
    )


def fetch(url: str, retries: int = 3, timeout: int = 180) -> bytes:
    """GET with a few retries on server errors. The body is returned untouched."""
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                return resp.read()
        except (urllib.error.URLError, TimeoutError) as err:
            if attempt == retries - 1:
                raise RuntimeError(f"POWER request failed after {retries} tries: {err}") from err
            time.sleep(5 * (attempt + 1))
    raise AssertionError("unreachable")


def expected_dates(start: date, end: date) -> list[str]:
    return [f"{start + timedelta(days=i):%Y%m%d}" for i in range((end - start).days + 1)]


def inspect(body: bytes, start: date, end: date, variables=VARIABLES):
    """Structural checks on a raw POWER response. Returns (CheckResult, summary dict)."""
    result, summary = CheckResult(), {}
    try:
        doc = json.loads(body)
        parameter = doc["properties"]["parameter"]
        header = doc["header"]
        lon, lat, elevation = doc["geometry"]["coordinates"]
    except (ValueError, KeyError, TypeError) as err:
        result.problems.append(f"not a POWER daily response ({type(err).__name__}: {err})")
        return result, summary
    wanted = expected_dates(start, end)
    fill = header.get("fill_value")
    summary.update(
        api_version=header.get("api", {}).get("version"), sources=header.get("sources"),
        time_standard=header.get("time_standard"), fill_value=fill, returned_lat=lat,
        returned_lon=lon, elevation_m=elevation, days=len(wanted), fill_counts={},
    )
    if fill is None or not summary["time_standard"]:
        result.problems.append("header lacks fill_value or time_standard")
    for name in variables:
        series = parameter.get(name)
        if series is None:
            result.problems.append(f"{name}: missing")
            continue
        if sorted(series) != wanted:
            result.problems.append(f"{name}: {len(series)} dates, expected {len(wanted)}")
        if not all(isinstance(v, int | float) for v in series.values()):
            result.problems.append(f"{name}: non-numeric values")
        summary["fill_counts"][name] = sum(v == fill for v in series.values())
    return result, summary


def growing_season_summary(body: bytes) -> dict[int, tuple[float, float]]:
    """(mean T2M, total PRECTOTCORR) for April to November, by year. For the DS2 review only."""
    parameter = json.loads(body)["properties"]["parameter"]
    out = {}
    for year in sorted({d[:4] for d in parameter["T2M"]}):
        keys = [d for d in parameter["T2M"] if d[:4] == year and 4 <= int(d[4:6]) <= 11]
        t = [parameter["T2M"][k] for k in keys if parameter["T2M"][k] != -999]
        p = [parameter["PRECTOTCORR"][k] for k in keys if parameter["PRECTOTCORR"][k] != -999]
        out[int(year)] = (round(sum(t) / len(t), 2), round(sum(p), 1))
    return out


def _point_item(base: Path, name: str, lat: float, lon: float, start: date, end: date,
                fetcher, field_id: str | None = None) -> Item:
    """Pull one point once (the saved file is reused later) and describe it for upload."""
    path = base / f"{name}_{start:%Y%m%d}-{end:%Y%m%d}.json"
    url = request_url(lat, lon, start, end)
    if not path.exists():  # POWER can be reprocessed, so one pull is kept and never repeated
        path.write_bytes(fetcher(url))
    body = path.read_bytes()
    checks, summary = inspect(body, start, end)
    version = f"daily-point-api-{summary.get('api_version') or 'unknown'}"
    manifest = build_manifest(
        path,
        source_url=url,
        product="NASA POWER daily point API, community AG, JSON",
        version=version,
        retrieval_date=datetime.fromtimestamp(path.stat().st_mtime).date().isoformat(),
        licence=LICENCE,
        subset=subset_record(
            "point", site=name, field_id=field_id, lat=lat, lon=lon,
            start=f"{start:%Y%m%d}", end=f"{end:%Y%m%d}", variables=list(VARIABLES),
            community=COMMUNITY, time_standard=summary.get("time_standard"),
        ),
        evidence_type="model_reanalysis",
        scale=SCALE,
        notes=(
            f"Raw API response, unchanged. Fill value {summary.get('fill_value')} is kept as "
            f"returned (converted to null in Phase 4). Sources {summary.get('sources')}; "
            f"time standard {summary.get('time_standard')}; fill counts {summary.get('fill_counts')}. "
            "The API returns the coordinates sent, rounded; they do not identify the grid cell. "
            "Fields in the same grid cell have identical series; grouping is done in Phase 4."
        ),
    )
    return Item(path, manifest, checks, SOURCE)


def plan_first_pull(base: Path | None = None, fetcher=fetch) -> list[Item]:
    """The Marsden site for 2003-2011, which DS2 reviewed before the full run."""
    base = Path(base) if base else default_dir()
    base.mkdir(parents=True, exist_ok=True)
    item = _point_item(base, MARSDEN_SITE["name"], MARSDEN_SITE["lat"], MARSDEN_SITE["lon"],
                       *FIRST_PULL, fetcher)
    check_budget(SOURCE, item.manifest.size_bytes, BUDGET_BYTES)
    return [item]


def plan_full(base: Path | None = None, fetcher=fetch, pause: float = 2.0) -> list[Item]:
    """One request per field centroid plus the Marsden site, 1991-2025 (DS2's sheet).

    DS2 agreed to one request per field, with identical series grouped in Phase 4.
    """
    base = Path(base) if base else default_dir()
    base.mkdir(parents=True, exist_ok=True)
    start, end = FULL_PERIOD
    fields = gpd.read_file(FIELDS_PATH)
    points = [(MARSDEN_SITE["name"], MARSDEN_SITE["lat"], MARSDEN_SITE["lon"], None)]
    points += [(fid, lat, lon, fid) for fid, (lon, lat) in field_points(fields).items()]
    items = []
    for name, lat, lon, field_id in points:
        fresh = not (base / f"{name}_{start:%Y%m%d}-{end:%Y%m%d}.json").exists()
        items.append(_point_item(base, name, lat, lon, start, end, fetcher, field_id))
        if fresh:
            time.sleep(pause)  # be polite to the public API
    check_budget(SOURCE, sum(i.manifest.size_bytes for i in items), BUDGET_BYTES)
    return items
