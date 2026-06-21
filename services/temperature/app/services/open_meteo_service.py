# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

from __future__ import annotations

import logging
import time
from threading import Lock

import pandas as pd
import requests

logger = logging.getLogger(__name__)


class OpenMeteoService:
    """Service to fetch historical daily temperature data from Open-Meteo archive API.

    The method implemented here returns a Pandas DataFrame with columns: `date`, `tmax`, `tmin`.
    """

    BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

    def __init__(self) -> None:
        self._session = requests.Session()
        self._cache: dict[tuple[int, float, float], pd.DataFrame] = {}
        self._cache_lock = Lock()

    @staticmethod
    def _cache_key(lat: float, lon: float, year: int) -> tuple[int, float, float]:
        # Round for stable cache hits while retaining locality precision.
        return (year, round(lat, 4), round(lon, 4))

    def get_daily_data(self, lat: float, lon: float, year: int) -> pd.DataFrame:
        """Fetch daily temperature max/min for a full year from Open-Meteo.

        Args:
            lat: Latitude in decimal degrees.
            lon: Longitude in decimal degrees.
            year: Year to fetch (e.g. 2023).

        Returns:
            pd.DataFrame with columns: `date` (datetime), `tmax`, `tmin` (floats).
        """
        key = self._cache_key(lat, lon, year)
        with self._cache_lock:
            cached = self._cache.get(key)
        if cached is not None:
            return cached.copy(deep=True)

        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": f"{year}-01-01",
            "end_date": f"{year}-12-31",
            "daily": "temperature_2m_max,temperature_2m_min",
            "timezone": "UTC",
        }

        retries = 3
        for attempt in range(retries + 1):
            try:
                resp = self._session.get(self.BASE_URL, params=params, timeout=30)
                if resp.status_code == 429:
                    retry_after_raw = resp.headers.get("Retry-After")
                    retry_after = float(retry_after_raw) if retry_after_raw else 0.0
                    backoff_s = retry_after if retry_after > 0 else 0.6 * (2**attempt)
                    if attempt < retries:
                        time.sleep(min(backoff_s, 8.0))
                        continue
                resp.raise_for_status()

                payload = resp.json()
                daily = payload.get("daily", {})
                times = daily.get("time", [])
                tmax = daily.get("temperature_2m_max", [])
                tmin = daily.get("temperature_2m_min", [])

                df = pd.DataFrame({"date": pd.to_datetime(times), "tmax": tmax, "tmin": tmin})
                df["tmax"] = pd.to_numeric(df["tmax"], errors="coerce")
                df["tmin"] = pd.to_numeric(df["tmin"], errors="coerce")

                if df.empty:
                    raise RuntimeError("OpenMeteo returned empty daily series")

                with self._cache_lock:
                    if len(self._cache) >= 256:
                        self._cache.pop(next(iter(self._cache)))
                    self._cache[key] = df.copy(deep=True)
                return df
            except Exception:
                if attempt >= retries:
                    logger.exception("OpenMeteo API request failed")
                    raise
                time.sleep(0.4 * (2**attempt))
