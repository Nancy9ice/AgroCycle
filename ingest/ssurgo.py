"""SSURGO raw data: USDA Soil Data Access responses stored exactly as the service returns them.

Four queries per field, following docs/source_requirements/ds2_source_requirements.md
section 2: A map units (with the field's intersection geometry, so Phase 4 can compute area
shares), B components, C horizons, D survey version. The first pull is `primary-001`, which DS2
reviews before the full run. Nothing is cleaned, weighted or dropped here.
"""

import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

import geopandas as gpd
from shapely import to_wkt

from ingest.checks import CheckResult
from ingest.items import Item
from ingest.manifest import build_manifest
from ingest.subset import check_budget, subset_record
from transform.field_schema import FIELDS_PATH

SOURCE = "ssurgo"
VERSION = "soil-data-access"
BUDGET_BYTES = 200_000_000
SDA_URL = "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest"
FIRST_FIELD = "primary-001"
AREA_SYMBOLS = {"Boone": "IA015", "Story": "IA169"}
LICENCE = (
    "USDA NRCS soil survey data, publicly available through Soil Data Access. Terms were not "
    "confirmed from a source page; check before redistributing."
)
SCALE = "mapped soil units (survey), not a lab sample of the field"
COMPONENT_COLUMNS = (
    "mu.mukey, mu.musym, mu.muname, c.cokey, c.compname, c.comppct_r, c.majcompflag, c.slope_r, "
    "c.slopelenusle_r, c.drainagecl, c.hydgrp, c.hydricrating, c.taxclname, c.tfact"
)
HORIZON_COLUMNS = (
    "ch.cokey, ch.chkey, ch.hzname, ch.hzdept_r, ch.hzdepb_r, ch.sandtotal_r, ch.silttotal_r, "
    "ch.claytotal_r, ch.om_r, ch.ph1to1h2o_r, ch.awc_r, ch.ksat_r, ch.dbthirdbar_r, "
    "ch.cec7_r, ch.kffact"
)


def default_dir() -> Path:
    return Path.home() / "agrocycle_ssurgo"


