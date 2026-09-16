# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

from __future__ import annotations

import logging
import math
import pickle
from pathlib import Path
from typing import Any

import numpy as np
from scipy.spatial import cKDTree
import tropycal.tracks as tracks

logger = logging.getLogger("cyclone_dataset")

# Cache path for serialized tropycal North Indian TrackDataset
CACHE_FILE = Path(__file__).parent / "tropycal_north_indian.pkl"


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points in kilometers."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# Name + Season to NOAA IBTrACS 13-character SID mapping for cross-referencing pre-cached grids
KNOWN_SIDS: dict[tuple[str, int], str] = {
    ("AMPHAN", 2020): "2020137N10086",
    ("FANI", 2019): "2019116N11080",
    ("VARDAH", 2016): "2016341N10087",
    ("HUDHUD", 2014): "2014280N12090",
    ("TAUKTAE", 2021): "2021134N11072",
    ("NISARGA", 2020): "2020153N15071",
    ("PHAILIN", 2013): "2013280N12093",
    ("NIVAR", 2020): "2020328N10083",
    ("MANDOUS", 2022): "2022340N09085",
    ("MICHAUNG", 2023): "2023335N10084",
    ("BIPARJOY", 2023): "2023157N13066",
    ("GAJA", 2018): "2018314N11087",
    ("THANE", 2011): "2011360N10084",
    ("LAILA", 2010): "2010137N10086",
    ("JAL", 2010): "2010308N10083",
    ("SIDR", 2007): "2007315N10088",
    ("ODISHA", 1999): "1999298N17089",
    ("BOB 06", 1999): "1999298N17089",
    ("1999 ODISHA SUPER CYCLONE", 1999): "1999298N17089",
    ("MACHILIPATNAM", 1990): "1990124N10084",
    ("1990 MACHILIPATNAM CYCLONE", 1990): "1990124N10084",
    ("ANDHRA PRADESH", 1977): "1977319N12086",
    ("1977 ANDHRA PRADESH CYCLONE", 1977): "1977319N12086",
    ("BHOLA", 1970): "1970312N10087",
    ("1970 BHOLA CYCLONE", 1970): "1970312N10087",
    ("SRIHARIKOTA", 1985): "1985310N11085",
    ("1985 SRIHARIKOTA CYCLONE", 1985): "1985310N11085",
    ("KAVALI", 1989): "1989143N12085",
    ("1989 KAVALI CYCLONE", 1989): "1989143N12085",
    ("CUDDALORE", 2000): "2000299N11084",
    ("2000 CUDDALORE CYCLONE", 2000): "2000299N11084",
    ("TAMIL NADU", 2005): "2005332N10083",
    ("2005 TAMIL NADU DEEP DEPRESSION", 2005): "2005332N10083",
    ("MADRAS", 1975): "1975305N12085",
    ("1975 MADRAS CYCLONE", 1975): "1975305N12085",
    ("GUJARAT", 1982): "1982315N11086",
    ("1982 GUJARAT CYCLONE", 1982): "1982315N11086",
    ("GUJARAT", 1998): "1998155N14068",
    ("1998 GUJARAT CYCLONE", 1998): "1998155N14068",
}


def format_storm_name(raw_name: str, season: int) -> str:
    """Format cyclone name into standard human-readable display string."""
    name_clean = (raw_name or "").strip()
    upper = name_clean.upper()
    if not upper or upper in ("UNNAMED", "NOT NAMED"):
        return f"Cyclone ({season})"
    if upper.startswith("CYCLONE ") or upper.startswith("SUPER CYCLONE "):
        return name_clean.title()
    return f"Cyclone {name_clean.title()}"


