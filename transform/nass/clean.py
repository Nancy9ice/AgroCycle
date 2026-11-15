"""Clean the raw NASS QuickStats files into the county_stats frame (Phase 12, DE).

Reads the raw responses exactly as stored (local pull folder, or S3 when absent). A withheld value
such as "(D)" becomes null with value_status "withheld"; nothing is filled, zeroed or interpolated.
Units stay as NASS gives them. Corn grain and corn silage stay separate rows (different units),
and hay keeps its three classes.
"""

import json
from pathlib import Path

import pandas as pd

from common.schemas import COUNTY_STATS

SOURCE_ID = "nass_quickstats"
RAW_PATTERN = "*_2003-2025.json"
S3_PREFIX = "raw/nass/api_GET/"
COLUMNS = list(COUNTY_STATS.columns)


def default_dir() -> Path:
    return Path.home() / "agrocycle_nass"


def parse_value(text: str) -> tuple[float | None, str]:
    """(number, status). Only "(D)" (withheld to avoid disclosing data) is known. Other NASS codes mean
    different things: "(Z)" is less than half the unit shown, "(NA)" is not available, "(S)" is too few
    reports. Calling those "withheld" would be wrong, so they stop the run until each is handled."""
    cleaned = str(text).strip()
    if cleaned == "(D)":
        return None, "withheld"
    if not cleaned or cleaned.startswith("("):
        raise ValueError(f"unhandled NASS value {cleaned!r}: only (D) is mapped; add the code with its meaning")
    return float(cleaned.replace(",", "")), "reported"


def parse_cv(text: str) -> float | None:
    cleaned = str(text).strip()
    return float(cleaned) if cleaned and not cleaned.startswith("(") else None


# The one series the table holds. The unique key leaves these out, so a row from any other series
# (irrigated, a forecast, a monthly period) must stop the run instead of colliding or mixing in.
EXPECTED_SERIES = {
    "source_desc": "SURVEY", "agg_level_desc": "COUNTY", "state_alpha": "IA", "domain_desc": "TOTAL",
    "prodn_practice_desc": "ALL PRODUCTION PRACTICES", "freq_desc": "ANNUAL", "reference_period_desc": "YEAR",
}


def rows_from_response(body: bytes) -> list[dict]:
    out = []
    for r in json.loads(body)["data"]:
        for field, wanted in EXPECTED_SERIES.items():
            if r.get(field) != wanted:
                raise ValueError(f"unexpected NASS series: {field} is {r.get(field)!r}, expected {wanted!r}")
        value, status = parse_value(r["Value"])
        out.append({
            "county": r["county_name"].title(),
            "county_fips": f"{r['state_fips_code']}{r['county_code']}",
            "year": int(r["year"]),
            "commodity": r["commodity_desc"],
            "class_desc": r["class_desc"],
            "utilization": r["util_practice_desc"],
            "statistic": r["statisticcat_desc"],
            "unit": r["unit_desc"],
            "value": value,
            "value_status": status,
            "cv_percent": parse_cv(r.get("CV (%)", "")),
            "short_desc": r["short_desc"],
            "evidence_type": "survey",
            "source_id": SOURCE_ID,
        })
    return out


def build(bodies: list[bytes]) -> pd.DataFrame:
    """The validated county_stats frame from raw response bodies."""
    rows = [row for body in bodies for row in rows_from_response(body)]
    frame = pd.DataFrame(rows, columns=COLUMNS)
    frame = frame.astype({"value": "float64", "cv_percent": "float64"})
    frame = frame.sort_values(["county", "commodity", "class_desc", "utilization", "statistic", "unit", "year"])
    return COUNTY_STATS.validate(frame.reset_index(drop=True))


def read_local(base: Path | None = None) -> list[bytes]:
    base = Path(base) if base else default_dir()
    files = sorted(base.glob(RAW_PATTERN))
    if not files:
        raise RuntimeError(f"no NASS raw files in {base}; run the ingest first")
    return [f.read_bytes() for f in files]


def read_s3(client, bucket: str) -> list[bytes]:
    """Read-only. Every retrieval date under raw/nass/api_GET/, the newest copy of each file.

    A pull spread over several days (a failed run resumed later) is read whole; taking only the newest
    date would silently drop the counties pulled earlier.
    """
    from ingest.s3_store import list_keys

    keys = [o["Key"] for o in list_keys(client, bucket, S3_PREFIX) if o["Key"].endswith("_2003-2025.json")]
    if not keys:
        raise RuntimeError("no NASS raw files in S3")
    newest: dict[str, str] = {}
    for key in sorted(keys, key=lambda k: k.split("/")[3]):  # oldest date first, so the newest wins
        newest[key.rsplit("/", 1)[1]] = key
    return [client.get_object(Bucket=bucket, Key=k)["Body"].read() for _, k in sorted(newest.items())]
