"""What each raw source is, in the words of PRD 6.1. Compiled by the DE from the S3 manifests, DS1's and DS2's
source sheets, the extractors in `ingest/` and the lineage rows. DS1 and DS2 review it; a correction is a line here.

What the manifests state (product, retrieval date, licence, evidence type) and what S3 holds (file count, bytes)
is read by `scan.py`, not typed here.
"""
from __future__ import annotations

COMPILED_FROM = (
    "Compiled by the DE from the S3 manifests, the DS1 and DS2 source sheets and the extractors in ingest/; "
    "not yet reviewed by the data scientist who owns the source"
)

# source_id -> (S3 prefix of the pull, the PRD 6.1 text)
SOURCES: dict[str, dict] = {
    "cdl": {
        "prefix": "raw/cdl/annual-30m-website-export/2026-11-14/",
        "provider": "USDA National Agricultural Statistics Service (NASS)",
        "product_version": "Annual Cropland Data Layer, 2015 to 2025, as exported from CropScape",
        "url": "https://nassgeodata.gmu.edu/CropScape/",
        "variables": ["crop class code per 30 m pixel", "class table (.vat.dbf) per year"],
        "spatial_resolution": "30 m raster (2024 and 2025 are resampled from the native 10 m product)",
        "temporal_resolution": "annual (one growing-season map per year)",
        "geographic_coverage": "Story and Boone Counties, Iowa (county polygon clip; pixels outside the outline are 0)",
        "historical_coverage": "2015 to 2025",
        "processing_steps": "Stored unchanged. Crop history, rotation class and class shares are computed later "
                            "from the per-field pixels (transform/crop_history).",
        "quality_flags": "Class table per year; background 0 means no data",
        "known_limitations": "A classified product: agreement with another classification, not independent "
                             "validation or ground truth. 2024 and 2025 are resampled. A mixed or low-confidence "
                             "year is labelled as such, never filled.",
    },
    "hls_l30": {
        "prefix": "raw/hls/l30/v2.0/2026-11-14/",
        "provider": "NASA (Harmonized Landsat Sentinel-2 project, distributed through Earthdata)",
        "product_version": "HLS L30 v2.0 (Landsat 8 and 9 surface reflectance)",
        "url": "https://lpdaac.usgs.gov/products/hlsl30v002/",
        "variables": ["B04 red", "B05 near infrared", "B06 shortwave infrared 1", "Fmask quality band"],
        "spatial_resolution": "30 m, per-field windows with a 500 m buffer",
        "temporal_resolution": "per scene, April to October",
        "geographic_coverage": "The 45 demonstration fields in Story and Boone Counties, Iowa",
        "historical_coverage": "2023 to 2025",
        "processing_steps": "Windows cut per field and date, stored unmasked and unscaled (reflectance scale 0.0001, "
                            "fill -9999; Fmask 255 is fill). The valid-pixel counts are computed in transform/hls.",
        "quality_flags": "Fmask per pixel; a pixel is valid when Fmask & 0b00111110 == 0",
        "known_limitations": "Optical: cloud, shadow and snow remove observations, so counts of valid pixels are "
                             "kept beside every value. Observed reflectance, not yet a vegetation index.",
    },
    "hls_s30": {
        "prefix": "raw/hls/s30/v2.0/2026-11-14/",
        "provider": "NASA (Harmonized Landsat Sentinel-2 project, distributed through Earthdata)",
        "product_version": "HLS S30 v2.0 (Sentinel-2A and 2B surface reflectance)",
        "url": "https://lpdaac.usgs.gov/products/hlss30v002/",
        "variables": ["B04 red", "B8A near infrared", "B11 shortwave infrared 1", "Fmask quality band"],
        "spatial_resolution": "30 m, per-field windows with a 500 m buffer",
        "temporal_resolution": "per scene, April to October",
        "geographic_coverage": "The 45 demonstration fields in Story and Boone Counties, Iowa",
        "historical_coverage": "2023 to 2025",
        "processing_steps": "Windows cut per field and date, stored unmasked and unscaled (reflectance scale 0.0001, "
                            "fill -9999; Fmask 255 is fill). The valid-pixel counts are computed in transform/hls.",
        "quality_flags": "Fmask per pixel; a pixel is valid when Fmask & 0b00111110 == 0",
        "known_limitations": "Optical: cloud, shadow and snow remove observations, so counts of valid pixels are "
                             "kept beside every value. Observed reflectance, not yet a vegetation index.",
    },
    "hls_no_data": {
        "prefix": "raw/hls/no-data/v2.0/2026-11-14/",
        "provider": "AgroCycle data engineering (a list made while pulling NASA HLS)",
        "product_version": "HLS v2.0 windows with no data (list of skipped cuts)",
        "url": "https://lpdaac.usgs.gov/products/hlsl30v002/",
        "variables": ["sensor", "field_id", "date", "granule", "tile"],
        "spatial_resolution": "per field window",
        "temporal_resolution": "per scene date",
        "geographic_coverage": "The 45 demonstration fields in Story and Boone Counties, Iowa",
        "historical_coverage": "2023 to 2025",
        "processing_steps": "Windows whose pixels are all fill were not uploaded and are listed here instead.",
        "quality_flags": "Each row is one granule window with no observation",
        "known_limitations": "Counted as no observation (unknown) in denominators; never as clear or cloudy.",
    },
    "power": {
        "prefix": "raw/power/daily-point-api-v2.10.3/2026-11-14/",
        "provider": "NASA Langley Research Center, POWER project",
        "product_version": "POWER daily point API v2.10.3, community AG",
        "url": "https://power.larc.nasa.gov/docs/services/api/temporal/daily/",
        "variables": ["T2M_MAX", "T2M_MIN", "T2M", "PRECTOTCORR", "RH2M", "ALLSKY_SFC_SW_DWN", "WS2M"],
        "spatial_resolution": "Grid cell, about 0.5 x 0.625 degrees (about 50 km) for MERRA-2 meteorology; some variables coarser",
        "temporal_resolution": "daily (local solar time)",
        "geographic_coverage": "One point per field centroid cell (45 fields) plus the Marsden Farm site",
        "historical_coverage": "1991-01-01 to 2025-12-31",
        "processing_steps": "Raw API response stored unchanged; fill value -999 becomes null when cleaned "
                            "(transform/clean); indicators are computed by DS2's runner.",
        "quality_flags": "Fill counts per variable recorded in the manifest notes; fill days stay null, never zero",
        "known_limitations": "Model reanalysis at grid scale, not a field measurement: it shows regional conditions, "
                             "and neighbouring fields can share one cell.",
    },
    "ssurgo": {
        "prefix": "raw/ssurgo/soil-data-access/2026-11-14/",
        "provider": "USDA Natural Resources Conservation Service (NRCS)",
        "product_version": "SSURGO via Soil Data Access (tabular REST service), retrieved 2026-11-14",
        "url": "https://sdmdataaccess.nrcs.usda.gov/",
        "variables": ["map unit shares", "component drainage class and hydrologic group", "slope",
                      "horizon organic matter, clay, silt, sand, pH, available water capacity"],
        "spatial_resolution": "Mapped soil units (survey polygons), not a lab sample of the field",
        "temporal_resolution": "static survey (no time dimension)",
        "geographic_coverage": "Map units intersecting the 45 demonstration fields (three steps per field)",
        "historical_coverage": "Current survey at the time of retrieval",
        "processing_steps": "Representative (_r) values only, stored unchanged; area shares, depth weighting and "
                            "units are applied later (transform/clean, DS2's aggregation).",
        "quality_flags": "Missing values stay unknown; partial depth coverage is stated per value",
        "known_limitations": "A soil survey, not a measurement of the field: a map unit mixes soils. Licence terms "
                             "were not confirmed from a source page; check before redistributing.",
    },
    "marsden_supplement": {
        "prefix": "raw/marsden/pone.0047149-supplement/2026-11-13/",
        "provider": "Davis et al. (2012), Iowa State University Marsden Farm experiment, PLOS ONE",
        "product_version": "PLOS ONE 7(10): e47149, article and supporting information (DS2's originals)",
        "url": "https://doi.org/10.1371/journal.pone.0047149",
        "variables": ["applied, manufactured and manure nitrogen per rotation", "herbicide per rotation"],
        "spatial_resolution": "one research farm (plot level), not a field in Story or Boone County",
        "temporal_resolution": "annual means over the nine-season experiment",
        "geographic_coverage": "Marsden Farm, Boone County, Iowa",
        "historical_coverage": "2003 to 2011",
        "processing_steps": "Files stored unchanged with DS2's checksum list; tables read and checked against the "
                            "paper by DS2's reproduction (transform/marsden).",
        "quality_flags": "Every file checked against DS2's checksums; reconciled against the Europe PMC copy",
        "known_limitations": "Experimental evidence from one farm over nine seasons: not a prediction for a farmer's "
                             "field. The diversified systems also received manure.",
    },
    "marsden_europepmc": {
        "prefix": "raw/marsden/europepmc-supplementary-zip/2026-11-14/",
        "provider": "Europe PMC (a copy of the Davis et al. 2012 supplement)",
        "product_version": "PMC3468434 supplementary files ZIP, as returned by Europe PMC",
        "url": "https://europepmc.org/article/PMC/PMC3468434",
        "variables": ["the seven supplement files", "the figures"],
        "spatial_resolution": "one research farm (plot level)",
        "temporal_resolution": "annual means over the nine-season experiment",
        "geographic_coverage": "Marsden Farm, Boone County, Iowa",
        "historical_coverage": "2003 to 2011",
        "processing_steps": "The ZIP is stored exactly as received; it is an independent copy used to check DS2's originals.",
        "quality_flags": "Byte-identical to DS2's originals where the files overlap",
        "known_limitations": "Experimental evidence from one farm over nine seasons: not a prediction for a farmer's field.",
    },
    "nass_quickstats": {
        "prefix": "raw/nass/api_GET/2026-11-15/",
        "provider": "USDA National Agricultural Statistics Service (NASS)",
        "product_version": "QuickStats API (api_GET, no version number), county survey statistics, retrieved 2026-11-15",
        "url": "https://quickstats.nass.usda.gov/",
        "variables": ["area planted", "area harvested", "yield", "production",
                      "for corn, soybeans, oats and hay (alfalfa is a class of hay)"],
        "spatial_resolution": "County (Story and Boone, Iowa), not field",
        "temporal_resolution": "annual (one survey figure per county, commodity and year)",
        "geographic_coverage": "Story County (FIPS 19169) and Boone County (FIPS 19015), Iowa",
        "historical_coverage": "2003 to 2025; the years NASS published for each commodity (oats and hay have gaps, "
                               "and hay ends in 2017 for Story and 2018 for Boone)",
        "processing_steps": "One request per county, commodity and statistic, stored unchanged. Cleaned into "
                            "county_stats (transform/nass): a withheld value such as (D) becomes null with a "
                            "withheld status; corn grain and silage stay separate rows; nothing is filled.",
        "quality_flags": "Withheld values (2, both Boone hay 2013) stay null; requests NASS has no data for "
                         "(hay area planted) are listed in empty_requests.json; production agrees with yield "
                         "times area harvested within 1.4 % in the 171 combinations checked",
        "known_limitations": "A county survey estimate: context for what is grown nearby, not field-level yield "
                             "validation. No county data exists for red clover, and oats and hay are patchy or "
                             "discontinued.",
    },
}

# The text in indicator_lineage.source_ids (one JSON list item) -> source ids.
LINEAGE_TEXT_TO_SOURCES: dict[str, tuple[str, ...]] = {
    "NASA POWER daily point API, community AG": ("power",),
    "USDA SSURGO via Soil Data Access (SDA) tabular REST service": ("ssurgo",),
    "Marsden Farm supplementary data, Davis et al. (2012) PLOS ONE 7(10): e47149, "
    "https://doi.org/10.1371/journal.pone.0047149": ("marsden_supplement",),
}

# Derived tables and the sources they are computed from.
TABLE_SOURCES: dict[str, tuple[str, ...]] = {
    "crop_class_shares": ("cdl",),
    "crop_history": ("cdl",),
    "crop_rotation": ("cdl",),
    "hls_valid_pixels": ("hls_l30", "hls_s30", "hls_no_data"),
    "climate_points": ("power",),
    "climate_daily": ("power",),
    "soil_properties": ("ssurgo",),
    "county_stats": ("nass_quickstats",),
    "marsden_management": ("marsden_supplement",),
    "marsden_reconciliation": ("marsden_supplement", "marsden_europepmc"),
}
