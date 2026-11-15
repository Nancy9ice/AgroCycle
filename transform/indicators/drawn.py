"""Prepare weather and soil indicators for a boundary a farmer drew, with DS2's own pipeline.

A drawn boundary is saved with no pre-processed data (`POST /fields/drawn`), so its profile shows weather and soil
as not loaded and its comparison says "not enough evidence". This runs the same steps the 45 demonstration fields
went through, for one drawn field: pull NASA POWER at its centroid and USDA Soil Data Access for its polygon, compute
the indicators with `transform.indicators.runner` unchanged, and write the same CSVs. Nothing in the computation is new.

It is a batch step a person runs, not something the API does when a farmer clicks: the tech-stack rule is that the API
reads curated data only, with no external call at request time.

    uv run python -m transform.indicators.drawn                          # list drawn fields still without indicators
    uv run python -m transform.indicators.drawn --field drawn-ab12cd34   # fetch and compute; loads nothing
    uv run python -m transform.indicators.drawn --field drawn-ab12cd34 --load    # also append that field's rows
    uv run python -m transform.indicators.drawn --boundary FILE.geojson --field-id drawn-test   # no database at all

WHY THE LOAD IS ITS OWN CODE. `field_indicators` and `soil_properties` are one partition each, so the standard loader
(`transform.indicators.load`, `common.load`) replaces the WHOLE table, which would wipe the demonstration fields'
indicators, and it refuses any field that is not in fields.geojson. This appends rows for the one drawn field id only,
refuses if the field already has rows, and never touches another field's rows or the lineage table.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

import pandas as pd
from shapely import wkt as shapely_wkt
from shapely.geometry import shape

from ingest import power, ssurgo
from transform.indicators import runner

DRAWN_PREFIX = "drawn-"
DEFAULT_OUT = runner.REPO_ROOT / "data" / "out" / "drawn"
INDICATOR_TABLE, SOIL_TABLE, LINEAGE_TABLE = "field_indicators", "soil_properties", "indicator_lineage"


class EnrichError(RuntimeError):
    """Something that must stop the run, in words a person can act on."""


def centroid_and_wkt(geometry: dict) -> tuple[float, float, str]:
    """(latitude, longitude, WKT) of a GeoJSON Polygon in WGS 84."""
    geom = shape(geometry)
    if geom.geom_type != "Polygon" or geom.is_empty:
        raise EnrichError(f"A drawn boundary must be one Polygon, got {geom.geom_type}.")
    centre = geom.centroid
    return round(centre.y, 4), round(centre.x, 4), shapely_wkt.dumps(geom, rounding_precision=6)


def fetch_raw(
    field_id: str, geometry: dict, work: Path, fetcher=power.fetch, poster=ssurgo.post, marsden_from=None
) -> None:
    """Pull POWER and Soil Data Access into `work`, in the layout the runner reads (the same keys as S3)."""
    if not field_id.startswith(DRAWN_PREFIX):
        raise EnrichError(f"{field_id!r} is not a drawn field id (they start with {DRAWN_PREFIX!r}).")
    lat, lon, wkt = centroid_and_wkt(geometry)
    power_dir = work / runner.POWER_PREFIX
    ssurgo_dir = work / runner.SSURGO_PREFIX
    power_dir.mkdir(parents=True, exist_ok=True)
    ssurgo_dir.mkdir(parents=True, exist_ok=True)
    start, end = power.FULL_PERIOD

    item = power._point_item(power_dir, field_id, lat, lon, start, end, fetcher, field_id)
    if not item.checks.ok:
        raise EnrichError(f"POWER did not return a usable series: {'; '.join(item.checks.problems)}")

    # The Marsden series is the reference the climate-distance indicator needs. DS2 pinned one pull in S3; use that
    # (`marsden_from`) so a drawn field is judged against the same series as the others, and only pull a fresh one
    # when it is not available, which can differ slightly because POWER is reprocessed.
    marsden = power_dir / f"{power.MARSDEN_SITE['name']}_{start:%Y%m%d}-{end:%Y%m%d}.json"
    if not marsden.exists() and marsden_from is not None:
        marsden.write_text(json.dumps(marsden_from()), encoding="utf-8")
    if not marsden.exists():
        site = power.MARSDEN_SITE
        ref = power._point_item(power_dir, site["name"], site["lat"], site["lon"], start, end, fetcher)
        if not ref.checks.ok:
            raise EnrichError("Could not get the Marsden reference series.")

    ssurgo.pull_field(field_id, wkt, ssurgo_dir, poster)


def compute(field_id: str, work: Path, out: Path) -> dict:
    """DS2's runner, unchanged, over the raw files for this one field. Writes the three CSVs to `out`."""
    return runner.run(runner.RawStore(local=work), [field_id], out=out)


