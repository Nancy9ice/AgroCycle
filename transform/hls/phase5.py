"""Phase 5: HLS vegetation features (NDVI, bare-field windows, HLS-vs-CDL test).

Reads the hls_valid_pixels table from ClickHouse, reads HLS stacks from S3,
computes NDVI, finds bare-field windows, and tests whether HLS adds value beyond CDL.
Loads all results into ClickHouse tables that the frontend reads from.

Usage (from Codespaces, after .env is set up):
    uv run python -m transform.hls.phase5 --sample 5    # process only 5 fields for testing
    uv run python -m transform.hls.phase5                 # full run
    uv run python -m transform.hls.phase5 --dry-run       # see what would be loaded without writing
"""
from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from common.config import clickhouse_client, s3_bucket, s3_client
from common.load import load
from common.migrate import migrate
from transform.field_schema import load_fields
from transform.hls.sources import S3Source, Window
from transform.hls.mask import TILE_CRS, masked_reflectance

ROOT = Path(__file__).resolve().parents[2]

NDVI_COLS = [
    "field_id", "sensor", "acquired", "sensing_time",
    "ndvi_mean", "ndvi_median", "ndvi_p25", "ndvi_p75", "ndvi_std",
    "ndvi_valid_pixels", "valid_share",
    "n_clear_pixels",
]
BARE_WINDOW_COLS = [
    "field_id", "year",
    "bare_window_start", "bare_window_end", "bare_days",
    "ndvi_before", "ndvi_after", "confidence",
]
VALUE_TEST_COLS = [
    "conclusion", "corn_mean_ndvi", "soy_mean_ndvi",
    "ndvi_difference", "n_corn_obs", "n_soy_obs", "n_fields",
]


def ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    """NDVI = (NIR - Red) / (NIR + Red)."""
    denom = nir + red
    result = np.full_like(nir, np.nan, dtype=np.float32)
    valid = ~np.isnan(nir) & ~np.isnan(red) & (denom != 0)
    result[valid] = (nir[valid] - red[valid]) / denom[valid]
    return result


def compute_ndvi_for_field(
    field_id: str,
    windows: list[Window],
    source: S3Source,
) -> list[dict]:
    rows = []
    for w in windows:
        try:
            ms = masked_reflectance(source.read(w))
        except Exception:
            continue

        red = ms.reflectance[0]
        nir = ms.reflectance[1]

        valid_mask = ms.classes.valid & ms.inside & ~np.isnan(red) & ~np.isnan(nir)
        n_valid = int(valid_mask.sum())

        if n_valid == 0:
            continue

        ndvi_vals = ndvi(nir, red)
        valid_ndvi = ndvi_vals[valid_mask]
        total_inside = int(ms.inside.sum())

        rows.append({
            "field_id": field_id,
            "sensor": w.sensor,
            "acquired": w.acquired.isoformat(),
            "sensing_time": w.sensing_time,
            "ndvi_mean": float(np.nanmean(valid_ndvi)),
            "ndvi_median": float(np.nanmedian(valid_ndvi)),
            "ndvi_p25": float(np.percentile(valid_ndvi, 25)),
            "ndvi_p75": float(np.percentile(valid_ndvi, 75)),
            "ndvi_std": float(np.nanstd(valid_ndvi)),
            "ndvi_valid_pixels": n_valid,
            "valid_share": round(n_valid / total_inside, 3) if total_inside > 0 else 0.0,
            "n_clear_pixels": n_valid,
        })
    return rows