def post(query: str, timeout: int = 180) -> bytes:
    """One Soil Data Access query. The response body is returned untouched."""
    data = json.dumps({"format": "JSON+COLUMNNAME", "query": query}).encode()
    request = urllib.request.Request(SDA_URL, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as err:  # the service's own wording matters for DS2
        raise RuntimeError(f"Soil Data Access rejected the query: HTTP {err.code} {err.read()[:300]!r}") from err


def rows(body: bytes) -> list[list]:
    """Data rows of a JSON+COLUMNNAME response (the first row holds the column names)."""
    table = json.loads(body)["Table"]
    return table[1:]


def query_a(wkt: str) -> str:
    geom = f"geometry::STGeomFromText('{wkt}', 4326)"
    return (
        f"SELECT mp.mukey, mp.mupolygongeo.STIntersection({geom}).STAsText() AS isect_wkt "
        f"FROM mupolygon AS mp WHERE mp.mupolygongeo.STIntersects({geom}) = 1"
    )


def query_a_fallback(wkt: str) -> str:
    return f"SELECT DISTINCT mukey FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('{wkt}')"


def query_b(mukeys: list[str]) -> str:
    keys = ",".join(f"'{k}'" for k in mukeys)
    return (
        f"SELECT {COMPONENT_COLUMNS} FROM mapunit mu LEFT JOIN component c ON c.mukey = mu.mukey "
        f"WHERE mu.mukey IN ({keys})"
    )


def query_c(cokeys: list[str]) -> str:
    keys = ",".join(f"'{k}'" for k in cokeys)
    return f"SELECT {HORIZON_COLUMNS} FROM chorizon ch WHERE ch.cokey IN ({keys})"


def query_d() -> str:
    areas = ",".join(f"'{a}'" for a in AREA_SYMBOLS.values())
    return f"SELECT areasymbol, areaname, saverest FROM sacatalog WHERE areasymbol IN ({areas})"


def _structure(body: bytes, label: str, checks: CheckResult) -> list[list]:
    try:
        return rows(body)
    except (ValueError, KeyError, TypeError):
        checks.problems.append(f"{label}: not a Soil Data Access table ({body[:120]!r})")
        return []


def pull_field(field_id: str, wkt: str, base: Path, poster=post) -> dict:
    """Run steps A to D for one field and save each raw response. Reuses saved files."""
    folder = base / field_id
    folder.mkdir(parents=True, exist_ok=True)
    queries, route = {}, "A: STIntersection with area geometry"

    def save(name: str, query: str, fn) -> bytes:
        path = folder / name
        if not path.exists():  # one pull is kept; the service is not asked again
            path.write_bytes(fn(query))
        queries[name] = query
        return path.read_bytes()

    a_path = folder / "step_a_map_units.json"
    try:
        body_a = save(a_path.name, query_a(wkt), poster)
        rows(body_a)
    except (RuntimeError, ValueError, KeyError, TypeError):
        a_path.unlink(missing_ok=True)  # rejected: use the sheet's fallback, no area geometry
        route = "A fallback: SDA_Get_Mukey_from_intersection_with_WktWgs84 (no areas; area_unknown)"
        body_a = save(a_path.name, query_a_fallback(wkt), poster)
    mukeys = sorted({str(r[0]) for r in rows(body_a)})
    body_b = save("step_b_components.json", query_b(mukeys), poster)
    cokeys = sorted({str(r[3]) for r in rows(body_b) if r[3] is not None})
    save("step_c_horizons.json", query_c(cokeys), poster)
    save("step_d_survey_areas.json", query_d(), poster)
    return {"folder": folder, "queries": queries, "route": route, "mukeys": mukeys, "cokeys": cokeys}


def plan_field(field_id: str, wkt: str, base: Path, poster=post) -> list[Item]:
    pulled = pull_field(field_id, wkt, base, poster)
    items, a_rows = [], None
    for name, query in pulled["queries"].items():
        path = pulled["folder"] / name
        body = path.read_bytes()
        checks = CheckResult()
        table = _structure(body, name, checks)
        if name == "step_a_map_units.json":
            a_rows = table
            if not table:
                checks.problems.append("no map units: a geometry or CRS problem, stop and tell DS2")
        if name == "step_b_components.json" and not any(r[3] is not None for r in table):
            checks.problems.append("no components found for the map units")
        if name == "step_c_horizons.json" and not table:
            checks.problems.append("no horizons found")
        manifest = build_manifest(
            path,
            source_url=SDA_URL,
            product="USDA NRCS SSURGO via Soil Data Access (REST, JSON+COLUMNNAME)",
            version=VERSION,
            retrieval_date=datetime.fromtimestamp(path.stat().st_mtime).date().isoformat(),
            licence=LICENCE,
            subset=subset_record(
                "sda-query", field_id=field_id, step=name.removesuffix(".json"),
                route=pulled["route"] if name.startswith("step_a") else "see step A",
                query=query, rows=len(table),
            ),
            evidence_type="survey",
            scale=SCALE,
            notes=(
                "Raw Soil Data Access response, unchanged. Representative (_r) values only; "
                "nothing dropped or filled. Area shares, weighting and units are Phase 4."
            ),
        )
        items.append(Item(path, manifest, checks, SOURCE, f"{field_id}/{name}"))
    check_budget(SOURCE, sum(i.manifest.size_bytes for i in items), BUDGET_BYTES)
    assert a_rows is not None
    return items


def plan_first_pull(base: Path | None = None, poster=post) -> list[Item]:
    base = Path(base) if base else default_dir()
    fields = gpd.read_file(FIELDS_PATH).set_index("field_id")
    wkt = to_wkt(fields.loc[FIRST_FIELD, "geometry"], rounding_precision=7)
    return plan_field(FIRST_FIELD, wkt, base, poster)
