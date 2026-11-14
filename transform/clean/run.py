"""Clean POWER and SSURGO for every field. Dry run unless --load is given.

    uv run python -m transform.clean.run                # clean, check, write local files, print the report
    uv run python -m transform.clean.run --load         # also load climate_points and climate_daily

Reads the Phase 1 pull folders (POWER_DIR and SSURGO_DIR, default ~/agrocycle_power and ~/agrocycle_ssurgo),
and falls back to S3 for a file that is missing there. Outputs go to data/out/clean/ (gitignored): the gap
report, the SSURGO findings, the tidy soil frames and the climate tables. A hard POWER check stops the run;
SSURGO findings are reported and never fixed. `--load` applies new schema/*.sql, then loads the two climate
tables, one at a time (each atomic, the pair not).
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

from common.schemas import TABLES
from transform.clean import power, ssurgo
from transform.clean.sources import MARSDEN_POINT, SSURGO_STEPS, Raw
from transform.field_schema import ROOT, load_fields

OUT_DIR = ROOT / "data" / "out" / "clean"


def gap_report(points: list[power.PointResult]) -> pd.DataFrame:
    """Every date that held the fill value or had no row, per point and variable."""
    rows = []
    for point in points:
        for kind, found in (("fill", point.fill_dates), ("missing", point.missing_dates)):
            for variable, dates in found.items():
                rows += [{"point_id": point.point_id, "variable": variable, "kind": kind, "date": d} for d in dates]
    return pd.DataFrame(rows, columns=["point_id", "variable", "kind", "date"])


def summary(points, cells, report, soils, daily) -> list[str]:
    days = {p.expected_days for p in points}
    soft = {flag: sum(p.soft_flags.get(flag, 0) for p in points) for flag in (power.QC_T_ORDER, power.QC_T_RANGE)}
    findings = [f for s in soils for f in s.findings]
    fills = int((report["kind"] == "fill").sum())
    gaps = int((report["kind"] == "missing").sum())
    lines = [
        (f"POWER: {len(points)} points ({len(points) - 1} fields and {MARSDEN_POINT}), "
         f"{', '.join(str(d) for d in sorted(days))} days x {len(power.VARIABLES)} variables each, {cells} distinct cells"),
        f"  fill values turned to null: {fills}; dates missing from the response: {gaps}; soft flags: {soft}",
        f"  climate_daily rows: {len(daily)}",
        (f"SSURGO: {len(soils)} fields, {sum(len(s.map_units) for s in soils)} map units, "
         f"{sum(len(s.components) for s in soils)} components, {sum(len(s.horizons) for s in soils)} horizons; "
         f"findings: {len(findings)}"),
    ]
    lines += [f"  - {f}" for f in findings[:20]]
    if not report.empty:
        lines.append("  gap report: " + "; ".join(
            f"{r.point_id} {r.variable} {r.kind} {r.date}" for r in report.head(12).itertuples()))
    return lines


def load_tables(points_table: pd.DataFrame, daily: pd.DataFrame) -> None:
    from common.config import clickhouse_client
    from common.load import load
    from common.migrate import migrate

    for table, frame in (("climate_points", points_table), ("climate_daily", daily)):
        TABLES[table].schema.validate(frame)  # both frames are checked before any table is touched
    client = clickhouse_client()
    applied = migrate(client)
    if applied:
        print("applied: " + ", ".join(applied))
    for table, frame in (("climate_points", points_table), ("climate_daily", daily)):
        result = load(client, table, frame)
        print(f"loaded {table}: {result.rows} rows, run {result.load_id}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--power-dir", type=Path, help="the POWER pull folder (default POWER_DIR or ~/agrocycle_power)")
    parser.add_argument("--ssurgo-dir", type=Path, help="the SSURGO pull folder (default SSURGO_DIR or ~/agrocycle_ssurgo)")
    parser.add_argument("--out", type=Path, default=OUT_DIR, help="folder for the local outputs")
    parser.add_argument("--load", action="store_true", help="load into ClickHouse (default: dry run)")
    args = parser.parse_args(argv)
    raw = Raw(args.power_dir, args.ssurgo_dir)
    try:
        field_ids = list(load_fields()["field_id"])
        points = [power.clean_point(raw.power(p), p) for p in [*field_ids, MARSDEN_POINT]]
        soils = [ssurgo.clean_field(f, *(raw.ssurgo(f, step) for step in SSURGO_STEPS)) for f in field_ids]
    except (ValueError, RuntimeError, OSError) as err:  # a hard POWER check, a bad file, a missing folder
        print(f"clean: {err}")
        return 1
    points_table, daily = power.group_cells(points)
    report = gap_report(points)

    args.out.mkdir(parents=True, exist_ok=True)
    report.to_csv(args.out / "power_gap_report.csv", index=False)
    points_table.to_csv(args.out / "climate_points.csv", index=False)
    daily.to_parquet(args.out / "climate_daily.parquet", index=False)
    for name in ("map_units", "components", "horizons"):
        pd.concat([getattr(s, name).assign(field_id=s.field_id) if name != "map_units" else s.map_units for s in soils]
                  ).to_csv(args.out / f"ssurgo_{name}.csv", index=False)
    (args.out / "ssurgo_findings.txt").write_text("\n".join(f for s in soils for f in s.findings) + "\n")

    print("\n".join(summary(points, points_table["cell_id"].nunique(), report, soils, daily)))
    if args.load:
        load_tables(points_table, daily)
    else:
        print("dry run: nothing loaded (use --load)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
