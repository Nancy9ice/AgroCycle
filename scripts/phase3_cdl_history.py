"""Phase 3: Compute CDL crop history for all 45 fields.
Downloads county CDL clips from S3, clips to each field polygon,
computes dominant crop per year using the 60% threshold rule,
and produces the crop history table.

Usage: uv run python scripts/phase3_cdl_history.py
"""
import os
import sys
from pathlib import Path

import boto3
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask as rio_mask

# --- Config --------------------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "data" / "out" / "phase3"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Load credentials
with open(REPO_ROOT / ".env") as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()

S3_BUCKET = "agrocycle-fieldshift-2026-data"
CDL_PREFIX = "raw/cdl/annual-30m-website-export/2026-11-14/"
COUNTY_FIPS = {"Story": "19169", "Boone": "19015"}

# CDL class-code groups (from cdl-crop-rules.md v1.0)
CORN_CODES = {1, 12, 13, 225, 226}
SOY_CODES = {5, 26, 239, 240}
PASTURE_CODES = {176, 37, 58, 59}
OATS_CODES = {28}
ALFALFA_CODES = {36}
YEARS = list(range(2015, 2026))
DOMINANT_THRESHOLD = 0.60

s3 = boto3.client("s3", region_name=os.environ["AWS_REGION"])


def download_s3(key, local):
    if not local.exists():
        print(f"    Downloading {key}...")
        try:
            s3.download_file(S3_BUCKET, key, str(local))
        except Exception as e:
            print(f"    FAILED: {e}")
            return None
    return local


def classify_pixel(value):
    if value in CORN_CODES:
        return "corn"
    elif value in SOY_CODES:
        return "soybean"
    elif value in PASTURE_CODES:
        return "pasture"
    elif value in OATS_CODES:
        return "oats"
    elif value in ALFALFA_CODES:
        return "alfalfa"
    elif value == 0:
        return "no_data"
    else:
        return "other"


def compute_dominant_crop(counts):
    total_valid = sum(counts.values())
    if total_valid == 0:
        return "no_data", 0.0, True
    top_class, top_count = max(counts.items(), key=lambda x: x[1])
    top_pct = top_count / total_valid
    if top_pct >= DOMINANT_THRESHOLD:
        return top_class, round(top_pct * 100, 1), False
    else:
        return "mixed", round(top_pct * 100, 1), True


def process_field(field_id, county, geometry):
    """Process one field across all years."""
    fips = COUNTY_FIPS[county]
    rows = []
    
    for year in YEARS:
        cdl_key = f"{CDL_PREFIX}CDL_{year}_{fips}.tif"
        cdl_local = REPO_ROOT / "data" / "tmp" / f"CDL_{year}_{fips}.tif"
        cdl_local.parent.mkdir(parents=True, exist_ok=True)
        download_s3(cdl_key, cdl_local)
        
        with rasterio.open(cdl_local) as src:
            try:
                out_image, _ = rio_mask(src, [geometry], crop=True, all_touched=True)
            except (ValueError, Exception) as e:
                print(f"    Skipping {year}: {e}")
                continue
        
        data = out_image[0]
        valid = data[data > 0]
        
        if len(valid) == 0:
            rows.append({
                "field_id": field_id, "year": year, "county": county,
                "valid_pixels": 0, "corn_pct": 0, "soybean_pct": 0,
                "pasture_pct": 0, "oats_pct": 0, "alfalfa_pct": 0,
                "other_crop_pct": 0, "dominant_crop": "no_data",
                "dominant_pct": 0.0, "is_mixed": True,
            })
            continue
        
        # Count by class
        counts = {}
        for v in np.unique(valid):
            c = classify_pixel(int(v))
            counts[c] = counts.get(c, 0) + int(np.sum(valid == v))
        
        total = len(valid)
        dominant, dom_pct, is_mixed = compute_dominant_crop(counts)
        
        rows.append({
            "field_id": field_id,
            "year": year,
            "county": county,
            "valid_pixels": total,
            "corn_pct": round(counts.get("corn", 0) / total * 100, 1),
            "soybean_pct": round(counts.get("soybean", 0) / total * 100, 1),
            "pasture_pct": round(counts.get("pasture", 0) / total * 100, 1),
            "oats_pct": round(counts.get("oats", 0) / total * 100, 1),
            "alfalfa_pct": round(counts.get("alfalfa", 0) / total * 100, 1),
            "other_crop_pct": round(counts.get("other", 0) / total * 100, 1),
            "dominant_crop": dominant,
            "dominant_pct": dom_pct,
            "is_mixed": is_mixed,
        })
    
    return rows


