"""Turns a NAIP field chip into a picture a web map can lay on the ground.

The chip is a small GeoTIFF kept in S3 on its source grid (UTM metres, 4 bands). A web map places an image
by its longitude and latitude corners, so the chip is warped to longitude/latitude here, with a transparent
edge where the chip has no pixels. Colours are not changed: red, green and blue are the first three bands as
flown. The picture is reference imagery from one flight date; it is never crop ground truth.

`rasterio` is imported inside `render_chip`, so the API starts without it.
"""
from __future__ import annotations

import struct
import threading
import zlib
from collections import OrderedDict
from dataclasses import dataclass
from datetime import date

MAX_PIXELS = 1600  # long side of the picture; a 0.6 m chip of a large field is shrunk to this
ATTRIBUTION = "Aerial photo: USDA Farm Service Agency (NAIP), via Microsoft Planetary Computer"


class ImageryError(RuntimeError):
    """A chip that cannot be read or does not match the index. Never turned into a blank picture."""


@dataclass(frozen=True)
class ChipRecord:
    """One row of `naip_tiles`: a chip, the tile it was cut from, and when that tile was flown."""

    field_id: str
    year: int
    tile_id: str
    flight_date: date
    resolution_m: float
    bbox: tuple[float, float, float, float]  # west, south, east, north (longitude, latitude)
    buffer_m: float
    bands: str
    s3_key: str
    size_bytes: int
    sha256: str
    evidence_type: str
    source_id: str


@dataclass(frozen=True)
class RenderedChip:
    png: bytes
    bounds: tuple[float, float, float, float]  # west, south, east, north of the picture as drawn
    width: int
    height: int


def encode_png(rgba) -> bytes:
    """An RGBA PNG from a (height, width, 4) uint8 array, with the standard library only."""
    height, width, channels = rgba.shape
    if channels != 4:
        raise ImageryError("expected four channels (red, green, blue, alpha)")
    raw = b"".join(b"\x00" + rgba[row].tobytes() for row in range(height))

    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 6))
        + chunk(b"IEND", b"")
    )


def render_chip(tif: bytes, max_pixels: int = MAX_PIXELS) -> RenderedChip:
    import numpy as np
    import rasterio
    from rasterio.io import MemoryFile
    from rasterio.transform import array_bounds
    from rasterio.warp import Resampling, calculate_default_transform, reproject

    try:
        memory = MemoryFile(tif)
        source = memory.open()
    except Exception as err:  # rasterio raises several types for a file it cannot open
        raise ImageryError(f"the chip is not a readable GeoTIFF: {err}") from err
    with memory, source:
        if source.count < 3:
            raise ImageryError(f"the chip has {source.count} bands; red, green and blue are needed")
        if source.crs is None:
            raise ImageryError("the chip has no coordinate system, so it cannot be placed on a map")
        if any(dtype != "uint8" for dtype in source.dtypes[:3]):
            raise ImageryError(f"expected 8-bit colour bands, got {source.dtypes[:3]}")

        target = "EPSG:4326"
        transform, width, height = calculate_default_transform(
            source.crs, target, source.width, source.height, *source.bounds
        )
        longest = max(width, height)
        if longest > max_pixels:
            shrink = longest / max_pixels
            transform, width, height = calculate_default_transform(
                source.crs, target, source.width, source.height, *source.bounds,
                resolution=(transform.a * shrink, -transform.e * shrink),
            )

        out = np.zeros((4, height, width), dtype=np.uint8)
        for band in range(3):
            reproject(
                source=rasterio.band(source, band + 1), destination=out[band],
                src_transform=source.transform, src_crs=source.crs,
                dst_transform=transform, dst_crs=target, resampling=Resampling.bilinear,
            )
        # Opaque where the chip has pixels, transparent elsewhere (the corners the warp leaves empty).
        reproject(
            source=source.dataset_mask(), destination=out[3],
            src_transform=source.transform, src_crs=source.crs,
            dst_transform=transform, dst_crs=target, resampling=Resampling.nearest,
        )
        west, south, east, north = array_bounds(height, width, transform)

    return RenderedChip(
        png=encode_png(np.ascontiguousarray(np.moveaxis(out, 0, -1))),
        bounds=(west, south, east, north), width=width, height=height,
    )


class RenderCache:
    """Rendered photos, kept so each chip is fetched from S3 and rendered once, not once per request.

    A chip is a few MB and the bucket is remote, so a cold render costs seconds. Both photo endpoints ask for the
    same chip, and several people can ask at once: they share one render (the others wait for it). Keyed by the
    chip's checksum, so a replaced chip is never served from here. Bounded, oldest out first.
    """

    def __init__(self, max_entries: int = 64) -> None:
        self._max = max_entries
        self._items: OrderedDict[tuple[str, str], RenderedChip] = OrderedDict()
        self._lock = threading.Lock()
        self._key_locks: dict[tuple[str, str], threading.Lock] = {}

    def get(self, record: ChipRecord, fetch_and_render) -> RenderedChip:
        key = (record.s3_key, record.sha256)
        with self._lock:
            if key in self._items:
                self._items.move_to_end(key)
                return self._items[key]
            key_lock = self._key_locks.setdefault(key, threading.Lock())
        with key_lock:
            with self._lock:
                if key in self._items:
                    return self._items[key]
            rendered = fetch_and_render()  # an ImageryError propagates and is not cached
            with self._lock:
                self._items[key] = rendered
                while len(self._items) > self._max:
                    self._items.popitem(last=False)
            return rendered