def _count(client, table: str, field_id: str) -> int:
    return int(client.query(f"SELECT count() FROM {table} WHERE field_id = {{f:String}}", parameters={"f": field_id}).result_rows[0][0])


def append_rows(client, out: Path, field_id: str, replace: bool = False) -> dict[str, int]:
    """Append this field's rows, and only this field's. Returns how many rows went into each table."""
    if not field_id.startswith(DRAWN_PREFIX):
        raise EnrichError(f"Refusing to load {field_id!r}: only drawn fields, never a demonstration field.")
    frames = {
        INDICATOR_TABLE: pd.read_csv(out / "field_indicators.csv", dtype=str, keep_default_na=False),
        SOIL_TABLE: pd.read_csv(out / "soil_properties.csv", dtype=str, keep_default_na=False),
    }
    for name, frame in frames.items():
        others = set(frame["field_id"]) - {field_id}
        if others:
            raise EnrichError(f"{name}.csv holds rows for {sorted(others)}; refusing to load anything but {field_id}.")
        if frame.empty:
            raise EnrichError(f"{name}.csv has no rows for {field_id}.")

    existing = {t: _count(client, t, field_id) for t in (INDICATOR_TABLE, SOIL_TABLE)}
    if any(existing.values()):
        if not replace:
            raise EnrichError(f"{field_id} already has rows ({existing}). Run again with --replace to redo only this field.")
        for table in (INDICATOR_TABLE, SOIL_TABLE):
            # A mutation scoped to this one field id; other fields' rows are not touched.
            client.command(f"ALTER TABLE {table} DELETE WHERE field_id = {{f:String}}", parameters={"f": field_id})

    lineage = {r[0] for r in client.query(f"SELECT DISTINCT indicator_id FROM {LINEAGE_TABLE}").result_rows}
    used = set(frames[INDICATOR_TABLE]["indicator_id"]) | set(frames[SOIL_TABLE]["indicator_id"])
    if used - lineage:
        raise EnrichError(f"Indicators with no lineage row, refusing to load: {sorted(used - lineage)}")

    run_id = str(frames[INDICATOR_TABLE]["run_id"].iloc[0])
    inserted = {}
    for table, frame in frames.items():
        frame = frame.copy()
        frame["load_id"] = f"drawn-{run_id}"
        _typed(table, frame)
        client.insert_df(table, frame)
        inserted[table] = len(frame)
    return inserted


def _typed(table: str, frame: pd.DataFrame) -> None:
    """Blank cells are null (never the text "nan"), numbers are numbers: the same rules as the standard loader."""
    numbers = {"field_indicators": ["value"], "soil_properties": ["share_pct", "value_num"]}[table]
    for col in numbers:
        frame[col] = pd.to_numeric(frame[col].replace("", None))
    if table == INDICATOR_TABLE:
        for col in ("window_start", "window_end"):
            parsed = pd.to_datetime(frame[col].replace("", None))
            frame[col] = parsed.dt.date.where(parsed.notna(), None)
        frame["valid_obs"] = pd.to_numeric(frame["valid_obs"].replace("", None)).astype("Int64")
    for col in {"field_indicators": ["unknown_reason"], "soil_properties": ["value_text"]}[table]:
        frame[col] = frame[col].where(frame[col] != "", None)


