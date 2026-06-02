"""
IMD imdlib validation tests — Enhancement-Later.

These tests document the CORRECT imdlib API usage and are marked xfail
because:
  1. No .grd data files exist in the repository.
  2. The IMDWeatherService adapter uses wrong reader names ('read_grd', 'open',
     'load', 'read') — none of which exist on the imdlib module.

When this feature is promoted to Enhancement-Ready:
  - Rewrite IMDWeatherService to use imdlib.get_data() + imdlib.open_data()
  - Provision .grd files via IMD data pipeline
  - Remove xfail marks

Run:
    pytest tests/temperature_imd_validation.py -v
"""
from __future__ import annotations

import os
import tempfile

import pytest


@pytest.mark.xfail(
    reason=(
        "Enhancement-Later: no .grd files in repo; "
        "IMDWeatherService adapter uses wrong API names. "
        "Fix adapter + provision data before enabling."
    ),
    strict=False,
)
def test_imdlib_download_and_read():
    """
    Validates correct imdlib API:
      1. imdlib.get_data() downloads .GRD file to target directory
      2. imdlib.open_data().get_xarray() reads it
      3. Lat/lon coordinate extraction returns a finite float
    """
    try:
        import imdlib
    except ImportError:
        pytest.skip("imdlib not installed")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Download one year of tmax data
        imdlib.get_data("tmax", 2023, 2023, "yearwise", "stn", tmpdir)

        ds = imdlib.open_data("tmax", 2023, 2023, "stn", tmpdir).get_xarray()
        # Delhi: 28.6°N, 77.2°E
        val = float(ds.sel(lat=28.6, lon=77.2, method="nearest").values[0])
        assert 0.0 < val < 60.0, f"Unexpected tmax value: {val}"


@pytest.mark.xfail(
    reason="Enhancement-Later: IMDWeatherService uses wrong reader names; adapter needs rewrite.",
    strict=False,
)
def test_imd_service_adapter_reads_grd():
    """
    Validates that IMDWeatherService.get_daily_data() returns a DataFrame
    with 'date', 'tmax', 'tmin' columns when given a real .grd file.
    """
    try:
        import imdlib  # noqa: F401
    except ImportError:
        pytest.skip("imdlib not installed")

    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parents[1] / "services" / "temperature"))

    try:
        from app.services.imd_weather_service import IMDWeatherService
    except ImportError:
        pytest.skip("app/ not on sys.path — run from SAT root")

    with tempfile.TemporaryDirectory() as tmpdir:
        import imdlib
        imdlib.get_data("tmax", 2023, 2023, "yearwise", "stn", tmpdir)
        imdlib.get_data("tmin", 2023, 2023, "yearwise", "stn", tmpdir)

        svc = IMDWeatherService(data_dir=tmpdir)
        df = svc.get_daily_data(lat=28.6, lon=77.2, year=2023)

        assert not df.empty
        assert "date" in df.columns
        assert "tmax" in df.columns
        assert "tmin" in df.columns
        assert (df["tmax"] > 0).any()