def classify_rotation(seq):
    """Classify 11-year crop sequence into rotation type."""
    corn_years = seq.count("C")
    soy_years = seq.count("S")
    pasture_years = seq.count("P")
    
    alt_count = sum(
        1 for i in range(len(seq) - 1)
        if (seq[i] == "C" and seq[i+1] == "S") or (seq[i] == "S" and seq[i+1] == "C")
    )
    
    if alt_count >= 7:
        return "rotation"
    elif corn_years >= 8:
        return "continuous_corn"
    elif pasture_years >= 8:
        return "pasture_hay"
    elif corn_years + soy_years >= 5:
        return "mixed"
    else:
        return "other"


def main():
    print("=" * 60)
    print("Phase 3: CDL Crop History Computation")
    print("=" * 60)
    
    # Load fields
    fields_path = REPO_ROOT / "data" / "fields" / "fields.geojson"
    print(f"\nLoading fields from {fields_path}")
    fields_gdf = gpd.read_file(fields_path)
    print(f"  {len(fields_gdf)} fields loaded\n")
    
    # Process each field
    all_rows = []
    for idx, row in fields_gdf.iterrows():
        fid = row["field_id"]
        print(f"[{idx+1}/45] {fid} ({row['county']})...")
        geometry = row.geometry
        result = process_field(fid, row["county"], geometry)
        all_rows.extend(result)
        print(f"  -> {len(result)} years processed")
    
    # Build DataFrame
    df = pd.DataFrame(all_rows)
    
    # Add one-letter codes
    shorthand = {"corn": "C", "soybean": "S", "pasture": "P", "mixed": "M",
                 "oats": "O", "alfalfa": "A", "other": "X", "no_data": "N"}
    df["code"] = df["dominant_crop"].map(lambda x: shorthand.get(x, "?"))
    
    # Build sequence per field and classify rotation
    summaries = []
    for fid in sorted(df["field_id"].unique()):
        fdf = df[df["field_id"] == fid].sort_values("year")
        seq = "".join(fdf["code"].values)
        cls = classify_rotation(seq)
        
        row_info = fields_gdf[fields_gdf["field_id"] == fid].iloc[0]
        summaries.append({
            "field_id": fid,
            "county": row_info["county"],
            "role": row_info["role"],
            "domain_note": row_info.get("domain_note", ""),
            "crop_sequence": seq,
            "rotation_class": cls,
            "corn_years": seq.count("C"),
            "soybean_years": seq.count("S"),
            "pasture_years": seq.count("P"),
            "mixed_years": seq.count("M"),
        })
    
    df_seq = pd.DataFrame(summaries)
    
    # Save
    csv_path = OUT_DIR / "cdl_crop_history.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nSaved per-year history: {csv_path}")
    
    seq_path = OUT_DIR / "cdl_rotation_summary.csv"
    df_seq.to_csv(seq_path, index=False)
    print(f"Saved rotation summary: {seq_path}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("ROTATION CLASSIFICATION SUMMARY")
    print("=" * 60)
    for cls in ["rotation", "continuous_corn", "pasture_hay", "mixed", "other"]:
        subset = df_seq[df_seq["rotation_class"] == cls]
        if len(subset) > 0:
            print(f"\n{cls} ({len(subset)} fields):")
            for _, r in subset.iterrows():
                print(f"  {r['field_id']:20s} seq={r['crop_sequence']}")
    
    print(f"\nTotal: {len(df_seq)} fields")
    
    # Compare with DE's labels
    print("\n" + "=" * 60)
    print("COMPARISON WITH DE'S LABELS (from field_selection_notes.csv)")
    print("=" * 60)
    notes_path = REPO_ROOT / "data" / "fields" / "field_selection_notes.csv"
    if notes_path.exists():
        notes = pd.read_csv(notes_path)
        merged = df_seq.merge(notes, on="field_id", suffixes=("_ds1", "_de"))
        mismatches = merged[merged["rotation_class"] != merged["cdl_class"]]
        if len(mismatches) > 0:
            print(f"\nMismatches ({len(mismatches)} fields):")
            for _, r in mismatches.iterrows():
                print(f"  {r['field_id']:20s} DS1={r['rotation_class']:20s} DE={r['cdl_class']:20s} seq={r['crop_sequence']}")
        else:
            print("\nAll field classifications match the DE's labels. ✓")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())