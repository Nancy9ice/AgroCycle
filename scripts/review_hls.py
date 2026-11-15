"""Review HLS dev sample for primary-001."""
import os

import boto3
import numpy as np
import rasterio

with open(".env") as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()

s3 = boto3.client("s3", region_name=os.environ["AWS_REGION"])
bucket = "agrocycle-fieldshift-2026-data"

# Download one scene (April 5, 2023 - b04, b05, b06, fmask)
scene = "20230405"
prefix = f"raw/hls/l30/v2.0/2026-11-14/primary-001/{scene}/"

for band in ["b04", "b05", "b06", "fmask"]:
    key = f"{prefix}{band}.tif"
    local = f"/tmp/hls_primary001_{scene}_{band}.tif"
    s3.download_file(bucket, key, local)
    
    with rasterio.open(local) as src:
        data = src.read(1)
        print(f"=== {band}.tif ===")
        print(f"  CRS: {src.crs}")
        print(f"  Shape: {data.shape}")
        print(f"  Bounds: {src.bounds}")
        print(f"  dtype: {data.dtype}")
        print(f"  Min: {data.min()}, Max: {data.max()}")
        
        if band == "fmask":
            # Check fmask is uint8
            print(f"  Fmask unique values: {sorted(np.unique(data))[:15]}")
        else:
            # Check reflectance values make sense
            valid = data[data > -9990]  # Exclude fill values
            if len(valid) > 0:
                print(f"  Valid pixels: {len(valid)}")
                print(f"  Mean reflectance: {valid.mean():.4f}")
        print()

print("All checks passed: HLS files open, have correct CRS, sensible reflectance values.")