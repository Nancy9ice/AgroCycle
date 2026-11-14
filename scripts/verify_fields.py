"""Recompute each field's yearly dominant crop from the CDL clips and compare it with the notes.

Independent of the selection code: it clips the rasters with the saved polygons instead of
searching blocks. Needs the CDL clips (they are not in git). Usage:
    CDL_DIR=~/agrocycle_cdl uv run python -m scripts.verify_fields
"""

import sys

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask

from scripts.select_fields import CDL_DIR, FIPS, LETTERS, LUT, NOTES, THRESHOLD, YEARS
from transform.field_schema import FIELDS_PATH


def dominant_sequence(geometry, county: str):
    """Return (sequence string, lowest dominant-group share) for a polygon in EPSG:5070."""
    letters, lowest = "", 1.0
    for year in YEARS:
        (path,) = CDL_DIR.glob(f"polygonclip_*/CDL_{year}_{FIPS[county]}.tif")
        with rasterio.open(path) as src:
            clip = mask(src, [geometry], crop=True, nodata=0)[0][0]
        groups = LUT[clip[clip != 0]]
        counts = np.bincount(groups, minlength=5)
        letters += LETTERS[counts.argmax()]
        lowest = min(lowest, counts.max() / counts.sum())
    return letters, lowest


def main() -> int:
    fields = gpd.read_file(FIELDS_PATH).to_crs(5070)
    notes = pd.read_csv(NOTES).set_index("field_id")
    column = f"crops_{YEARS[0]}_{YEARS[-1]}"
    mismatches, lowest = [], 1.0
    for f in fields.itertuples():
        sequence, share = dominant_sequence(f.geometry, f.county)
        lowest = min(lowest, share)
        if sequence != notes.loc[f.field_id, column]:
            mismatches.append(f.field_id)
    print(f"{len(fields)} fields; sequence mismatches: {len(mismatches)} {mismatches}")
    print(f"lowest dominant-crop share: {lowest:.3f} (rule: at least {THRESHOLD})")
    return 1 if mismatches or lowest < THRESHOLD else 0


if __name__ == "__main__":
    sys.exit(main())
