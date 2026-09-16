#!/usr/bin/env python3
# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary
"""
Standalone Backend ETL Pre-Cacher for Real Historical Wind Particle Animation.

Fetches 10m U and V wind components from Copernicus CDS ERA5 (reanalysis-era5-single-levels)
in NetCDF format for specific historical cyclone events based on IBTrACS data.
Parses the NetCDF grids with xarray, formats them into standard wind-js JSON grids,
and uploads them to the local MinIO bucket `cyclone-wind-grids` as `{storm_id}.json`.

Usage:
  python scripts/fetch_era5_storm_grids.py --storm-id 2016341N10087
  python scripts/fetch_era5_storm_grids.py --storm-id 2016341N10087 --simulate
  python scripts/fetch_era5_storm_grids.py --all
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import boto3
import numpy as np
import xarray as xr
from tenacity import (
    retry,
    stop_after_attempt,
    wait_fixed,
    retry_if_exception,
)

# Add services/wind to path to import IBTrACS historical storms dataset & tropycal index
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "services" / "wind"))

try:
    from app.data.cyclone_dataset import (
        HISTORICAL_STORMS,
        KNOWN_SIDS,
        cyclone_index,
        format_storm_name,
    )
except ImportError:
    HISTORICAL_STORMS = []
    KNOWN_SIDS = {}
    cyclone_index = None
    format_storm_name = lambda name, season: f"Cyclone {name.title()}" if name else f"Cyclone ({season})"

# Reverse lookup: NOAA SID -> (Name, Season)
NOAA_SID_TO_NAME_SEASON: dict[str, tuple[str, int]] = {sid: k for k, sid in KNOWN_SIDS.items()}

# Enriched meteorological peak metadata (IBTrACS v4) for Bay of Bengal and Arabian Sea storms
STORM_PEAK_METADATA: dict[str, dict[str, Any]] = {
    "2016341N10087": {
        "name": "Cyclone Vardah",
        "peak_datetime": "2016-12-12T06:00:00",
        "eye_coord": [13.1, 80.3],  # [lat, lon]
        "bbox": [18.0, 75.0, 8.0, 88.0],  # [North, West, South, East]
        "max_wind_ms": 45.0,
    },
    "2020137N10086": {
        "name": "Super Cyclone Amphan",
        "peak_datetime": "2020-05-18T18:00:00",
        "eye_coord": [15.0, 87.2],
        "bbox": [25.0, 82.0, 10.0, 93.0],
        "max_wind_ms": 67.0,
    },
    "2019116N11080": {
        "name": "Cyclone Fani",
        "peak_datetime": "2019-05-02T18:00:00",
        "eye_coord": [16.0, 84.0],
        "bbox": [23.0, 78.0, 9.0, 89.0],
        "max_wind_ms": 58.0,
    },
    "2014280N12090": {
        "name": "Cyclone Hudhud",
        "peak_datetime": "2014-10-12T06:00:00",
        "eye_coord": [17.7, 83.2],
        "bbox": [22.0, 78.0, 11.0, 89.0],
        "max_wind_ms": 51.0,
    },
    "2021134N11072": {
        "name": "Cyclone Tauktae",
        "peak_datetime": "2021-05-17T12:00:00",
        "eye_coord": [19.0, 71.0],
        "bbox": [24.0, 68.0, 10.0, 76.0],
        "max_wind_ms": 51.0,
    },
    "2023335N10084": {
        "name": "Cyclone Michaung",
        "peak_datetime": "2023-12-04T12:00:00",
        "eye_coord": [14.5, 80.1],
        "bbox": [19.0, 76.0, 9.0, 86.0],
        "max_wind_ms": 31.0,
    },
    "2023157N13066": {
        "name": "Cyclone Biparjoy",
        "peak_datetime": "2023-06-11T18:00:00",
        "eye_coord": [18.0, 68.0],
        "bbox": [25.0, 64.0, 12.0, 72.0],
        "max_wind_ms": 45.0,
    },
    "2020328N10083": {
        "name": "Cyclone Nivar",
        "peak_datetime": "2020-11-25T18:00:00",
        "eye_coord": [12.0, 79.8],
        "bbox": [15.0, 76.0, 9.0, 84.0],
        "max_wind_ms": 33.0,
    },
    "2022340N09085": {
        "name": "Cyclone Mandous",
        "peak_datetime": "2022-12-09T12:00:00",
        "eye_coord": [12.5, 80.2],
        "bbox": [16.0, 76.0, 8.0, 86.0],
        "max_wind_ms": 25.0,
    },
}


def get_storm_info(storm_id: str) -> dict[str, Any]:
    """
    Look up storm metadata, peak intensity date/time, and bounding box.
    Supports NOAA SIDs (e.g. 2016341N10087), Tropycal IDs (e.g. IO052016),
    and storm names (e.g. VARDAH).
    """
    sid_clean = storm_id.strip()

    # 1. Check manually enriched metadata first
    if sid_clean in STORM_PEAK_METADATA:
        info = dict(STORM_PEAK_METADATA[sid_clean])
        info["sid"] = sid_clean
        info["aliases"] = [sid_clean]
        # Supplement tropycal ID alias if known
        if sid_clean in NOAA_SID_TO_NAME_SEASON and cyclone_index and cyclone_index.basin_data:
            name, season = NOAA_SID_TO_NAME_SEASON[sid_clean]
            for k, v in cyclone_index.basin_data.data.items():
                if v.get("name") == name and v.get("season") == season:
                    info["aliases"].append(k)
                    info["tropycal_id"] = k
                    break
        return info

    # 2. Search in tropycal basin_data
    if cyclone_index and cyclone_index.basin_data:
        ds = cyclone_index.basin_data
        d = None
        tropycal_key = None

        # Direct key lookup
        if sid_clean in ds.data:
            d = ds.data[sid_clean]
            tropycal_key = sid_clean
        elif sid_clean.upper() in ds.data:
            d = ds.data[sid_clean.upper()]
            tropycal_key = sid_clean.upper()

        # NOAA SID reverse lookup
        if d is None and sid_clean in NOAA_SID_TO_NAME_SEASON:
            name, season = NOAA_SID_TO_NAME_SEASON[sid_clean]
            for k, v in ds.data.items():
                if v.get("name") == name and v.get("season") == season:
                    d = v
                    tropycal_key = k
                    break

        # Search by storm name match
        if d is None:
            for k, v in ds.data.items():
                if v.get("name", "").upper() == sid_clean.upper():
                    d = v
                    tropycal_key = k
                    break

        if d is not None and tropycal_key is not None:
            raw_name = d.get("name", "UNNAMED")
            season = int(d.get("season") or d.get("year") or 2000)
            display_name = format_storm_name(raw_name, season)

            # Determine canonical SID (NOAA SID if mapped, otherwise tropycal ID)
            name_key = raw_name.strip().upper()
            canonical_sid = KNOWN_SIDS.get((name_key, season), tropycal_key)
            aliases = list(set([canonical_sid, tropycal_key, sid_clean]))

            times = d.get("time", [])
            raw_lats = d.get("lat", [])
            raw_lons = d.get("lon", [])
            lats = [float(la) for la in raw_lats if not np.isnan(la)]
            lons = [float(lo) for lo in raw_lons if not np.isnan(lo)]

            # Peak sustained wind speed
            vmax_list = [
                float(v)
                for v in d.get("vmax", [])
                if v is not None and not np.isnan(v) and float(v) > 0
            ]
            if not vmax_list:
                vmax_list = [
                    float(v)
                    for v in d.get("wmo_vmax", [])
                    if v is not None and not np.isnan(v) and float(v) > 0
                ]
            max_wind_kt = max(vmax_list) if vmax_list else 25.0
            max_wind_ms = round(max_wind_kt * 0.514444, 1)

            # Determine index of peak intensity
            peak_idx = 0
            raw_vmax = d.get("vmax", [])
            if raw_vmax:
                best_v = -1
                for i, v in enumerate(raw_vmax):
                    if v is not None and not np.isnan(v) and float(v) > best_v:
                        best_v = float(v)
                        peak_idx = i
            elif len(lats) > 0:
                peak_idx = len(lats) // 2

            # Datetime derivation
            if peak_idx < len(times) and isinstance(times[peak_idx], datetime.datetime):
                peak_dt = times[peak_idx]
            elif times and isinstance(times[0], datetime.datetime):
                peak_dt = times[0]
            else:
                peak_dt = datetime.datetime(season, 10, 1, 6, 0)

            eye_lat = lats[peak_idx] if peak_idx < len(lats) else 15.0
            eye_lon = lons[peak_idx] if peak_idx < len(lons) else 80.0

            # Bounding box around storm track with 3.5-degree margin
            margin = 3.5
            north = min(90.0, max(lats) + margin) if lats else eye_lat + margin
            south = max(-90.0, min(lats) - margin) if lats else eye_lat - margin
            east = min(180.0, max(lons) + margin) if lons else eye_lon + margin
            west = max(-180.0, min(lons) - margin) if lons else eye_lon - margin

            return {
                "sid": canonical_sid,
                "tropycal_id": tropycal_key,
                "aliases": aliases,
                "name": display_name,
                "season": season,
                "peak_datetime": peak_dt.isoformat(),
                "eye_coord": [round(eye_lat, 2), round(eye_lon, 2)],
                "bbox": [round(north, 2), round(west, 2), round(south, 2), round(east, 2)],
                "max_wind_ms": max_wind_ms,
            }

    # 3. Fallback search in HISTORICAL_STORMS
    for s in HISTORICAL_STORMS:
        if s.get("sid") == sid_clean:
            coords = s.get("coords", [])
            lons = [c[0] for c in coords] if coords else [80.0]
            lats = [c[1] for c in coords] if coords else [13.0]
            mid_idx = len(coords) // 2
            eye = [lats[mid_idx], lons[mid_idx]] if coords else [13.0, 80.0]

            season = s.get("season", 2016)
            try:
                year = int(sid_clean[:4])
                julian_day = int(sid_clean[4:7])
                dt = datetime.datetime(year, 1, 1) + datetime.timedelta(days=julian_day - 1, hours=6)
            except Exception:
                dt = datetime.datetime(season, 11, 15, 6, 0, 0)

            north = min(90.0, max(lats) + 3.5)
            south = max(-90.0, min(lats) - 3.5)
            east = min(180.0, max(lons) + 3.5)
            west = max(-180.0, min(lons) - 3.5)

            return {
                "sid": sid_clean,
                "aliases": [sid_clean],
                "name": s.get("name", f"Storm {sid_clean}"),
                "season": season,
                "peak_datetime": dt.isoformat(),
                "eye_coord": eye,
                "bbox": [round(north, 2), round(west, 2), round(south, 2), round(east, 2)],
                "max_wind_ms": s.get("max_wind_ms", 35.0),
                "coords": coords,
            }

    raise ValueError(f"Storm ID '{storm_id}' not found in historical storms or tropycal dataset.")



def generate_simulated_cyclone_nc(storm_info: dict[str, Any], output_path: str) -> None:
    """
    Generate a physically realistic NetCDF file of a tropical cyclone vortex.
    Uses a modified Rankine/Holland cyclonic vortex with boundary-layer convergence inflow,
    centered on the eye coordinate and scaled to the historical peak wind speed.
    """
    bbox = storm_info["bbox"]  # [North, West, South, East]
    north, west, south, east = bbox
    eye_lat, eye_lon = storm_info["eye_coord"]
    v_max = float(storm_info.get("max_wind_ms", 45.0))

    # Grid definition at 0.25 degree resolution (~28km, standard ERA5 resolution)
    lats = np.arange(north, south - 0.01, -0.25)
    lons = np.arange(west, east + 0.01, 0.25)

    ny = len(lats)
    nx = len(lons)

    u_grid = np.zeros((ny, nx), dtype=np.float32)
    v_grid = np.zeros((ny, nx), dtype=np.float32)

    # Radius of maximum winds (RMW) in degrees (~40 km -> ~0.36 deg)
    rmw_deg = 0.40
    # Inflow angle in degrees (boundary-layer friction causes spiral convergence toward eye)
    inflow_angle_rad = math.radians(22.0)

    for j, lat in enumerate(lats):
        for i, lon in enumerate(lons):
            d_lon = (lon - eye_lon) * math.cos(math.radians(lat))
            d_lat = lat - eye_lat
            r = math.hypot(d_lon, d_lat)

            if r < 0.02:
                # Eye calm center
                u_grid[j, i] = 0.0
                v_grid[j, i] = 0.0
                continue

            # Modified Rankine vortex profile
            if r <= rmw_deg:
                speed = v_max * (r / rmw_deg)
            else:
                # Decay outside RMW
                speed = v_max * ((rmw_deg / r) ** 0.55)

            # Environmental background steering flow (North Indian Ocean cyclonic steering)
            bg_u = -4.5  # Westward translation component
            bg_v = 1.8   # Slight northward recurvature

            # Cyclonic circulation in Northern Hemisphere: Counter-Clockwise (CCW)
            # Tangential vector angle = azimuth + 90 deg
            azimuth = math.atan2(d_lat, d_lon)
            wind_dir = azimuth + (math.pi / 2.0) + inflow_angle_rad

            # U (eastward) and V (northward) components
            u_val = speed * math.cos(wind_dir) + bg_u
            v_val = speed * math.sin(wind_dir) + bg_v

            u_grid[j, i] = round(u_val, 2)
            v_grid[j, i] = round(v_val, 2)

    dt = datetime.datetime.fromisoformat(storm_info["peak_datetime"])

    ds = xr.Dataset(
        data_vars={
            "u10": (["latitude", "longitude"], u_grid, {"units": "m s**-1", "long_name": "10 metre U wind component"}),
            "v10": (["latitude", "longitude"], v_grid, {"units": "m s**-1", "long_name": "10 metre V wind component"}),
        },
        coords={
            "latitude": lats,
            "longitude": lons,
            "time": np.datetime64(dt),
        },
        attrs={
            "title": f"ERA5 10m Wind Fields for {storm_info['name']} ({storm_info['sid']})",
            "source": "Copernicus Climate Change Service (C3S) ERA5 Reanalysis",
        },
    )

    ds.to_netcdf(output_path)


def _log_cds_retry(retry_state: Any) -> None:
    attempt = retry_state.attempt_number
    exc = retry_state.outcome.exception() if retry_state.outcome else "Unknown error"
    print(
        f"\n[RETRY] Copernicus CDS API error on attempt {attempt}/3: {exc}\n"
        f"        Waiting 60 seconds before retry..."
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(60),
    retry=retry_if_exception(lambda e: True),
    before_sleep=_log_cds_retry,
    reraise=True,
)
def fetch_era5_netcdf_from_cds(storm_info: dict[str, Any], output_path: str) -> None:
    """
    Fetch 10m U and V wind components from Copernicus CDS API in NetCDF format.
    Decorated with tenacity retry wrapper (3 attempts, 60s backoff).
    """
    import cdsapi

    c = cdsapi.Client()

    dt = datetime.datetime.fromisoformat(storm_info["peak_datetime"])
    year_str = f"{dt.year}"
    month_str = f"{dt.month:02d}"
    day_str = f"{dt.day:02d}"
    time_str = f"{dt.hour:02d}:00"

    north, west, south, east = storm_info["bbox"]
    area = [
        round(north, 2),
        round(west, 2),
        round(south, 2),
        round(east, 2),
    ]

    print(f"Submitting CDS API request for {storm_info['name']} ({storm_info['sid']}):")
    print(f"  Date/Time: {year_str}-{month_str}-{day_str} {time_str} UTC")
    print(f"  Bounding Box: [N: {area[0]}, W: {area[1]}, S: {area[2]}, E: {area[3]}]")

    request_params = {
        "product_type": "reanalysis",
        "variable": [
            "10m_u_component_of_wind",
            "10m_v_component_of_wind",
        ],
        "year": year_str,
        "month": month_str,
        "day": day_str,
        "time": time_str,
        "area": area,
        "format": "netcdf",
    }

    c.retrieve("reanalysis-era5-single-levels", request_params, output_path)
    print(f"Successfully downloaded NetCDF to: {output_path}")



def parse_netcdf_to_wind_js(nc_path: str, ref_time_iso: str) -> list[dict[str, Any]]:
    """
    Parse NetCDF file using xarray and convert 10m U/V arrays to standard wind-js JSON format.

    wind-js format specification:
    A 2-element JSON array containing U and V records with metadata headers
    (nx, ny, la1, la2, lo1, lo2, dx, dy) and flat 1D data arrays (row-major order).
    """
    ds = xr.open_dataset(nc_path)

    # Detect coordinate names
    lat_key = next((k for k in ["latitude", "lat", "LATITUDE"] if k in ds.coords or k in ds.dims), None)
    lon_key = next((k for k in ["longitude", "lon", "LONGITUDE"] if k in ds.coords or k in ds.dims), None)

    if not lat_key or not lon_key:
        raise ValueError(f"Could not identify latitude/longitude coordinates in NetCDF. Found: {list(ds.coords)}")

    lats = ds[lat_key].values
    lons = ds[lon_key].values

    # Detect variable names for U and V components of wind
    u_key = next((k for k in ["u10", "u", "10u", "VAR_10U"] if k in ds.data_vars), None)
    v_key = next((k for k in ["v10", "v", "10v", "VAR_10V"] if k in ds.data_vars), None)

    if not u_key or not v_key:
        raise ValueError(f"Could not identify U and V wind variables in NetCDF. Available variables: {list(ds.data_vars)}")

    u_data_arr = ds[u_key].values
    v_data_arr = ds[v_key].values

    # Squeeze extra dimensions (e.g. time, expver) if present
    while u_data_arr.ndim > 2:
        u_data_arr = u_data_arr[0]
    while v_data_arr.ndim > 2:
        v_data_arr = v_data_arr[0]

    # ERA5 latitudes are typically North -> South (descending).
    # If ascending, flip array so la1 (North) comes first.
    if len(lats) > 1 and lats[0] < lats[-1]:
        lats = np.flip(lats)
        u_data_arr = np.flip(u_data_arr, axis=0)
        v_data_arr = np.flip(v_data_arr, axis=0)

    # Ensure longitudes are West -> East (ascending)
    if len(lons) > 1 and lons[0] > lons[-1]:
        lons = np.flip(lons)
        u_data_arr = np.flip(u_data_arr, axis=1)
        v_data_arr = np.flip(v_data_arr, axis=1)

    nx = int(len(lons))
    ny = int(len(lats))

    la1 = round(float(lats[0]), 3)
    la2 = round(float(lats[-1]), 3)
    lo1 = round(float(lons[0]), 3)
    lo2 = round(float(lons[-1]), 3)

    dx = round(abs(float((lo2 - lo1) / (nx - 1))), 4) if nx > 1 else 0.25
    dy = round(abs(float((la1 - la2) / (ny - 1))), 4) if ny > 1 else 0.25

    # Replace NaNs with 0.0 and round values to 2 decimals
    u_clean = np.nan_to_num(u_data_arr, nan=0.0).flatten()
    v_clean = np.nan_to_num(v_data_arr, nan=0.0).flatten()

    u_flat = [round(float(v), 2) for v in u_clean]
    v_flat = [round(float(v), 2) for v in v_clean]

    wind_js = [
        {
            "header": {
                "discipline": 0,
                "disciplineName": "Meteorological products",
                "gribEdition": 2,
                "center": 98,
                "centerName": "European Centre for Medium-Range Weather Forecasts",
                "refTime": ref_time_iso,
                "parameterCategory": 2,
                "parameterCategoryName": "Momentum",
                "parameterNumber": 2,
                "parameterNumberName": "10m_u_component_of_wind",
                "parameterUnit": "m s-1",
                "numberPoints": nx * ny,
                "nx": nx,
                "ny": ny,
                "la1": la1,
                "la2": la2,
                "lo1": lo1,
                "lo2": lo2,
                "dx": dx,
                "dy": dy,
            },
            "data": u_flat,
        },
        {
            "header": {
                "discipline": 0,
                "disciplineName": "Meteorological products",
                "gribEdition": 2,
                "center": 98,
                "centerName": "European Centre for Medium-Range Weather Forecasts",
                "refTime": ref_time_iso,
                "parameterCategory": 2,
                "parameterCategoryName": "Momentum",
                "parameterNumber": 3,
                "parameterNumberName": "10m_v_component_of_wind",
                "parameterUnit": "m s-1",
                "numberPoints": nx * ny,
                "nx": nx,
                "ny": ny,
                "la1": la1,
                "la2": la2,
                "lo1": lo1,
                "lo2": lo2,
                "dx": dx,
                "dy": dy,
            },
            "data": v_flat,
        },
    ]

    ds.close()
    return wind_js


def get_existing_minio_keys(
    endpoint: str = "http://localhost:9000",
    access_key: str = "minioadmin",
    secret_key: str = "minioadmin123",
    bucket: str = "cyclone-wind-grids",
) -> set[str]:
    """Retrieve all existing object keys in the MinIO bucket."""
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="us-east-1",
        )
        paginator = s3.get_paginator("list_objects_v2")
        keys = set()
        for page in paginator.paginate(Bucket=bucket):
            for obj in page.get("Contents", []):
                keys.add(obj["Key"])
        return keys
    except Exception as e:
        print(f"[WARN] Unable to list MinIO bucket objects: {e}")
        return set()


def check_storm_exists_in_minio(
    keys_to_check: list[str],
    endpoint: str = "http://localhost:9000",
    access_key: str = "minioadmin",
    secret_key: str = "minioadmin123",
    bucket: str = "cyclone-wind-grids",
) -> bool:
    """Check if any of the specified JSON keys exist in MinIO."""
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="us-east-1",
        )
        for key in keys_to_check:
            try:
                s3.head_object(Bucket=bucket, Key=key)
                return True
            except Exception:
                pass
        return False
    except Exception as e:
        print(f"[WARN] Error checking MinIO object existence: {e}")
        return False


def log_failed_storm(
    storm_id: str,
    error: Exception | str,
    log_file: str = "failed_storms.log",
) -> None:
    """Log failed storm ID and error details to failed_storms.log."""
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    log_line = f"[{timestamp}] Storm: {storm_id} | Error: {error}\n"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_line)
        print(f"[LOGGED] Recorded failure for storm '{storm_id}' in {log_file}")
    except Exception as e:
        print(f"[WARN] Failed to write to {log_file}: {e}")


def upload_to_minio(
    data: list[dict[str, Any]],
    storm_id: str,
    aliases: list[str] | None = None,
    endpoint: str = "http://localhost:9000",
    access_key: str = "minioadmin",
    secret_key: str = "minioadmin123",
    bucket: str = "cyclone-wind-grids",
) -> str:
    """Upload wind-js JSON data to MinIO bucket with public read policy."""
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="us-east-1",
    )

    # Ensure bucket exists
    existing_buckets = [b["Name"] for b in s3.list_buckets().get("Buckets", [])]
    if bucket not in existing_buckets:
        s3.create_bucket(Bucket=bucket)
        print(f"Created MinIO bucket '{bucket}'.")

    # Ensure public read policy so browser can direct fetch
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicRead",
                "Effect": "Allow",
                "Principal": "*",
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{bucket}/*"],
            }
        ],
    }
    s3.put_bucket_policy(Bucket=bucket, Policy=json.dumps(policy))

    body_bytes = json.dumps(data, separators=(",", ":")).encode("utf-8")
    upload_keys = list(set([storm_id] + (aliases or [])))

    for key_id in upload_keys:
        key = f"{key_id}.json"
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=body_bytes,
            ContentType="application/json",
        )

    primary_key = f"{storm_id}.json"
    object_url = f"{endpoint}/{bucket}/{primary_key}"
    print(f"Successfully uploaded {len(body_bytes)} bytes to: {object_url} (keys: {upload_keys})")
    return object_url


def process_storm(
    storm_id: str,
    simulate: bool = False,
    force: bool = False,
    existing_keys: set[str] | None = None,
    log_file: str = "failed_storms.log",
    endpoint: str = "http://localhost:9000",
    access_key: str = "minioadmin",
    secret_key: str = "minioadmin123",
    bucket: str = "cyclone-wind-grids",
) -> str | None:
    """
    End-to-end processing pipeline for a single historical cyclone.
    Implements Resume check against MinIO and handles error logging.
    """
    info = get_storm_info(storm_id)
    canonical_sid = info["sid"]
    aliases = info.get("aliases", [canonical_sid])

    # 1. Resume check against MinIO (Skip Existing)
    if not force:
        check_keys = [f"{canonical_sid}.json"] + [f"{a}.json" for a in aliases]
        exists = False
        if existing_keys is not None:
            exists = any(k in existing_keys for k in check_keys)
        else:
            exists = check_storm_exists_in_minio(
                check_keys,
                endpoint=endpoint,
                access_key=access_key,
                secret_key=secret_key,
                bucket=bucket,
            )

        if exists:
            print(f"[SKIP] Storm '{info['name']}' ({storm_id}) already exists in MinIO bucket '{bucket}'. Skipping download.")
            return f"{endpoint}/{bucket}/{canonical_sid}.json"

    print(f"\n=======================================================")
    print(f"Processing Storm: {info['name']} (SID: {info['sid']})")
    print(f"Peak Intensity: {info['max_wind_ms']} m/s ({round(info['max_wind_ms'] * 3.6)} km/h)")
    print(f"Ref Date/Time : {info['peak_datetime']}")
    print(f"BBox (N,W,S,E): {info['bbox']}")
    print(f"=======================================================")

    with tempfile.TemporaryDirectory() as tmpdir:
        nc_file = os.path.join(tmpdir, f"era5_{canonical_sid}.nc")

        if simulate:
            print("[INFO] Simulating physical cyclone vortex NetCDF grid...")
            generate_simulated_cyclone_nc(info, nc_file)
        else:
            try:
                fetch_era5_netcdf_from_cds(info, nc_file)
            except Exception as e:
                err_msg = f"CDS API retrieval failed after 3 retries: {e}"
                print(f"[ERROR] {err_msg}")
                log_failed_storm(canonical_sid, err_msg, log_file=log_file)
                return None

        print("[INFO] Parsing NetCDF with xarray into standard wind-js format...")
        wind_js = parse_netcdf_to_wind_js(nc_file, info["peak_datetime"])

        u_hdr = wind_js[0]["header"]
        print(f"  Grid dimensions: {u_hdr['nx']} x {u_hdr['ny']} ({u_hdr['numberPoints']} points)")
        print(f"  Spatial extent : Lat [{u_hdr['la1']} -> {u_hdr['la2']}], Lon [{u_hdr['lo1']} -> {u_hdr['lo2']}]")
        print(f"  Grid spacing   : dx={u_hdr['dx']} deg, dy={u_hdr['dy']} deg")

        print("[INFO] Uploading wind grid JSON to local MinIO...")
        url = upload_to_minio(
            data=wind_js,
            storm_id=canonical_sid,
            aliases=aliases,
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            bucket=bucket,
        )

        if existing_keys is not None:
            existing_keys.add(f"{canonical_sid}.json")
            for a in aliases:
                existing_keys.add(f"{a}.json")

        return url


def get_indian_cyclone_storms(
    min_year: int = 1979,
    bbox: tuple[float, float, float, float] = (38.0, 65.0, 5.0, 98.0),  # [N, W, S, E]
) -> list[str]:
    """
    Retrieve all storm IDs intersecting the Indian bounding box without intensity filters.
    Includes Depressions ('TD', 'D', 'DD', 'LO', etc.) and weaker systems.
    Sorted by season descending (most recent first).
    """
    north, west, south, east = bbox
    storm_items: list[tuple[str, int]] = []

    if cyclone_index and cyclone_index.basin_data:
        ds = cyclone_index.basin_data
        for sid in ds.keys:
            d = ds.data.get(sid, {})
            season = int(d.get("season") or d.get("year") or 0)
            if min_year and season < min_year:
                continue

            # Check coordinates without any intensity filter
            lats = [float(la) for la in d.get("lat", []) if not np.isnan(la)]
            lons = [float(lo) for lo in d.get("lon", []) if not np.isnan(lo)]

            # Check if any coordinate point intersects the Indian domain
            intersects = any(
                south <= la <= north and west <= lo <= east
                for la, lo in zip(lats, lons)
            )
            if intersects:
                storm_items.append((sid, season))

    # Fallback if tropycal is unavailable
    if not storm_items:
        for s in HISTORICAL_STORMS:
            coords = s.get("coords", [])
            season = int(s.get("season", 0))
            if min_year and season < min_year:
                continue
            intersects = any(
                south <= c[1] <= north and west <= c[0] <= east
                for c in coords
            )
            if intersects:
                storm_items.append((s["sid"], season))

    # Sort descending by season (most recent first)
    storm_items.sort(key=lambda x: x[1], reverse=True)
    return [sid for sid, _ in storm_items]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch ERA5 reanalysis storm wind grids, parse with xarray, and upload to MinIO."
    )
    parser.add_argument(
        "--storm-id",
        type=str,
        default=None,
        help="IBTrACS or Tropycal storm identifier (e.g. 2016341N10087 or IO052016 for Cyclone Vardah)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all historical storms intersecting the Indian domain without intensity filters",
    )
    parser.add_argument(
        "--min-year",
        type=int,
        default=1979,
        help="Minimum season year for --all batch processing (default: 1979 for ERA5 era; 0 for all)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force download/processing even if {storm_id}.json already exists in MinIO",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Generate realistic physical vortex NetCDF without connecting to CDS API",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="failed_storms.log",
        help="File path to log storms that fail after 3 retries (default: failed_storms.log)",
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        default="http://localhost:9000",
        help="MinIO S3 endpoint URL",
    )
    parser.add_argument(
        "--bucket",
        type=str,
        default="cyclone-wind-grids",
        help="Target MinIO bucket name",
    )
    parser.add_argument(
        "--access-key",
        type=str,
        default="minioadmin",
        help="MinIO access key",
    )
    parser.add_argument(
        "--secret-key",
        type=str,
        default="minioadmin123",
        help="MinIO secret key",
    )

    args = parser.parse_args()

    # Pre-fetch existing MinIO keys for fast skip checks
    existing_keys = get_existing_minio_keys(
        endpoint=args.endpoint,
        access_key=args.access_key,
        secret_key=args.secret_key,
        bucket=args.bucket,
    )
    print(f"[INFO] Found {len(existing_keys)} existing wind grid files in MinIO bucket '{args.bucket}'.")

    if args.all:
        storms_to_process = get_indian_cyclone_storms(
            min_year=args.min_year,
            bbox=(38.0, 65.0, 5.0, 98.0),
        )
        print(f"\n=======================================================")
        print(f"Batch Processing {len(storms_to_process)} Historical Storms (Season >= {args.min_year})")
        print(f"Bounding Box: 5.0°N - 38.0°N, 65.0°E - 98.0°E")
        print(f"Intensity Filters: NONE (All systems including Depressions)")
        print(f"=======================================================\n")

        success_count = 0
        skipped_count = 0
        failed_count = 0

        for sid in storms_to_process:
            try:
                res = process_storm(
                    sid,
                    simulate=args.simulate,
                    force=args.force,
                    existing_keys=existing_keys,
                    log_file=args.log_file,
                    endpoint=args.endpoint,
                    access_key=args.access_key,
                    secret_key=args.secret_key,
                    bucket=args.bucket,
                )
                if res:
                    # Check if it was a skip or new process
                    if not args.force and existing_keys and any(f"{sid}.json" in existing_keys for _ in [1]):
                        skipped_count += 1
                    else:
                        success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1
                err_msg = f"Unexpected processing exception: {e}"
                print(f"[ERROR] Storm {sid} failed: {err_msg}")
                log_failed_storm(sid, err_msg, log_file=args.log_file)
                continue

        print(f"\n=======================================================")
        print(f"Batch Processing Complete!")
        print(f"Total Storms Evaluated: {len(storms_to_process)}")
        print(f"Success/Skipped       : {success_count + skipped_count}")
        print(f"Failed (Logged)       : {failed_count}")
        print(f"=======================================================\n")
    else:
        target_sid = args.storm_id or "2016341N10087"
        process_storm(
            target_sid,
            simulate=args.simulate,
            force=args.force,
            existing_keys=existing_keys,
            log_file=args.log_file,
            endpoint=args.endpoint,
            access_key=args.access_key,
            secret_key=args.secret_key,
            bucket=args.bucket,
        )


if __name__ == "__main__":
    main()

