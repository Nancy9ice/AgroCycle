"""Where the stacked HLS windows come from: the local Phase 1 pull, or S3 (read-only).

A window is one stack: a field, a sensor, an acquisition date and a sensing time. The local pull holds all
16,560 files, including the 1,962 with no data. S3 holds the 14,598 with data; the 1,962 windows with no data
are only listed in `raw/hls/no-data/.../skipped_no_data.csv`.
"""

import csv
import io
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from ingest.hls import default_dir as default_pull_dir
from transform.hls.mask import Stack, read_stack, stack_from_bytes

RUN_DATE = "2026-11-14"  # the retrieval-date folder of the full run
VERSION = "v2.0"
SENSORS = ("l30", "s30")
NO_DATA_KEY = f"raw/hls/no-data/{VERSION}/{RUN_DATE}/skipped_no_data.csv"
_NAME = re.compile(r"^(?P<sensing>T\d{6})_stack_.*\.tif$")


@dataclass(frozen=True)
class Window:
    field_id: str
    sensor: str
    acquired: date
    sensing_time: str  # "T165930"
    name: str  # the stack's file name

    @property
    def s3_key(self) -> str:
        return f"raw/hls/{self.sensor}/{VERSION}/{RUN_DATE}/{self.field_id}/{self.acquired:%Y%m%d}/{self.name}"


class LocalSource:
    """The pull folder (HLS_DIR, default ~/agrocycle_hls), whose stacks sit under `stacks/`."""

    def __init__(self, base: Path | None = None):
        self.base = (base or default_pull_dir()) / "stacks"

    def windows(self) -> list[Window]:
        found = []
        for path in sorted(self.base.glob("*/*/*/*.tif")):
            match = _NAME.match(path.name)
            sensor, field_id, day = path.parts[-4], path.parts[-3], path.parts[-2]
            if match and sensor in SENSORS:
                found.append(Window(field_id, sensor, datetime.strptime(day, "%Y%m%d").date(),
                                    match["sensing"], path.name))
        return found

    def read(self, window: Window) -> Stack:
        return read_stack(self.base / window.sensor / window.field_id / f"{window.acquired:%Y%m%d}" / window.name)

    def no_data_windows(self) -> list[Window]:
        return []  # they are ordinary files here, and are found by windows()


class S3Source:
    def __init__(self, client, bucket: str):
        self.client, self.bucket = client, bucket

    def windows(self) -> list[Window]:
        found = []
        for sensor in SENSORS:
            prefix = f"raw/hls/{sensor}/{VERSION}/{RUN_DATE}/"
            for page in self.client.get_paginator("list_objects_v2").paginate(Bucket=self.bucket, Prefix=prefix):
                for item in page.get("Contents", []):
                    field_id, day, name = item["Key"][len(prefix):].split("/")
                    match = _NAME.match(name)
                    if match:  # the 460 first-pull band files and the manifests are not stacks
                        found.append(Window(field_id, sensor, datetime.strptime(day, "%Y%m%d").date(),
                                            match["sensing"], name))
        return sorted(found, key=lambda w: (w.field_id, w.acquired, w.sensor, w.sensing_time))

    def read(self, window: Window) -> Stack:
        body = self.client.get_object(Bucket=self.bucket, Key=window.s3_key)["Body"].read()
        return stack_from_bytes(body, window.s3_key)

    def no_data_windows(self) -> list[Window]:
        text = self.client.get_object(Bucket=self.bucket, Key=NO_DATA_KEY)["Body"].read().decode()
        windows = []
        for row in csv.DictReader(io.StringIO(text)):
            sensing = "T" + row["granule"].split(".")[3].split("T")[1]  # HLS.L30.T15TVG.2023135T165901.v2.0
            windows.append(Window(row["field_id"], row["sensor"], date.fromisoformat(row["date"]), sensing, ""))
        return windows
