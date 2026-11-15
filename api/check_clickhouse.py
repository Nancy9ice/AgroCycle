"""Print what the API would read from ClickHouse for one field. Run by someone with credentials:

    uv run python -m api.check_clickhouse primary-001

It uses the same repository the API uses (`AGROCYCLE_DATA_SOURCE=clickhouse`) and reads only. Output is the
field record, the indicator statuses the engine would see, the weather means the profile would show, and the
drainage class. If anything here looks wrong, the API will serve it.
"""
from __future__ import annotations

import sys

from .core.profile import build_profile
from .db.repository import ClickHouseRepository, FileRepository


def describe(repository: ClickHouseRepository, field_id: str) -> list[str]:
    record = repository.get_field(field_id)
    if record is None:
        return [f"no field {field_id!r} in ClickHouse `fields`"]
    facts = repository.get_indicators(field_id)
    profile = build_profile(record, facts)
    lines = [
        f"field        {record.field_id}  ({record.county} County, {record.boundary_source}, {record.role})",
        f"class        {record.field_class}  (from ClickHouse crop_rotation)",
        f"sequence     {record.crop_sequence}  (from the committed notes)",
        f"soil         {record.soil_series} / {record.soil_map_unit}  (from the committed notes)",
        f"statuses     {facts.statuses or 'none'}",
        f"unknown      {list(profile.unknown_required_indicators()) or 'none: all four required indicators are ok'}",
        f"gdd vs Marsden   {facts.gdd_season_difference_vs_marsden}",
        f"frost-free days  {facts.frost_free_days}",
        f"drainage     {facts.dominant_drainage_class}",
    ]
    if not facts.seasonal:
        lines.append("weather      no indicator rows read for this field")
    for mean in facts.seasonal.values():
        lines.append(
            f"weather      {mean.indicator_id}: mean {mean.mean:.1f} {mean.unit} "
            f"over {mean.seasons_used} of {mean.seasons_total} seasons ({mean.first_year} to {mean.last_year})"
        )
    return lines


def main(argv: list[str]) -> int:
    from common.config import clickhouse_client  # needs the project's dependencies and a .env

    field_id = argv[1] if len(argv) > 1 else "primary-001"
    repository = ClickHouseRepository(clickhouse_client(), notes=FileRepository())
    print("\n".join(describe(repository, field_id)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
