"""Comprehensive Phase 5 script - reads from ClickHouse, writes to ClickHouse."""
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
from transform.hls.mask import TILE_CRS, masked_reflectance
from transform.hls.sources import S3Source, Window

ROOT = Path(__file__).resolve().parents[2]


def ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    denom = nir + red
    result = np.full_like(nir, np.nan, dtype=np.float32)
    valid = ~np.isnan(nir) & ~np.isnan(red) & (denom != 0)
    result[valid] = (nir[valid] - red[valid]) / denom[valid]
    return result


def compute_ndvi_for_field(field_id: str, windows: list[Window], source: S3Source) -> list[dict]:
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
            "acquired": pd.Timestamp(w.acquired),
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
                    "field_id": field_id, "year": year,
                    "bare_window_start": pd.Timestamp(bare_start.date()),
                    "bare_window_end": pd.Timestamp(date_val.date()),
                    "bare_days": bare_days,
                    "ndvi_before": float("nan"), "ndvi_after": round(ndvi_val, 4),
                    "confidence": "high",
                })
            elif bare_days >= 14:
                bare_periods.append({
                    "field_id": field_id, "year": year,
                    "bare_window_start": pd.Timestamp(bare_start.date()),
                    "bare_window_end": pd.Timestamp(date_val.date()),
                    "bare_days": bare_days,
                    "ndvi_before": float("nan"), "ndvi_after": round(ndvi_val, 4),
                    "confidence": "low",
                })
    return bare_periods


def hls_vs_cdl_test(ndvi_df: pd.DataFrame, cdl_df: pd.DataFrame) -> dict:
    if ndvi_df.empty or cdl_df.empty:
        return {"conclusion": "insufficient_data"}
    merged = ndvi_df.copy()
    merged["year"] = pd.to_datetime(merged["acquired"]).dt.year
    cdl_df["year"] = cdl_df["year"].astype(int)
    merged = merged.merge(cdl_df[["field_id", "year", "dominant_group"]], on=["field_id", "year"])
    merged = merged[merged["dominant_group"].isin(["corn", "soybean"])]
    if len(merged) < 10:
        return {"conclusion": "insufficient_data", "n_comparisons": len(merged)}
    corn = merged[merged["dominant_group"] == "corn"]["ndvi_mean"]
    soy = merged[merged["dominant_group"] == "soybean"]["ndvi_mean"]
    if len(corn) < 3 or len(soy) < 3:
        return {"conclusion": "insufficient_data"}
    diff = abs(float(corn.mean()) - float(soy.mean()))
    return {
        "conclusion": "adds_value" if diff > 0.05 else "no_clear_difference",
        "corn_mean_ndvi": round(float(corn.mean()), 4),
        "soy_mean_ndvi": round(float(soy.mean()), 4),
        "ndvi_difference": round(diff, 4),
        "n_corn_obs": len(corn),
        "n_soy_obs": len(soy),
        "n_fields": int(merged["field_id"].nunique()),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--sample", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    print("Phase 5: HLS vegetation features")
    print("=" * 60)

    # 1. Connect
    client = clickhouse_client()
    print("\n1. Reading hls_valid_pixels...")
    counts_df = client.query_df("SELECT * FROM hls_valid_pixels ORDER BY field_id, acquired")
    print(f"   {len(counts_df)} windows loaded")
    if args.sample:
        sample_fields = counts_df["field_id"].unique()[:args.sample]
        counts_df = counts_df[counts_df["field_id"].isin(sample_fields)]
        print(f"   Sample: {list(sample_fields)}")

    # 2. Fields
    print("\n2. Loading field polygons...")
    fields = load_fields().to_crs(TILE_CRS)
    polygons = dict(zip(fields["field_id"], fields.geometry, strict=False))  # noqa: F841

    # 3. HLS windows from S3
    print("\n3. Loading HLS windows from S3...")
    source = S3Source(s3_client(), s3_bucket())
    all_windows = source.windows()
    field_ids = set(counts_df["field_id"].unique())
    windows_by_field = {}
    for w in all_windows:
        if w.field_id in field_ids:
            windows_by_field.setdefault(w.field_id, []).append(w)
    print(f"   {len(windows_by_field)} fields")

    # 4. NDVI
    print("\n4. Computing NDVI...")
    all_ndvi, all_bare = [], []
    fc = 0
    for fid in sorted(field_ids):
        fw = windows_by_field.get(fid, [])
        if not fw:
            continue
        nr = compute_ndvi_for_field(fid, fw, source)
        all_ndvi.extend(nr)
        all_bare.extend(find_bare_windows(nr, fid))
        fc += 1
        if fc % 10 == 0:
            print(f"   {fc}/{len(field_ids)} fields (NDVI={len(all_ndvi)}, bare={len(all_bare)})")

    ndvi_df = pd.DataFrame(all_ndvi)
    bare_df = pd.DataFrame(all_bare)
    print(f"\n   NDVI: {len(ndvi_df)} rows, fields: {ndvi_df['field_id'].nunique() if not ndvi_df.empty else 0}")
    print(f"   Bare windows: {len(bare_df)}")

    # 5. HLS-vs-CDL test
    print("\n5. HLS vs CDL value test...")
    vt = {"conclusion": "no_cdl_data"}
    try:
        cdl_df = client.query_df("SELECT * FROM crop_history")
        if not cdl_df.empty:
            vt = hls_vs_cdl_test(ndvi_df, cdl_df)
            print(f"   Conclusion: {vt['conclusion']}")
        else:
            print("   crop_history table is empty")
    except Exception as e:
        print(f"   Could not read crop_history: {e}")

    # 6. Load to ClickHouse
    action = "DRY RUN" if args.dry_run else "LOADING"
    print(f"\n6. {action} into ClickHouse...")
    if not args.dry_run:
        try:
            applied = migrate(client)
            if applied:
                print(f"   Applied: {', '.join(applied)}")
            if not ndvi_df.empty:
                r = load(client, "hls_ndvi", ndvi_df)
                print(f"   hls_ndvi: {r.rows} rows")
            if not bare_df.empty:
                r = load(client, "hls_bare_windows", bare_df)
                print(f"   hls_bare_windows: {r.rows} rows")
            print("\n   Frontend can now read: hls_ndvi, hls_bare_windows")
        except Exception as e:
            print(f"   LOAD ERROR: {e}")
            return 1
    else:
        print(f"   Would load {len(ndvi_df)} NDVI rows, {len(bare_df)} bare windows")

    print("\nDone!")
    return 0


if __name__ == "__main__":
    sys.exit(main())