# Fallback historical storms list if tropycal initialization fails completely (e.g. offline CI)
HISTORICAL_STORMS: list[dict[str, Any]] = [
    {
        "sid": "2020137N10086",
        "name": "Super Cyclone Amphan",
        "season": 2020,
        "max_wind_ms": 67.0,
        "min_pressure_hpa": 920.0,
        "coords": [[86.0, 10.0], [86.5, 12.5], [87.2, 15.0], [88.0, 18.2], [88.3, 21.6], [88.8, 24.0]],
    },
    {
        "sid": "2019116N11080",
        "name": "Cyclone Fani",
        "season": 2019,
        "max_wind_ms": 58.0,
        "min_pressure_hpa": 932.0,
        "coords": [[80.5, 11.0], [82.0, 13.5], [84.0, 16.0], [85.5, 19.5], [86.5, 21.0]],
    },
    {
        "sid": "2016341N10087",
        "name": "Cyclone Vardah",
        "season": 2016,
        "max_wind_ms": 45.0,
        "min_pressure_hpa": 975.0,
        "coords": [[90.0, 11.5], [86.5, 12.2], [83.0, 12.8], [80.3, 13.1], [78.5, 13.3]],
    },
    {
        "sid": "2014280N12090",
        "name": "Cyclone Hudhud",
        "season": 2014,
        "max_wind_ms": 51.0,
        "min_pressure_hpa": 950.0,
        "coords": [[92.0, 12.0], [88.0, 14.0], [84.5, 16.5], [83.2, 17.7], [81.0, 19.5]],
    },
    {
        "sid": "2021134N11072",
        "name": "Cyclone Tauktae",
        "season": 2021,
        "max_wind_ms": 51.0,
        "min_pressure_hpa": 950.0,
        "coords": [[73.0, 11.0], [72.5, 14.0], [71.5, 17.0], [71.0, 19.0], [71.1, 21.0]],
    },
    {
        "sid": "2020153N15071",
        "name": "Cyclone Nisarga",
        "season": 2020,
        "max_wind_ms": 31.0,
        "min_pressure_hpa": 984.0,
        "coords": [[71.0, 15.0], [72.0, 17.0], [73.0, 18.5], [74.0, 19.8]],
    },
    {
        "sid": "2013280N12093",
        "name": "Cyclone Phailin",
        "season": 2013,
        "max_wind_ms": 60.0,
        "min_pressure_hpa": 940.0,
        "coords": [[92.5, 12.0], [88.5, 14.5], [85.5, 17.5], [84.8, 19.3], [84.0, 21.0]],
    },
    {
        "sid": "2020328N10083",
        "name": "Cyclone Nivar",
        "season": 2020,
        "max_wind_ms": 33.0,
        "min_pressure_hpa": 980.0,
        "coords": [[83.5, 10.0], [81.5, 11.2], [79.8, 12.0], [79.0, 12.8]],
    },
    {
        "sid": "2022340N09085",
        "name": "Cyclone Mandous",
        "season": 2022,
        "max_wind_ms": 25.0,
        "min_pressure_hpa": 990.0,
        "coords": [[85.0, 9.5], [82.5, 10.8], [80.2, 12.5], [79.2, 13.0]],
    },
    {
        "sid": "2023335N10084",
        "name": "Cyclone Michaung",
        "season": 2023,
        "max_wind_ms": 31.0,
        "min_pressure_hpa": 986.0,
        "coords": [[84.0, 10.5], [81.2, 12.8], [80.1, 14.5], [80.2, 16.0]],
    },
    {
        "sid": "2023157N13066",
        "name": "Cyclone Biparjoy",
        "season": 2023,
        "max_wind_ms": 45.0,
        "min_pressure_hpa": 958.0,
        "coords": [[66.0, 13.0], [67.5, 16.0], [68.5, 20.0], [69.5, 23.0]],
    },
]


