# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class IMDWeatherService:
    """Service to read IMD .grd files from the local `data/` directory using `imdlib`.

    Behavior:
      - Tries to find a `.grd` file in `data/` matching the requested year.
      - Uses `imdlib` reader functions (attempts common function names) to produce a DataFrame.
      - If reading for `year` fails (e.g. "recent data" not available), automatically attempts `year - 1`.

    NOTE: IMD integration is Enhancement-Later. No .grd files ship with the repo.
    All production requests fall through to Open-Meteo. See AGENTS.md.
    """

    def __init__(self, data_dir: Path | None = None):
        # Prefer explicit arg, then IMD_DATA_DIR env var, then repo_root/data
        if data_dir is not None:
            self.data_dir = Path(data_dir).resolve()
        elif os.environ.get("IMD_DATA_DIR"):
            self.data_dir = Path(os.environ["IMD_DATA_DIR"]).resolve()
        else:
            repo_root = Path(__file__).resolve().parents[2]
            self.data_dir = (repo_root / "data").resolve()

    def _find_grd_for_year(self, year: int) -> Path:
        pattern = f"*{year}*.grd"
        matches = list(self.data_dir.glob(pattern))
        if not matches:
            raise FileNotFoundError(f"No .grd files found for year {year} in {self.data_dir}")
        return matches[0]

    def _call_reader(self, reader: Callable, path: Path):
        # Call reader and try to normalize to a DataFrame
        out = reader(str(path))
        # If reader returned a DataFrame-like object, normalize
        if isinstance(out, pd.DataFrame):
            return out
        if hasattr(out, "to_dataframe"):
            return out.to_dataframe()
        if hasattr(out, "to_pandas"):
            return out.to_pandas()
        # Some libs return dict/series-like structures
        if hasattr(out, "items") or isinstance(out, dict):
            return pd.DataFrame(out)
        raise RuntimeError(
            "imdlib returned an unsupported object; please adapt or extend this adapter"
        )

    def _load_year(self, year: int) -> pd.DataFrame:
        try:
            import imdlib
        except Exception:  # pragma: no cover - optional dependency
            logger.exception("Failed to import imdlib")
            raise

        path = self._find_grd_for_year(year)

        # Try several common reader entrypoints on imdlib
        for reader_name in ("read_grd", "open", "load", "read"):
            reader = getattr(imdlib, reader_name, None)
            if not callable(reader):
                continue
            try:
                df = self._call_reader(reader, path)
                # Ensure expected columns exist (best-effort mapping)
                df = self._normalize_columns(df)
                return df
            except Exception:
                logger.debug("Reader %s failed for %s", reader_name, path, exc_info=True)

        # If we get here nothing worked
        raise RuntimeError(f"Could not read .grd file {path} with available imdlib readers")

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        # Ensure there's a datetime column
        cols = [c.lower() for c in df.columns]
        mapping = {}
        # date/time
        for candidate in ("date", "time", "day", "datetime"):
            for c in df.columns:
                if candidate in c.lower():
                    mapping[c] = "date"
                    break
            if "date" in mapping.values():
                break

        # max/min temperature
        for c in df.columns:
            lc = c.lower()
            if ("max" in lc and "temp" in lc) or ("temperature_2m_max" in lc) or lc == "tmax":
                mapping[c] = "tmax"
            elif ("min" in lc and "temp" in lc) or ("temperature_2m_min" in lc) or lc == "tmin":
                mapping[c] = "tmin"

        df = df.rename(columns=mapping)

        if "date" not in df.columns:
            # Try to build a date column from index
            if hasattr(df.index, "to_datetime"):
                df = df.reset_index()
            if df.index.dtype == object or "time" in " ".join(cols):
                try:
                    df["date"] = pd.to_datetime(df.index)
                except Exception:
                    pass

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])

        # Ensure tmax/tmin exist (may raise if missing)
        if "tmax" not in df.columns or "tmin" not in df.columns:
            raise RuntimeError("Unable to find tmax/tmin columns in IMD file after normalization")

        # Keep only the required columns
        return df[["date", "tmax", "tmin"]].copy()

    def get_daily_data(self, lat: float, lon: float, year: int) -> pd.DataFrame:
        """Public API: returns DataFrame(date, tmax, tmin). If reading `year` fails, try `year - 1`.

        Note: IMD .grd file formats and `imdlib` APIs vary; this adapter attempts a best-effort
        normalization and will raise clear errors when it cannot proceed.
        """
        try:
            return self._load_year(year)
        except Exception as exc:  # pragma: no cover - runtime fallback
            logger.warning(
                "Reading IMD data for %s failed: %s; attempting fallback to %s", year, exc, year - 1
            )
            try:
                return self._load_year(year - 1)
            except Exception:
                logger.exception("Fallback to previous year failed")
                raise
