"""Write a starter field file with all 45 slots and properties filled in.

Each slot gets a tiny placeholder square (about 10 m) near its county's centre. The
square is below the minimum parcel area, so the validator reports every slot whose
polygon has not been redrawn yet.

Usage: uv run python -m scripts.make_field_template
"""

import geopandas as gpd
from shapely.geometry import box

from transform.field_schema import COUNTIES_PATH, IN_DOMAIN, OUT_OF_DOMAIN, ROOT

OUT = ROOT / "data" / "fields" / "fields_template.geojson"
PROVENANCE = "drawn by DE on 2026-11-14, demonstration geometry (not a real farm boundary)"

# (role, domain_note, Story count, Boone count)
PLAN = [
    ("primary", IN_DOMAIN, 1, 0),
    ("test", IN_DOMAIN, 13, 13),
    ("test", OUT_OF_DOMAIN[0], 3, 3),  # continuous corn
    ("test", OUT_OF_DOMAIN[1], 3, 3),  # pasture-hay
    ("test", OUT_OF_DOMAIN[2], 3, 3),  # mixed-non-rotation
]


def main() -> None:
    counties = gpd.read_file(COUNTIES_PATH).set_index("county")
    centres = {
        c: counties.geometry[[c]].to_crs(5070).representative_point().iloc[0].coords[0]
        for c in ("Story", "Boone")
    }
    rows, slot = [], {"Story": 0, "Boone": 0}
    n_test = 0
    for role, note, n_story, n_boone in PLAN:
        for county, n in (("Story", n_story), ("Boone", n_boone)):
            for _ in range(n):
                if role == "primary":
                    field_id = "primary-001"
                else:
                    n_test += 1
                    field_id = f"test-{n_test:03d}"
                cx, cy = centres[county]
                x = cx + slot[county] * 50  # a row of placeholders, 50 m apart
                slot[county] += 1
                rows.append(
                    {
                        "field_id": field_id,
                        "role": role,
                        "boundary_source": "demo",
                        "county": county,
                        "provenance": PROVENANCE,
                        "domain_note": note,
                        "geometry": box(x, cy, x + 10, cy + 10),
                    }
                )
    gdf = gpd.GeoDataFrame(rows, crs=5070).to_crs(4326)
    gdf.to_file(OUT, driver="GeoJSON")
    print(f"wrote {len(gdf)} placeholder fields to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
