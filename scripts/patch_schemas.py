"""Add HLS_NDVI and HLS_BARE_WINDOWS pandera schemas to common/schemas.py."""
import sys
from pathlib import Path

path = Path("common/schemas.py")
content = path.read_text(encoding="utf-8")

new_schemas = r"""
_ndvi_val = pa.Column(float, pa.Check.in_range(-1, 1, include_min=False), nullable=False)

HLS_NDVI = pa.DataFrameSchema(
    {
        "field_id": _key_text,
        "sensor": pa.Column(str, pa.Check.isin(["l30", "s30"]), nullable=False),
        "acquired": pa.Column("datetime64[ns]", nullable=False),
        "sensing_time": pa.Column(str, pa.Check.str_matches(r"^T\d{6}$"), nullable=False),
        "ndvi_mean": _ndvi_val,
        "ndvi_median": _ndvi_val,
        "ndvi_p25": _ndvi_val,
        "ndvi_p75": _ndvi_val,
        "ndvi_std": pa.Column(float, pa.Check.ge(0), nullable=False),
        "ndvi_valid_pixels": pa.Column(int, pa.Check.gt(0), nullable=False),
        "valid_share": pa.Column(float, pa.Check.in_range(0, 1), nullable=False),
        "n_clear_pixels": pa.Column(int, pa.Check.gt(0), nullable=False),
    },
    unique=["field_id", "sensor", "acquired", "sensing_time"],
    strict=True,
)

HLS_BARE_WINDOWS = pa.DataFrameSchema(
    {
        "field_id": _key_text,
        "year": pa.Column(int, pa.Check.in_range(2020, 2030), nullable=False),
        "bare_window_start": pa.Column("datetime64[ns]", nullable=False),
        "bare_window_end": pa.Column("datetime64[ns]", nullable=False),
        "bare_days": pa.Column(int, pa.Check.ge(14), nullable=False),
        "ndvi_before": pa.Column(float, nullable=True),
        "ndvi_after": pa.Column(float, nullable=True),
        "confidence": pa.Column(str, pa.Check.isin(["high", "medium", "low"]), nullable=False),
    },
    unique=["field_id", "year", "bare_window_start"],
    strict=True,
)

"""

old = "@dataclass(frozen=True)"
new = new_schemas + old

if old in content:
    content = content.replace(old, new, 1)
    path.write_text(content, encoding="utf-8")
    print("Added HLS_NDVI and HLS_BARE_WINDOWS schemas to schemas.py")
else:
    print("ERROR: @dataclass not found")
    sys.exit(1)