def load_tropycal_dataset() -> tracks.TrackDataset | None:
    """Load cached TrackDataset or fetch North Indian basin IBTrACS data via tropycal."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "rb") as f:
                ds = pickle.load(f)
                logger.info(f"Loaded tropycal North Indian TrackDataset from cache ({CACHE_FILE})")
                return ds
        except Exception as e:
            logger.warning(f"Failed to load cached tropycal TrackDataset: {e}")

    try:
        logger.info("Initializing tropycal TrackDataset(basin='north_indian', source='ibtracs')...")
        ds = tracks.TrackDataset(basin="north_indian", source="ibtracs")
        # Warm up interpolation cache to ensure instant subsequent spatial queries
        ds.analogs_from_point((13.0827, 80.2707), radius=10.0, units="km")
        try:
            with open(CACHE_FILE, "wb") as f:
                pickle.dump(ds, f)
            logger.info(f"Persisted tropycal TrackDataset cache to {CACHE_FILE}")
        except Exception as cache_err:
            logger.warning(f"Could not persist cache: {cache_err}")
        return ds
    except Exception as e:
        logger.error(f"Failed to initialize tropycal TrackDataset from NOAA: {e}")
        return None


class CycloneSpatialIndex:
    """Tropycal-backed spatial index for North Indian Ocean cyclone buffer queries."""

    def __init__(self) -> None:
        self.basin_data = load_tropycal_dataset()
        self._init_nearest_neighbor_index()

    def _init_nearest_neighbor_index(self) -> None:
        """Build 3D spherical cKDTree over all historical track observations for sub-millisecond NN queries."""
        if self.basin_data is None:
            self._nn_tree = None
            self._nn_sids = []
            return

        all_lats: list[float] = []
        all_lons: list[float] = []
        all_sids: list[str] = []

        for sid in self.basin_data.keys:
            d = self.basin_data.data.get(sid, {})
            lats = d.get("lat", [])
            lons = d.get("lon", [])
            for la, lo in zip(lats, lons):
                if not np.isnan(la) and not np.isnan(lo):
                    all_lats.append(float(la))
                    all_lons.append(float(lo))
                    all_sids.append(sid)

        if all_lats:
            lats_r = np.radians(np.array(all_lats))
            lons_r = np.radians(np.array(all_lons))
            pts_3d = np.column_stack([
                np.cos(lats_r) * np.cos(lons_r),
                np.cos(lats_r) * np.sin(lons_r),
                np.sin(lats_r),
            ])
            self._nn_tree = cKDTree(pts_3d)
            self._nn_sids = all_sids
            logger.info(f"Initialized 3D cKDTree with {len(all_lats)} historical track points for NN distance queries.")
        else:
            self._nn_tree = None
            self._nn_sids = []

    def nearest_neighbor_distance_km(self, lat: float, lon: float) -> float:
        """Find the unconditional distance (in km) to the absolute closest historical storm track in the database."""
        if getattr(self, "_nn_tree", None) is not None:
            qlat = np.radians(lat)
            qlon = np.radians(lon)
            qpt = np.array([np.cos(qlat) * np.cos(qlon), np.cos(qlat) * np.sin(qlon), np.sin(qlat)])
            d_chord, _ = self._nn_tree.query(qpt)
            arc = 2.0 * np.arcsin(np.clip(d_chord / 2.0, 0.0, 1.0))
            return round(float(6371.0 * arc), 1)

        # Fallback to embedded representative historical storms
        return round(min(
            haversine_distance_km(lat, lon, pt[1], pt[0])
            for s in HISTORICAL_STORMS
            for pt in s["coords"]
        ), 1)

    def query_radius(
        self, lat: float, lon: float, radius_km: float
    ) -> list[dict[str, Any]]:
        """Find historical storms whose track passes within radius_km of (lat, lon)."""
        if self.basin_data is None:
            # Fallback to embedded representative historical storms
            logger.warning("tropycal dataset unavailable; using fallback historical storms.")
            return self._query_fallback(lat, lon, radius_km)

        try:
            # Spatial search using tropycal analogs_from_point
            analog_results = self.basin_data.analogs_from_point(
                point=(lat, lon), radius=radius_km, units="km"
            )
        except Exception as err:
            logger.error(f"Error querying tropycal analogs_from_point: {err}")
            return self._query_fallback(lat, lon, radius_km)

        results: list[dict[str, Any]] = []

        for storm_id, dist_km in analog_results.items():
            try:
                storm = self.basin_data.get_storm(storm_id)
            except Exception:
                continue

            season = int(getattr(storm, "season", getattr(storm, "year", 2000)))
            raw_name = str(getattr(storm, "name", "UNNAMED"))
            display_name = format_storm_name(raw_name, season)

            # Resolve 13-character NOAA SID if known, else use tropycal storm.id (e.g. IO052016)
            name_key = raw_name.strip().upper()
            sid = KNOWN_SIDS.get((name_key, season), storm_id)

            # Maximum recorded sustained wind speed in m/s (1 kt = 0.514444 m/s)
            vmax_arr = getattr(storm, "vmax", None)
            valid_vmax = [
                float(v)
                for v in (vmax_arr if vmax_arr is not None else [])
                if not np.isnan(v) and float(v) > 0
            ]
            if not valid_vmax:
                wmo_v = getattr(storm, "wmo_vmax", None)
                valid_vmax = [
                    float(v)
                    for v in (wmo_v if wmo_v is not None else [])
                    if not np.isnan(v) and float(v) > 0
                ]

            max_wind_kt = max(valid_vmax) if valid_vmax else 0.0
            max_wind_ms = round(max_wind_kt * 0.514444, 1)

            # Minimum atmospheric pressure in hPa
            mslp_arr = getattr(storm, "mslp", None)
            valid_mslp = [
                float(p)
                for p in (mslp_arr if mslp_arr is not None else [])
                if not np.isnan(p) and float(p) > 850
            ]
            if not valid_mslp:
                wmo_p = getattr(storm, "wmo_mslp", None)
                valid_mslp = [
                    float(p)
                    for p in (wmo_p if wmo_p is not None else [])
                    if not np.isnan(p) and float(p) > 850
                ]
            min_pressure_hpa = round(min(valid_mslp), 1) if valid_mslp else 1000.0

            # Extract track coordinates in [lon, lat] format
            lats = getattr(storm, "lat", [])
            lons = getattr(storm, "lon", [])
            coords: list[list[float]] = []
            for lo, la in zip(lons, lats):
                if np.isnan(lo) or np.isnan(la):
                    continue
                lo_val = round(float(lo), 3)
                la_val = round(float(la), 3)
                if not coords or coords[-1] != [lo_val, la_val]:
                    coords.append([lo_val, la_val])

            if len(coords) < 2:
                # If only 1 observation point exists, create minimal segment
                if coords:
                    coords.append([round(coords[0][0] + 0.01, 3), coords[0][1]])
                else:
                    continue

            results.append(
                {
                    "sid": sid,
                    "name": display_name,
                    "season": season,
                    "max_wind_ms": max_wind_ms,
                    "min_pressure_hpa": min_pressure_hpa,
                    "closest_distance_km": round(float(dist_km), 1),
                    "coords": coords,
                }
            )

        # Sort closest approach distance first
        results.sort(key=lambda s: s["closest_distance_km"])
        return results

    def _query_fallback(
        self, lat: float, lon: float, radius_km: float
    ) -> list[dict[str, Any]]:
        """Fallback radius search against embedded storms."""
        results = []
        for storm in HISTORICAL_STORMS:
            # Calculate min distance to storm points
            min_d = min(
                haversine_distance_km(lat, lon, pt[1], pt[0]) for pt in storm["coords"]
            )
            if min_d <= radius_km:
                sc = dict(storm)
                sc["closest_distance_km"] = round(min_d, 1)
                results.append(sc)
        results.sort(key=lambda s: s["closest_distance_km"])
        return results


# Global singleton index
cyclone_index = CycloneSpatialIndex()
