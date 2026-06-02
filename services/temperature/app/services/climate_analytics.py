from __future__ import annotations

import logging
from threading import Lock

import pandas as pd
from app.models.climate import (
    ClimateRecommendations,
    ClimateReport,
    ClimateSummary,
    MonthlyTemperature,
)
from app.services.imd_weather_service import IMDWeatherService
from app.services.open_meteo_service import OpenMeteoService

logger = logging.getLogger(__name__)


class ClimateAnalyticsService:
    """Service that composes IMD/OpenMeteo data and returns structured climate reports."""

    def __init__(self) -> None:
        self.imd = IMDWeatherService()
        self.open_meteo = OpenMeteoService()
        self._profile_cache: dict[tuple[int, float, float], ClimateReport] = {}
        self._profile_cache_lock = Lock()

    @staticmethod
    def _to_celsius(f: float) -> float:
        return (f - 32.0) * 5.0 / 9.0

    def get_annual_thermal_profile(self, lat: float, lon: float, year: int) -> ClimateReport:
        """Return a `ClimateReport` for the requested location and year.

        Steps:
          - Try IMD first, on failure fall back to OpenMeteo.
          - Normalize to Celsius if data appears to be Fahrenheit.
          - Aggregate monthly means and compute summary statistics.
          - Produce simple recommendations.
        """
        cache_key = (int(year), round(lat, 4), round(lon, 4))
        with self._profile_cache_lock:
            cached = self._profile_cache.get(cache_key)
        if cached is not None:
            return cached.model_copy(deep=True)

        # 1) Data fetch with IMD preferred
        try:
            df = self.imd.get_daily_data(lat, lon, year)
        except Exception as exc:
            logger.warning("IMD fetch failed: %s - falling back to OpenMeteo", exc)
            df = self.open_meteo.get_daily_data(lat, lon, year)

        if df.empty:
            raise RuntimeError(
                "No daily temperature data available for the requested year/location"
            )

        # Normalize
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])

        # Detect Fahrenheit (mean > 50 deg). This is a heuristic.
        mean_overall = ((df["tmax"] + df["tmin"]) / 2.0).mean()
        if mean_overall is None:
            raise RuntimeError("Unable to compute mean temperature from dataset")

        if mean_overall > 50.0:
            df["tmax"] = df["tmax"].apply(self._to_celsius)
            df["tmin"] = df["tmin"].apply(self._to_celsius)

        # Compute monthly aggregates
        df["month"] = df["date"].dt.month
        monthly = (
            df.groupby("month")
            .agg(avg_tmax=("tmax", "mean"), avg_tmin=("tmin", "mean"))
            .reset_index()
        )

        monthly_list: list[MonthlyTemperature] = []
        for row in monthly.itertuples(index=False):
            monthly_list.append(
                MonthlyTemperature(
                    month=int(row.month), avg_tmax=float(row.avg_tmax), avg_tmin=float(row.avg_tmin)
                )
            )

        # Summary statistics
        annual_avg = float(((df["tmax"] + df["tmin"]) / 2.0).mean())
        peak_max = float(df["tmax"].max())
        lowest_min = float(df["tmin"].min())

        summary = ClimateSummary(
            annual_avg_temp=annual_avg, peak_max_temp=peak_max, lowest_min_temp=lowest_min
        )

        # Recommendations based on annual average (thresholds tuned for Indian context)
        if annual_avg > 24.0:
            status = "Hot / High Thermal Mass"
            material = "Use high-reflectance, low-absorptance exterior materials; consider shading and thermal mass strategies."
            insulation = "Focus on reflective roofing, night-ventilation and selective insulation; emphasize cooling strategies."
        elif annual_avg < 18.0:
            status = "Cold / Insulation"
            material = "Use high-insulation envelope materials and minimize thermal bridges."
            insulation = "Prioritise continuous insulation, airtightness and increased glazing U-value performance."
        else:
            status = "Moderate"
            material = "Balanced materials with moderate thermal mass and moderate solar control."
            insulation = "Use standard insulation practices with emphasis on passive solar gain where beneficial."

        recommendations = ClimateRecommendations(
            material_suggestion=material,
            insulation_strategy=insulation,
            thermal_comfort_status=status,
        )

        report = ClimateReport(
            monthly_data=monthly_list, summary=summary, recommendations=recommendations
        )
        with self._profile_cache_lock:
            if len(self._profile_cache) >= 256:
                self._profile_cache.pop(next(iter(self._profile_cache)))
            self._profile_cache[cache_key] = report
        return report.model_copy(deep=True)
