"""The HLS quality mask, scaling and polygon clip (roadmap Phase 5, DE).

A stacked window holds four int16 bands: three reflectance bands, then `Fmask` (the 0-255 source value).
Reflectance has scale 0.0001 and fill -9999; `Fmask` 255 is fill.

The mask rule (NASA HLS v2.0 User Guide, Table 9; it corrects the bit table in DS1's first sheet):

    keep a pixel only if  Fmask & 0b00111110 == 0   (bits 1-5: cloud, adjacent to cloud, cloud shadow,
                                                      snow/ice, water)
    never keep fill       (Fmask == 255, or any reflectance band == -9999)

Bits 0 (cirrus, unused), 6 and 7 (aerosol level) do not mask. Reflectance is scaled and otherwise left as
it is, including the small negative values the product can hold. Fill becomes NaN, never zero.
"""

import threading
from dataclasses import dataclass

import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.io import MemoryFile
from shapely.geometry import mapping

TILE_CRS = "EPSG:32615"
SCALE = 0.0001
REFLECTANCE_FILL = -9999
FMASK_FILL = 255
MASK_BITS = 0b00111110
MASK_RULE = "Fmask & 0b00111110 == 0; Fmask 255 and reflectance -9999 are fill"
_RASTERIZE_LOCK = threading.Lock()


@dataclass(frozen=True)
class Stack:
    data: np.ndarray  # int16, (bands, rows, cols); the last band is Fmask
    transform: rasterio.Affine
    crs: str


@dataclass(frozen=True)
class Classes:
    fill: np.ndarray  # bool, (rows, cols)
    flagged: np.ndarray  # masked by bits 1-5, and not fill
    valid: np.ndarray  # kept


@dataclass(frozen=True)
class MaskedStack:
    reflectance: np.ndarray  # float32, (bands - 1, rows, cols), NaN unless valid and inside the polygon
    classes: Classes
    inside: np.ndarray  # bool: pixel centre inside the polygon (all True without a polygon)
    transform: rasterio.Affine
    crs: str


def _from_dataset(src, label) -> Stack:
    crs = src.crs.to_string()
    if crs != TILE_CRS:
        raise ValueError(f"{label}: CRS {crs}, expected {TILE_CRS}")
    if src.count < 2 or src.dtypes[0] != "int16":
        raise ValueError(f"{label}: {src.count} bands of {src.dtypes[0]}, expected a stack of int16")
    return Stack(src.read(), src.transform, crs)


def read_stack(path) -> Stack:
    with rasterio.open(path) as src:
        return _from_dataset(src, path)


def stack_from_bytes(content: bytes, label: str = "stack") -> Stack:
    with MemoryFile(content) as memory, memory.open() as src:
        return _from_dataset(src, label)


def classify(data: np.ndarray) -> Classes:
    """Fill, flagged and valid pixels of a stack, by the rule above."""
    fmask = data[-1].astype(np.int16)
    fill = (fmask == FMASK_FILL) | (data[:-1] == REFLECTANCE_FILL).any(axis=0)
    flagged = ~fill & ((fmask & MASK_BITS) != 0)
    return Classes(fill, flagged, ~fill & ~flagged)


def inside_polygon(shape: tuple[int, int], transform: rasterio.Affine, polygon) -> np.ndarray:
    """Pixels whose centre lies in `polygon` (EPSG:32615), the rule Phase 3 uses for CDL."""
    if polygon is None:
        return np.ones(shape, dtype=bool)
    with _RASTERIZE_LOCK:  # rasterio's in-memory rasters are not safe to create from several threads at once
        burned = rasterize([(mapping(polygon), 1)], out_shape=shape, transform=transform,
                           fill=0, all_touched=False, dtype="uint8")
    return burned.astype(bool)


def masked_reflectance(stack: Stack | str, polygon=None) -> MaskedStack:
    """Physical reflectance (x 0.0001) with every masked, fill or outside pixel set to NaN."""
    if not isinstance(stack, Stack):
        stack = read_stack(stack)
    classes = classify(stack.data)
    inside = inside_polygon(stack.data.shape[1:], stack.transform, polygon)
    keep = classes.valid & inside
    reflectance = np.where(keep, stack.data[:-1].astype(np.float32) * np.float32(SCALE), np.float32("nan"))
    return MaskedStack(reflectance.astype(np.float32), classes, inside, stack.transform, stack.crs)
