"""Read the raw POWER and SSURGO files: from the local Phase 1 pull folders when they exist, else from S3."""

import json
import os
from pathlib import Path

POWER_PREFIX = "raw/power/daily-point-api-v2.10.3/2026-11-14"
SSURGO_PREFIX = "raw/ssurgo/soil-data-access/2026-11-14"
POWER_SUFFIX = "_19910101-20251231.json"
MARSDEN_POINT = "marsden-site"
SSURGO_STEPS = ("step_a_map_units", "step_b_components", "step_c_horizons")


def default_power_dir() -> Path:
    return Path(os.environ.get("POWER_DIR", Path.home() / "agrocycle_power")).expanduser()


def default_ssurgo_dir() -> Path:
    return Path(os.environ.get("SSURGO_DIR", Path.home() / "agrocycle_ssurgo")).expanduser()


class Raw:
    """`power_dir` and `ssurgo_dir` hold the files as the extractors saved them. A file missing there is
    read from S3 (read-only), so a teammate with a local copy never needs S3."""

    def __init__(self, power_dir: Path | None = None, ssurgo_dir: Path | None = None):
        self.power_dir = power_dir or default_power_dir()
        self.ssurgo_dir = ssurgo_dir or default_ssurgo_dir()
        self._s3 = None

    def _s3_json(self, key: str):
        if self._s3 is None:
            from common.config import s3_bucket, s3_client

            self._s3 = (s3_client(), s3_bucket())
        client, bucket = self._s3
        return json.loads(client.get_object(Bucket=bucket, Key=key)["Body"].read())

    def power(self, point_id: str) -> dict:
        name = f"{point_id}{POWER_SUFFIX}"
        local = self.power_dir / name
        return json.loads(local.read_text()) if local.exists() else self._s3_json(f"{POWER_PREFIX}/{name}")

    def ssurgo(self, field_id: str, step: str) -> list[list]:
        local = self.ssurgo_dir / field_id / f"{step}.json"
        document = json.loads(local.read_text()) if local.exists() else self._s3_json(
            f"{SSURGO_PREFIX}/{field_id}/{step}.json"
        )
        return document["Table"]
