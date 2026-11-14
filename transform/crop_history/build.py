"""Turn field polygons and CDL clips into the four frames that go to ClickHouse.

    fields_frame(gdf)               -> `fields`
    crop_frames(gdf, clips, ...)    -> `crop_class_shares`, `crop_history`, `crop_rotation`

Rules come from transform.crop_history.rules (DS1 v1.0); counting from transform.crop_history.zonal.
"""

from dataclasses import dataclass, field

import geopandas as gpd
import pandas as pd

from transform.crop_history import rules, zonal

LIMITATION = (
    "Derived from the CDL, a classified product and not ground truth, at 30 m (2024-2025 resampled "
    "from 10 m). Thresholds are DS1's v1.0 and are not expert-reviewed. Demonstration geometry."
)


def fields_frame(gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    """The `fields` table, from the validated field file."""
    frame = pd.DataFrame(gdf.drop(columns="geometry"))
    frame["geometry_wkt"] = gdf.geometry.to_wkt()
    frame["cover_detail"] = frame["cover_detail"].fillna("")
    columns = ["field_id", "role", "boundary_source", "county", "provenance", "domain_note",
               "cover_detail", "geometry_wkt"]
    return frame[columns].reset_index(drop=True)


@dataclass
class CropFrames:
    shares: pd.DataFrame
    history: pd.DataFrame
    rotation: pd.DataFrame
    unlisted_codes: dict[int, str] = field(default_factory=dict)  # code -> name, for DS1 to review


def crop_frames(gdf: gpd.GeoDataFrame, clip_map: dict, counter=zonal.field_counts) -> CropFrames:
    """Count every field in every year, label the years and classify each field."""
    projected = gdf.to_crs(zonal.RASTER_CRS)
    names: dict[tuple[str, int], dict[int, str]] = {}
    shares, history, rotation, unlisted = [], [], [], {}
    for row in projected.itertuples():
        labels = {}
        for (county, year), clip in sorted(clip_map.items(), key=lambda item: item[0][1]):
            if county != row.county:
                continue
            counts = counter(clip.path, row.geometry)
            if (county, year) not in names:
                names[(county, year)] = zonal.class_names(clip.path)
            total = sum(counts.values())
            for code, pixels in sorted(counts.items()):
                name = names[(county, year)].get(code, f"unnamed class {code}")
                listed = rules.is_listed(code)
                if not listed:
                    unlisted[code] = name
                shares.append({
                    "field_id": row.field_id, "year": year, "cdl_class_code": code,
                    "cdl_class_name": name, "class_group": rules.class_group(code),
                    "flag": "" if listed else "unlisted_code",
                    "pixels": pixels, "share_pct": 100 * pixels / total,
                    "resolution_m": clip.resolution_m, "product_version": clip.product_version,
                    "source_s3_key": clip.s3_key,
                })
            label = rules.label_year(counts)
            labels[year] = label
            history.append({
                "field_id": row.field_id, "year": year, "dominant_group": label.group,
                "status": label.status, "dominant_share_pct": label.dominant_share_pct,
                "nodata_share_pct": label.nodata_share_pct, "total_pixels": label.total_pixels,
                "rule_version": rules.RULE_VERSION, "evidence_type": "classified",
            })
        result = rules.classify_field(labels)
        rotation.append({
            "field_id": row.field_id, "field_class": result.field_class, "sequence": result.sequence,
            "corn_years": result.corn_years, "soybean_years": result.soybean_years,
            "pasture_hay_years": result.pasture_hay_years, "alternations": result.alternations,
            "transitions_counted": result.transitions_counted, "rule_version": rules.RULE_VERSION,
            "evidence_type": "derived", "limitation": LIMITATION,
        })
    return CropFrames(pd.DataFrame(shares), pd.DataFrame(history), pd.DataFrame(rotation), unlisted)
