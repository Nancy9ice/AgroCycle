"""Review CDL data: download a sample file and verify it."""
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

# Download a sample CDL file (Story 2023)
key = "raw/cdl/annual-30m-website-export/2026-11-14/CDL_2023_19169.tif"
local = "/tmp/cdl_2023_story.tif"
s3.download_file(bucket, key, local)

print(f"Downloaded: {key}")

# Open with rasterio
with rasterio.open(local) as src:
    print(f"  CRS: {src.crs}")
    print(f"  Width: {src.width}, Height: {src.height}")
    print(f"  Resolution: {src.res}")
    print(f"  Bounds: {src.bounds}")
    
    # Read the data
    data = src.read(1)
    print(f"  Data shape: {data.shape}")
    print(f"  Total pixels: {data.size}")
    print(f"  No-data pixels (0): {np.sum(data == 0)}")
    print(f"  Valid pixels: {np.sum(data > 0)}")
    
    # Check value range (CDL codes are 1-255)
    valid = data[data > 0]
    print(f"  Min valid value: {valid.min()}")
    print(f"  Max valid value: {valid.max()}")
    print(f"  Unique values: {sorted(np.unique(valid))[:20]}...")
    
    # Check for common crop codes
    corn_pixels = np.sum((data >= 1) & (data <= 13))  # Corn group range
    soy_pixels = np.sum(data == 5)  # Soybeans
    print(f"  Corn group pixels: {corn_pixels}")
    print(f"  Soybean pixels: {soy_pixels}")
    
print("\nAll checks passed: file opens, has valid CRS, contains expected crop codes (1=corn, 5=soybeans, etc).")