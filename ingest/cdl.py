"""CDL raw data: the county clips exported from the CropScape website, plus their class tables.

22 GeoTIFFs (Story and Boone, 2015-2025) and the 22 `.tif.vat.dbf` class tables that came
with them. The tables map CDL class codes to crop names.
"""

import os
import re
from pathlib import Path

import geopandas as gpd

from ingest.checks import check_opens, check_raster
from ingest.items import Item
from ingest.manifest import Manifest, build_manifest
from ingest.subset import check_budget, subset_record, union_bbox
from transform.field_schema import FIELDS_PATH

SOURCE = "cdl"
VERSION = "annual-30m-website-export"
BUDGET_BYTES = 100_000_000
YEARS = range(2015, 2026)
COUNTIES = {"Story": "19169", "Boone": "19015"}
RESAMPLED_YEARS = (2024, 2025)  # native 10 m; the website serves the resampled 30 m product
SOURCE_URL = (
    "https://nassgeodata.gmu.edu/CropScape/ (website export, polygon clip to county; "
    "no per-file URL exists)"
)
LICENCE = (
    "Public domain, free to redistribute "
    "(USDA NASS CDL FAQ: https://www.nass.usda.gov/Research_and_Science/Cropland/sarsfaqs2.php)"
)
TIF_NOTES = (
    "Classified output: agreement with another classification, not independent validation. "
    "Exported from the CropScape website as a county polygon clip; pixels outside the county "
    "outline are 0 (no data)."
)
RESAMPLED_NOTE = (
    " This year is the resampled 30 m product; the native 2024-2025 CDL is 10 m. "
    "Native 10 m was not obtainable from the website exports, and DS1 agreed to use 30 m."
)


def default_dir() -> Path:
    return Path(os.environ.get("CDL_DIR", Path.home() / "agrocycle_cdl")).expanduser()


def retrieval_date(path: Path) -> str:
    """The export date, read from the website's folder name (polygonclip_YYYYMMDDhhmmss_...)."""
    match = re.fullmatch(r"polygonclip_(\d{4})(\d{2})(\d{2})\d{6}_\d+", path.parent.name)
    if not match:
        raise ValueError(f"{path}: cannot read the export date from the folder name")
    return "-".join(match.groups())


def find_files(base: Path) -> dict[tuple[str, int], Path]:
    """Map (county, year) to its GeoTIFF; fail on missing, duplicate or stray clips."""
    found, problems = {}, []
    for county, fips in COUNTIES.items():
        for year in YEARS:
            matches = sorted(base.glob(f"polygonclip_*/CDL_{year}_{fips}.tif"))
            if len(matches) != 1:
                problems.append(f"{county} {year}: expected 1 clip, found {len(matches)}")
            else:
                found[(county, year)] = matches[0]
    wanted = {p.name for p in found.values()}
    problems += [
        f"unexpected clip {p.name}" for p in base.glob("polygonclip_*/CDL_*.tif")
        if p.name not in wanted
    ]
    if problems:
        raise RuntimeError("CDL clips are not as expected:\n- " + "\n- ".join(problems))
    return found


def plan(base: Path | None = None, fields: gpd.GeoDataFrame | None = None) -> list[Item]:
    """Build a manifest and run the file checks for every clip and class table."""
    base = base or default_dir()
    fields = gpd.read_file(FIELDS_PATH) if fields is None else fields
    items = []
    for (county, year), tif in find_files(base).items():
        covers = union_bbox(fields[fields["county"] == county])
        resampled = year in RESAMPLED_YEARS
        subset = subset_record(
            "county", county=county, fips=COUNTIES[county], year=year,
            crs="EPSG:5070", pixel_m=30, resampled_from_10m=resampled,
        )
        common = {
            "source_url": SOURCE_URL,
            "product": "USDA NASS Cropland Data Layer (county clip)",
            "version": VERSION,
            "retrieval_date": retrieval_date(tif),
            "licence": LICENCE,
            "subset": subset,
            "evidence_type": "classified",
        }
        checks = check_raster(tif, crs="EPSG:5070", pixel_size=30, covers=covers)
        notes = TIF_NOTES + (RESAMPLED_NOTE if resampled else "")
        items.append(
            Item(tif, build_manifest(tif, scale="30 m raster", notes=notes, **common), checks, SOURCE)
        )
        table = tif.with_name(tif.name + ".vat.dbf")
        table_note = "Class table (code to crop name) that came with the matching GeoTIFF."
        items.append(
            Item(
                table,
                build_manifest(table, scale="class table", notes=table_note, **common)
                if table.exists() else _missing(table, common),
                check_opens(table),
                SOURCE,
            )
        )
    check_budget("cdl", sum(i.manifest.size_bytes for i in items), BUDGET_BYTES)
    return items


def _missing(table: Path, common: dict) -> Manifest:
    """Placeholder so a missing class table shows up as a failed check, not a crash."""
    return Manifest(sha256="0" * 64, size_bytes=0, scale="class table", notes="missing", **common)
