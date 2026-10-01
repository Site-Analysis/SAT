# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

from __future__ import annotations

import base64
import struct
import zlib

import numpy as np
from rasterio.warp import transform
from skimage import measure

VIRIDIS_STOPS = ["#440154", "#31688e", "#35b779", "#fde725"]


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def viridis_color(value: float, min_value: float, max_value: float) -> str:
    if max_value <= min_value:
        return VIRIDIS_STOPS[0]
    t = max(0.0, min(1.0, (value - min_value) / (max_value - min_value)))
    scaled = t * (len(VIRIDIS_STOPS) - 1)
    idx = min(int(scaled), len(VIRIDIS_STOPS) - 2)
    frac = scaled - idx
    a = _hex_to_rgb(VIRIDIS_STOPS[idx])
    b = _hex_to_rgb(VIRIDIS_STOPS[idx + 1])
    return _rgb_to_hex(tuple(round(a[i] + (b[i] - a[i]) * frac) for i in range(3)))


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def encode_png_b64(gray: np.ndarray) -> str:
    image = np.nan_to_num(gray, nan=0).astype("uint8")
    height, width = image.shape
    raw = b"".join(b"\x00" + image[row].tobytes() for row in range(height))
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
        + _png_chunk(b"IDAT", zlib.compress(raw, 9))
        + _png_chunk(b"IEND", b"")
    )
    return base64.b64encode(png).decode("ascii")


def compute_hillshade(dem: np.ndarray, cellsize: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    gy, gx = np.gradient(dem, cellsize, cellsize)
    slope_rad = np.arctan(np.sqrt(gx * gx + gy * gy))
    aspect_rad = np.arctan2(gy, -gx)
    az_rad = np.radians(315)
    alt_rad = np.radians(45)
    hillshade = (
        np.cos(alt_rad) * np.cos(slope_rad)
        + np.sin(alt_rad) * np.sin(slope_rad) * np.cos(az_rad - aspect_rad)
    )
    hillshade = np.clip(hillshade * 255, 0, 255).astype("uint8")
    return hillshade, slope_rad, aspect_rad


def generate_contours(dem: np.ndarray, affine_transform, crs: str, interval: int) -> dict:
    if interval < 10:
        raise ValueError("Contour interval below minimum reliable threshold for available DEM resolution")
    if interval > 60:
        raise ValueError("Contour interval above maximum supported threshold")

    min_elev = float(np.nanmin(dem))
    max_elev = float(np.nanmax(dem))
    start = np.ceil(min_elev / interval) * interval
    levels = np.arange(start, max_elev + interval, interval)
    features = []
    for level in levels:
        for line in measure.find_contours(np.nan_to_num(dem, nan=min_elev), float(level)):
            if len(line) < 2:
                continue
            xs = []
            ys = []
            for row, col in line:
                x, y = affine_transform * (float(col), float(row))
                xs.append(x)
                ys.append(y)
            lons, lats = transform(crs, "EPSG:4326", xs, ys)
            coords = [[round(lon, 7), round(lat, 7)] for lon, lat in zip(lons, lats)]
            is_index = abs(float(level) % (interval * 5)) < 1e-6
            features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "elevation": round(float(level), 2),
                        "is_index": is_index,
                        "color": viridis_color(float(level), min_elev, max_elev),
                        "line_weight": 2 if is_index else 1,
                    },
                    "geometry": {"type": "LineString", "coordinates": coords},
                }
            )
    return {"type": "FeatureCollection", "features": features}
