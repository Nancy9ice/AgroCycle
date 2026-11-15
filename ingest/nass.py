"""NASS QuickStats raw data: county statistics stored exactly as the API returns them.

County context only, never field-level yield validation (PRD S12). One request per county,
commodity and statistic, so each file is small and a failed request is easy to repeat.
Withheld values such as "(D)" are kept as returned; they become null in the clean step.
Settings follow docs/source_requirements/de_p1_layers_draft.md section 1 (DE draft, pending
DS2 sign-off). The API key is read from the environment and is never written to a manifest,
a file or a message.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path

from common.config import nass_api_key
from ingest.checks import CheckResult
from ingest.items import Item
from ingest.manifest import Manifest, build_manifest
from ingest.subset import check_budget, subset_record

SOURCE = "nass"
BUDGET_BYTES = 5_000_000
BASE_URL = "https://quickstats.nass.usda.gov/api/api_GET/"
COUNTIES = {"STORY": "169", "BOONE": "015"}  # county_code within Iowa (FIPS 19169 and 19015)
COMMODITIES = ("CORN", "SOYBEANS", "OATS", "HAY")  # the alfalfa line is under HAY
STATISTICS = ("AREA PLANTED", "AREA HARVESTED", "YIELD", "PRODUCTION")
YEARS = (2003, 2025)
EMPTY_NAME = "empty_requests.json"
REQUIRED_FIELDS = (
    "commodity_desc", "statisticcat_desc", "unit_desc", "county_code", "state_alpha",
    "year", "Value", "short_desc", "freq_desc", "reference_period_desc",
)
LICENCE = (
    "USDA NASS QuickStats data are public domain. Cite USDA National Agricultural Statistics "
    "Service, QuickStats (https://quickstats.nass.usda.gov/)."
)
SCALE = "county (Story and Boone, Iowa), not field"


def default_dir() -> Path:
    return Path.home() / "agrocycle_nass"


def query_params(county: str, commodity: str, statistic: str, years=YEARS) -> dict[str, str]:
    """The request parameters without the key."""
    return {
        "source_desc": "SURVEY", "agg_level_desc": "COUNTY", "state_alpha": "IA",
        "county_name": county, "commodity_desc": commodity, "statisticcat_desc": statistic,
        "year__GE": str(years[0]), "year__LE": str(years[1]), "format": "JSON",
    }


def public_url(params: dict[str, str]) -> str:
    """The URL kept in the manifest: the key is replaced so it never reaches S3."""
    return BASE_URL + "?" + urllib.parse.urlencode({"key": "<NASS_API_KEY>", **params})


class NoDataError(RuntimeError):
    """The API answered that nothing matches the request (it uses a 400 for this)."""


def fetch(params: dict[str, str], retries: int = 3, timeout: int = 120) -> bytes:
    """GET with a few retries on server errors. The body is returned untouched."""
    url = BASE_URL + "?" + urllib.parse.urlencode({"key": nass_api_key(), **params})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", "replace")
            if err.code == 400 and "no data" in body.lower():
                raise NoDataError("no data for this request") from None
            if err.code < 500 or attempt == retries - 1:
                # the message never repeats the URL, which holds the key
                raise RuntimeError(f"NASS request failed: HTTP {err.code}") from None
            time.sleep(5 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError) as err:
            if attempt == retries - 1:
                raise RuntimeError(f"NASS request failed after {attempt + 1} tries: "
                                   f"{type(err).__name__}") from None
            time.sleep(5 * (attempt + 1))
    raise AssertionError("unreachable")


def inspect(body: bytes, county: str, commodity: str, statistic: str, years=YEARS):
    """Structural checks on a raw QuickStats response. Returns (CheckResult, summary dict)."""
    result, summary = CheckResult(), {}
    try:
        rows = json.loads(body)["data"]
    except (ValueError, KeyError, TypeError) as err:
        result.problems.append(f"not a QuickStats response ({type(err).__name__})")
        return result, summary
    if not isinstance(rows, list) or not rows:
        result.problems.append("no data rows")
        return result, summary
    suppressed = sum(1 for r in rows if str(r.get("Value", "")).strip().startswith("("))
    summary.update(rows=len(rows), suppressed=suppressed,
                   years=sorted({int(r["year"]) for r in rows if str(r.get("year", "")).isdigit()}))
    for n, row in enumerate(rows):
        missing = [f for f in REQUIRED_FIELDS if f not in row]
        if missing:
            result.problems.append(f"row {n}: missing {missing}")
            break
        if (row["state_alpha"], row["county_code"]) != ("IA", COUNTIES[county]):
            result.problems.append(f"row {n}: not {county} county, Iowa")
            break
        if row["commodity_desc"] != commodity or row["statisticcat_desc"] != statistic:
            result.problems.append(f"row {n}: not {commodity} / {statistic}")
            break
        if not years[0] <= int(row["year"]) <= years[1]:
            result.problems.append(f"row {n}: year {row['year']} outside {years}")
            break
    return result, summary


def _manifest(path: Path, params: dict[str, str], summary: dict) -> Manifest:
    return build_manifest(
        path,
        source_url=public_url(params),
        product="USDA NASS QuickStats API, county survey statistics, JSON",
        version="api_GET",  # QuickStats has no version number; the retrieval date identifies the pull
        retrieval_date=datetime.fromtimestamp(path.stat().st_mtime).date().isoformat(),
        licence=LICENCE,
        subset=subset_record(
            "county", county=params["county_name"], state="IA",
            commodity=params["commodity_desc"], statistic=params["statisticcat_desc"],
            start=int(params["year__GE"]), end=int(params["year__LE"]),
        ),
        evidence_type="survey",
        scale=SCALE,
        notes=(
            f"Raw API response, unchanged: {summary.get('rows')} rows, years {summary.get('years')}, "
            f"{summary.get('suppressed')} withheld values such as (D), kept as returned and made "
            "null in the clean step. County context only, not field yield validation. The key "
            "in the request is shown as a placeholder."
        ),
    )


def plan(base: Path | None = None, fetcher=fetch, pause: float = 1.0, years=YEARS) -> list[Item]:
    """Every county x commodity x statistic, 2003-2025, plus a list of requests with no data."""
    base = Path(base) if base else default_dir()
    base.mkdir(parents=True, exist_ok=True)
    items, empty = [], []
    for county in COUNTIES:
        for commodity in COMMODITIES:
            for statistic in STATISTICS:
                name = f"{county.lower()}_{commodity.lower()}_{statistic.lower().replace(' ', '-')}"
                path = base / f"{name}_{years[0]}-{years[1]}.json"
                params = query_params(county, commodity, statistic, years)
                if not path.exists():  # one good pull is kept and never repeated
                    try:
                        fresh = fetcher(params)
                    except NoDataError:
                        empty.append({"county": county, "commodity": commodity,
                                      "statistic": statistic})
                        time.sleep(pause)
                        continue
                    checks, _ = inspect(fresh, county, commodity, statistic, years)
                    if not checks.ok:  # a rejected response is reported, not cached
                        items.append(_rejected(path.name, checks))
                        time.sleep(pause)
                        continue
                    part = path.with_name(path.name + ".part")
                    part.write_bytes(fresh)
                    part.rename(path)
                    time.sleep(pause)
                checks, summary = inspect(path.read_bytes(), county, commodity, statistic, years)
                items.append(Item(path, _manifest(path, params, summary), checks, SOURCE))
    if empty:
        items.append(_empty_item(base, empty, years))
    check_budget(SOURCE, sum(i.manifest.size_bytes for i in items), BUDGET_BYTES)
    return items


def _rejected(name: str, checks: CheckResult) -> Item:
    placeholder = Manifest(
        source_url="n/a", product="n/a", version="n/a", retrieval_date=date.today().isoformat(),
        sha256="0" * 64, size_bytes=0, licence="n/a", subset={}, evidence_type="assumption",
        scale="n/a", notes="rejected response, not kept",
    )
    return Item(Path(name), placeholder, CheckResult([f"{name}: {p}" for p in checks.problems]), SOURCE)


def _empty_item(base: Path, empty: list[dict], years) -> Item:
    """Requests the API answered with no data, kept so an empty cell is a documented fact."""
    path = base / EMPTY_NAME
    path.write_text(json.dumps({"requests_with_no_data": empty, "years": list(years)}, indent=2) + "\n")
    manifest = build_manifest(
        path, source_url=BASE_URL, product="NASS QuickStats requests that returned no data",
        version="api_GET", retrieval_date=date.today().isoformat(), licence=LICENCE,
        subset=subset_record("county", state="IA", counties=list(COUNTIES), start=years[0],
                             end=years[1]),
        evidence_type="survey", scale=SCALE,
        notes="Written by the DE, not returned by NASS. Each entry is a county, commodity and "
              "statistic with no published county data; it stays empty and is never filled.",
    )
    return Item(path, manifest, CheckResult(), SOURCE)