def find_bare_windows(ndvi_rows: list[dict], field_id: str) -> list[dict]:
    """Find bare-field windows: periods when NDVI < 0.3 for >= 14 consecutive days."""
    if not ndvi_rows:
        return []

    df = pd.DataFrame(ndvi_rows)
    df["acquired"] = pd.to_datetime(df["acquired"])
    df = df.sort_values("acquired")

    bare_periods = []
    in_bare = False
    bare_start = None
    years_done = set()

    for _, row in df.iterrows():
        ndvi_val = row["ndvi_mean"]
        date_val = row["acquired"]
        year = date_val.year

        is_bare = ndvi_val < 0.3

        if is_bare and not in_bare:
            in_bare = True
            bare_start = date_val
        elif not is_bare and in_bare:
            in_bare = False
            bare_days = (date_val - bare_start).days
            if bare_days >= 14 and year not in years_done:
                years_done.add(year)
                bare_periods.append({
                    "field_id": field_id,
                    "year": year,
                    "bare_window_start": bare_start.date().isoformat(),
                    "bare_window_end": date_val.date().isoformat(),
                    "bare_days": bare_days,
                    "ndvi_before": None,
                    "ndvi_after": round(ndvi_val, 4),
                    "confidence": "high",
                })
            elif bare_days >= 14:
                bare_periods.append({
                    "field_id": field_id,
                    "year": year,
                    "bare_window_start": bare_start.date().isoformat(),
                    "bare_window_end": date_val.date().isoformat(),
                    "bare_days": bare_days,
                    "ndvi_before": None,
                    "ndvi_after": round(ndvi_val, 4),
                    "confidence": "low",
                })

    return bare_periods


def hls_vs_cdl_test(ndvi_df: pd.DataFrame, cdl_history: pd.DataFrame) -> dict:
    """Test whether HLS NDVI adds value beyond CDL crop labels."""
    if ndvi_df.empty or cdl_history.empty:
        return {"conclusion": "insufficient_data"}

    merged = ndvi_df.copy()
    merged["year"] = pd.to_datetime(merged["acquired"]).dt.year
    merged = merged.merge(
        cdl_history[["field_id", "year", "dominant_crop"]],
        on=["field_id", "year"],
    )
    merged = merged[merged["dominant_crop"].isin(["corn", "soybean"])]

    if len(merged) < 10:
        return {"conclusion": "insufficient_data", "n_comparisons": len(merged)}

    corn = merged[merged["dominant_crop"] == "corn"]["ndvi_mean"]
    soy = merged[merged["dominant_crop"] == "soybean"]["ndvi_mean"]

    if len(corn) < 3 or len(soy) < 3:
        return {"conclusion": "insufficient_data"}

    corn_mean = float(corn.mean())
    soy_mean = float(soy.mean())
    diff = abs(corn_mean - soy_mean)

    return {
        "conclusion": "adds_value" if diff > 0.05 else "no_clear_difference",
        "corn_mean_ndvi": round(corn_mean, 4),
        "soy_mean_ndvi": round(soy_mean, 4),
        "ndvi_difference": round(diff, 4),
        "n_corn_obs": len(corn),
        "n_soy_obs": len(soy),
        "n_fields": int(merged["field_id"].nunique()),
    }


