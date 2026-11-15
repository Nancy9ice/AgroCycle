"""Check the aerial photo for one field against the real database and bucket.

    uv run python -m api.check_imagery primary-001 [out.png]

Needs the ClickHouse and AWS settings in `.env`. Prints what `naip_tiles` says, reads the chip from S3,
checks its checksum, and writes the picture it would serve. Open the file and look at it: a photo that is
shifted, flipped or blank is a bug this check exists to catch. Read-only.
"""
from __future__ import annotations

import sys
from pathlib import Path

from api.core.imagery import render_chip
from api.db.imagery import ClickHouseS3Imagery


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    field_id = argv[0]
    out = Path(argv[1] if len(argv) > 1 else f"{field_id}-aerial.png")

    from common.config import clickhouse_client, s3_bucket, s3_client

    source = ClickHouseS3Imagery(clickhouse_client(), s3_client(), s3_bucket())
    records = source.records(field_id)
    if not records:
        print(f"{field_id}: no rows in naip_tiles")
        return 1
    for r in records:
        print(f"tile {r.tile_id}  flown {r.flight_date}  {r.resolution_m} m  {r.bands}  {r.s3_key}")
    rendered = render_chip(source.chip(records[0]))
    out.write_bytes(rendered.png)
    west, south, east, north = rendered.bounds
    print(f"checksum ok. Picture {rendered.width} x {rendered.height} px, {len(rendered.png) / 1e6:.1f} MB -> {out}")
    print(f"bounds  west {west:.6f}  south {south:.6f}  east {east:.6f}  north {north:.6f}")
    print(f"index bbox for the same field: {records[0].bbox}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
