"""CDL confusion matrix: compare crop classifications across years for consistency.

What this checks:
- Year-to-year consistency: does a field labelled "corn" in 2023 also show "corn" in 2024?
- Dominant crop stability: do fields keep the same dominant crop across consecutive years?
- Anomalous transitions: corn->pasture or soybean->urban are suspicious and get flagged.

Usage: uv run python scripts/cdl_confusion_matrix.py
"""
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask as rio_mask

REPO_ROOT = Path(".")
tmp = REPO_ROOT / "data" / "tmp"
OUT_DIR = REPO_ROOT / "data" / "out" / "phase3"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CORN_CODES = {1, 12, 13, 225, 226}
SOY_CODES = {5, 26, 239, 240}
PASTURE_CODES = {176, 37, 58, 59}

def classify(v):
    if v in CORN_CODES: return "corn"
    if v in SOY_CODES: return "soybean"
    if v in PASTURE_CODES: return "pasture"
    if v==0: return "no_data"
    return "other"

def pixel_counts(data):
    """Count pixels per class for one clipped field."""
    valid = data[data>0]
    if len(valid)==0: return {}
    counts = {}
    for v in np.unique(valid):
        c = classify(int(v))
        counts[c] = counts.get(c,0) + int(np.sum(valid==v))
    return counts

def main():
    print("CDL Confusion Matrix")
    print("="*60)
    
    # Load fields
    fields = gpd.read_file("data/fields/fields.geojson")
    print(f"Loaded {len(fields)} fields")
    
    # Process all available years
    all_pixel_data = {}  # field_id -> {year -> {class: count}}
    
    for idx, field in fields.iterrows():
        fid = field["field_id"]
        county = field["county"]
        fips = "19015" if county=="Boone" else "19169"
        all_pixel_data[fid] = {}
        
        for year in range(2015, 2026):
            tif = tmp / f"CDL_{year}_{fips}.tif"
            if not tif.exists():
                continue
            
            with rasterio.open(tif) as src:
                field_5070 = fields.iloc[[idx]].to_crs(src.crs)
                geom = field_5070.geometry.iloc[0]
                try:
                    out_img, _ = rio_mask(src, [geom], crop=True, all_touched=True)
                except (ValueError, Exception):
                    continue
            
            counts = pixel_counts(out_img[0])
            if counts:
                all_pixel_data[fid][year] = counts
    
    # ---- 1. Year-to-year dominant crop transitions ----
    print("\n--- Year-to-Year Crop Transitions (all fields) ---")
    
    transitions = {}  # (year_n, crop_n, year_n1, crop_n1) -> count
    field_years = 0
    consistent = 0
    
    for fid, years in all_pixel_data.items():
        sorted_years = sorted(years.keys())
        for i in range(len(sorted_years)-1):
            y1 = sorted_years[i]
            y2 = sorted_years[i+1]
            c1 = max(years[y1], key=years[y1].get)
            c2 = max(years[y2], key=years[y2].get)
            field_years += 1
            
            key = (y1, c1, y2, c2)
            transitions[key] = transitions.get(key, 0) + 1
            
            if c1 == c2:
                consistent += 1
    
    # Build confusion matrix
    classes = ["corn", "soybean", "pasture", "mixed", "other"]
    matrix = pd.DataFrame(0, index=classes, columns=classes)
    
    for (y1, c1, y2, c2), count in transitions.items():
        if c1 in matrix.index and c2 in matrix.columns:
            matrix.loc[c1, c2] += count
    
    print(f"\nTransition count: {field_years} field-year pairs")
    print(f"Consistent (same crop next year): {consistent} ({consistent/max(field_years,1)*100:.1f}%)")
    print("\nConfusion Matrix (rows = year N, cols = year N+1):")
    print(matrix.to_string())
    
    # ---- 2. Anomalous transitions ----
    print("\n--- Anomalous Transitions ---")
    anomalous = []
    for fid, years in all_pixel_data.items():
        sorted_years = sorted(years.keys())
        for i in range(len(sorted_years)-1):
            y1 = sorted_years[i]
            y2 = sorted_years[i+1]
            c1 = max(years[y1], key=years[y1].get)
            c2 = max(years[y2], key=years[y2].get)
            
            # Suspicious: corn->pasture, pasture->corn, soybean->pasture, pasture->soybean
            if (c1=="corn" and c2=="pasture") or (c1=="pasture" and c2=="corn") or \
               (c1=="soybean" and c2=="pasture") or (c1=="pasture" and c2=="soybean"):
                anomalous.append((fid, y1, c1, y2, c2))
    
    if anomalous:
        print(f"Found {len(anomalous)} anomalous transitions:")
        for fid, y1, c1, y2, c2 in anomalous[:20]:
            print(f"  {fid:20s} {y1} {c1:8s} -> {y2} {c2}")
    else:
        print("No anomalous transitions found.")
    
    # ---- 3. Dominant crop stability per field ----
    print("\n--- Dominant Crop Per Field (overview) ---")
    stability_rows = []
    for fid, years in all_pixel_data.items():
        sorted_years = sorted(years.keys())
        doms = [max(years[y], key=years[y].get) for y in sorted_years]
        unique_doms = set(doms)
        
        # Top-1 consistency: percentage of years the most common crop appears
        top_crop = max(unique_doms, key=lambda c: doms.count(c))
        top_pct = doms.count(top_crop) / len(doms) * 100 if doms else 0
        
        stability_rows.append({
            "field_id": fid,
            "years_available": len(doms),
            "dominant_crops": "/".join(sorted(unique_doms)),
            "top_crop": top_crop,
            "top_crop_pct": round(top_pct, 1),
            "n_unique_crops": len(unique_doms),
            "crop_sequence": "".join(d[0].upper() for d in doms),
        })
    
    df_stability = pd.DataFrame(stability_rows)
    
    print("\nFields by number of unique dominant crops:")
    print(df_stability["n_unique_crops"].value_counts().sort_index().to_string())
    
    print("\nFields where top crop appears < 80% of years (potential issues):")
    flagged = df_stability[df_stability["top_crop_pct"] < 80]
    if len(flagged) > 0:
        for _, r in flagged.iterrows():
            print(f"  {r['field_id']:20s} top={r['top_crop']:8s} ({r['top_crop_pct']:.0f}%) crops={r['dominant_crops']:30s} seq={r['crop_sequence']}")
    else:
        print("None - all fields have a clear dominant crop.")
    
    # Save
    matrix.to_csv(OUT_DIR / "cdl_confusion_matrix.csv")
    print("\nSaved confusion matrix to data/out/phase3/cdl_confusion_matrix.csv")
    
    # Print summary for the frontend guy
    print("\n" + "="*60)
    print("SUMMARY FOR FRONTEND")
    print("="*60)
    print(f"- {field_years} field-year pairs analysed")
    print(f"- {consistent} ({consistent/max(field_years,1)*100:.1f}%) consistent year-to-year")
    print(f"- {len(anomalous)} anomalous transitions detected")
    print(f"- {len(df_stability)} fields analysed")
    print(f"- {len(flagged)} fields flagged for low stability")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())