def load_result(client, table_name: str, df: pd.DataFrame, load_desc: str) -> None:
    """Load a DataFrame into a ClickHouse table if not --dry-run."""
    if not df.empty:
        result = load(client, table_name, df)
        print(f"   Loaded {load_desc}: {result.rows} rows, load_id={result.load_id}")
    else:
        print(f"   {load_desc}: no rows to load")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--sample", type=int, default=0,
                        help="process only N fields (for testing)")
    parser.add_argument("--dry-run", action="store_true",
                        help="process but do not load into ClickHouse")
    args = parser.parse_args(argv)

    print("Phase 5: HLS vegetation features")
    print("=" * 60)

    # 1. Connect to ClickHouse
    client = clickhouse_client()
    print(f"\n1. Reading hls_valid_pixels from ClickHouse...")
    counts_df = client.query_df("SELECT * FROM hls_valid_pixels ORDER BY field_id, acquired")
    print(f"   {len(counts_df)} windows loaded")

    if args.sample:
        sample_fields = counts_df["field_id"].unique()[:args.sample]
        counts_df = counts_df[counts_df["field_id"].isin(sample_fields)]
        print(f"   Limited to {args.sample} fields: {list(sample_fields)}")

    # 2. Field polygons
    print(f"\n2. Loading field polygons...")
    fields = load_fields().to_crs(TILE_CRS)
    polygons = dict(zip(fields["field_id"], fields.geometry, strict=False))
    print(f"   {len(polygons)} field polygons loaded")

    # 3. Build windows from S3
    print(f"\n3. Loading HLS windows from S3...")
    source = S3Source(s3_client(), s3_bucket())
    all_windows = source.windows()
    print(f"   {len(all_windows)} windows in S3")

    field_ids = set(counts_df["field_id"].unique())
    windows_by_field: dict[str, list[Window]] = {}
    for w in all_windows:
        if w.field_id in field_ids:
            windows_by_field.setdefault(w.field_id, []).append(w)
    print(f"   Grouped for {len(windows_by_field)} fields")

    # 4. Compute NDVI per field
    print(f"\n4. Computing NDVI from masked reflectance...")
    all_ndvi = []
    all_bare_windows = []
    field_count = 0

    for fid in sorted(field_ids):
        f_windows = windows_by_field.get(fid, [])
        if not f_windows:
            continue

        ndvi_rows = compute_ndvi_for_field(fid, f_windows, source)
        all_ndvi.extend(ndvi_rows)
        bare_rows = find_bare_windows(ndvi_rows, fid)
        all_bare_windows.extend(bare_rows)

        field_count += 1
        if field_count % 10 == 0:
            print(f"   {field_count}/{len(field_ids)} fields "
                  f"(NDVI={len(all_ndvi)}, bare={len(all_bare_windows)})")

    ndvi_df = pd.DataFrame(all_ndvi)
    bare_df = pd.DataFrame(all_bare_windows)
    print(f"\n   NDVI: {len(ndvi_df)} rows across {field_count} fields")
    print(f"   Bare-field windows: {len(bare_df)} windows")

    # 5. HLS-vs-CDL value test
    print(f"\n5. HLS vs CDL value test...")
    value_test = {"test_run": True}
    cdl_path = ROOT / "data" / "out" / "phase3" / "cdl_crop_history.csv"
    if cdl_path.exists():
        cdl_history = pd.read_csv(cdl_path)
        value_test = hls_vs_cdl_test(ndvi_df, cdl_history)
        print(f"   Conclusion: {value_test['conclusion']}")
        if "ndvi_difference" in value_test:
            print(f"   Corn mean NDVI: {value_test['corn_mean_ndvi']}")
            print(f"   Soy mean NDVI: {value_test['soy_mean_ndvi']}")
            print(f"   Difference: {value_test['ndvi_difference']}")
    else:
        print(f"   No CDL history found at {cdl_path}")

    # 6. Write to ClickHouse
    action = "DRY RUN" if args.dry_run else "LOADING"
    print(f"\n6. {action} into ClickHouse...")

    if not args.dry_run:
        try:
            # Migrate first (apply any new table schemas)
            applied = migrate(client)
            if applied:
                print(f"   Applied migrations: {', '.join(applied)}")

            # Load NDVI table
            load_result(client, "hls_ndvi", ndvi_df, "hls_ndvi")

            # Load bare windows table
            load_result(client, "hls_bare_windows", bare_df, "hls_bare_windows")

            # Load value test result as a single row
            if value_test.get("test_run"):
                vt_df = pd.DataFrame([value_test])
                load_result(client, "hls_value_test", vt_df, "hls_value_test")

            print(f"\n   All data loaded into ClickHouse. Frontend can now read:")
            print(f"     - hls_ndvi: per-field NDVI time series")
            print(f"     - hls_bare_windows: bare-field windows per year")
            print(f"     - hls_value_test: whether HLS adds value beyond CDL")
        except Exception as e:
            print(f"   LOAD ERROR: {e}")
            return 1
    else:
        print(f"   Would load {len(ndvi_df)} NDVI rows")
        print(f"   Would load {len(bare_df)} bare window rows")
        if "conclusion" in value_test:
            print(f"   Would load value test: {value_test['conclusion']}")

    print("\nDone!")
    return 0


if __name__ == "__main__":
    sys.exit(main())