def pending(client) -> list[tuple[str, dict]]:
    """Drawn fields that have no indicator rows yet."""
    rows = client.query(
        "SELECT field_id, geometry FROM drawn_fields FINAL "
        "WHERE field_id NOT IN (SELECT DISTINCT field_id FROM field_indicators) ORDER BY created_at"
    ).result_rows
    return [(str(r[0]), json.loads(r[1])) for r in rows]


def _client():
    from common.config import clickhouse_client

    return clickhouse_client()


def _marsden_from_s3():
    return runner.RawStore().power(power.MARSDEN_SITE["name"])


def _geometry_from_db(client, field_id: str) -> dict:
    rows = client.query(
        "SELECT geometry FROM drawn_fields FINAL WHERE field_id = {f:String}", parameters={"f": field_id}
    ).result_rows
    if not rows:
        raise EnrichError(f"No drawn field {field_id!r} in the database.")
    return json.loads(rows[0][0])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--field", help="a drawn field id from the database")
    parser.add_argument("--boundary", type=Path, help="a GeoJSON Polygon file; no database is used (needs --field-id)")
    parser.add_argument("--field-id", help="the id to use with --boundary, e.g. drawn-test")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="where the CSVs go")
    parser.add_argument("--load", action="store_true", help="append this field's rows to ClickHouse")
    parser.add_argument("--replace", action="store_true", help="with --load: redo a field that already has rows")
    args = parser.parse_args(argv)

    try:
        if args.boundary:
            if not args.field_id or args.load:
                raise EnrichError("--boundary needs --field-id and cannot be combined with --load (it uses no database).")
            document = json.loads(args.boundary.read_text(encoding="utf-8"))
            geometry = document.get("geometry", document) if document.get("type") == "Feature" else document
            field_id, client = args.field_id, None
        elif args.field:
            client = _client()
            field_id, geometry = args.field, _geometry_from_db(client, args.field)
        else:
            client = _client()
            todo = pending(client)
            print(f"{len(todo)} drawn field(s) without weather and soil:")
            for field_id, geometry in todo:
                lat, lon, _ = centroid_and_wkt(geometry)
                print(f"  {field_id}  centroid {lat}, {lon}")
            print("\nRun again with --field <id> to prepare one. Nothing was fetched or written.")
            return 0

        out = args.out / field_id
        with tempfile.TemporaryDirectory(prefix="drawn-raw-") as tmp:
            work = Path(tmp)
            print(f"{field_id}: pulling NASA POWER (1991 to 2025) and USDA Soil Data Access ...")
            fetch_raw(field_id, geometry, work, marsden_from=_marsden_from_s3)
            if out.exists():
                shutil.rmtree(out)
            result = compute(field_id, work, out)
        manifest = result["manifest"]
        print(f"run {manifest['run_id']}")
        for table, count in manifest["rows"].items():
            print(f"  {table:<22}{count:>6} rows")
        print("  status:", ", ".join(f"{k} {v}" for k, v in sorted(result["indicators"]["status"].value_counts().items())))
        for finding in manifest["soil_table_findings"].get(field_id, []):
            print(f"  soil finding: {finding}")
        print(f"  CSVs in {out}")
        if not args.load:
            print("\nNothing was loaded. Check the CSVs, then re-run with --load to append this field's rows.")
            return 0
        inserted = append_rows(client, out, field_id, replace=args.replace)
        print(f"\nAppended {inserted} for {field_id}. Other fields' rows were not touched.")
        print("The API reads them within five minutes (its lookup cache).")
        return 0
    except EnrichError as error:
        print(f"stopped: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
