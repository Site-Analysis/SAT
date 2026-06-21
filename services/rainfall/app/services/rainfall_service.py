# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

try:
    import ee
except ImportError:
    ee = None  # type: ignore[assignment,misc]

from app.models.rainfall import (
    AnomalyResponse,
    ClimateProfileResponse,
    RainfallArchiveDaily,
    RainfallArchiveDailyUnits,
    RainfallArchiveResponse,
    RainfallDateRange,
    RainfallSummaryRequest,
    RainfallSummaryResponse,
    SeasonalityResponse,
    SiteAnalysisResponse,
    SuitabilityScores,
)
from app.settings import RainfallSettings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DailySeries:
    dates: list[str]
    precipitation_mm: list[float]


class RainfallService:
    def __init__(self, settings: RainfallSettings | None = None) -> None:
        self.settings = settings or RainfallSettings()
        self._gee_initialized = False
        if self.settings.gee_project_id and self.settings.gee_service_account_key_path:
            self._initialize_gee()

    def _initialize_gee(self) -> None:
        if ee is None:
            logger.warning("earthengine-api not installed; GEE features disabled")
            return
        try:
            credentials = ee.ServiceAccountCredentials(
                self.settings.gee_service_account_email, self.settings.gee_service_account_key_path
            )
            ee.Initialize(credentials, project=self.settings.gee_project_id)
            self._gee_initialized = True
            logger.info("GEE initialized successfully")
        except Exception as exc:
            logger.error("Failed to initialize GEE: %s", exc)
            self._gee_initialized = False

    def get_archive(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        source: str | None = None,
    ) -> RainfallArchiveResponse:
        resolved_source = source or self.settings.default_source
        series = self._fetch_chirps_daily_series(latitude, longitude, start_date, end_date)

        return RainfallArchiveResponse(
            latitude=latitude,
            longitude=longitude,
            timezone="UTC",
            daily_units=RainfallArchiveDailyUnits(),
            daily=RainfallArchiveDaily(
                time=series.dates,
                precipitation_sum=series.precipitation_mm,
            ),
            source=resolved_source,
        )

    def get_summary(
        self,
        request: RainfallSummaryRequest,
        source: str | None = None,
    ) -> RainfallSummaryResponse:
        resolved_source = source or self.settings.default_source
        latitude, longitude = self._resolve_point(request)
        start_date = date.fromisoformat(request.start_date)
        end_date = date.fromisoformat(request.end_date)
        series = self._fetch_chirps_daily_series(latitude, longitude, start_date, end_date)

        total = float(sum(series.precipitation_mm))
        count = len(series.precipitation_mm)
        mean = total / count if count else 0.0
        max_daily = max(series.precipitation_mm) if series.precipitation_mm else 0.0
        rainy_days = sum(1 for v in series.precipitation_mm if v > 0.1)
        dry_days = count - rainy_days

        return RainfallSummaryResponse(
            total_rainfall_mm=round(total, 2),
            mean_daily_rainfall_mm=round(mean, 2),
            max_daily_rainfall_mm=round(max_daily, 2),
            rainy_days=rainy_days,
            dry_days=dry_days,
            date_range=RainfallDateRange(
                start_date=request.start_date,
                end_date=request.end_date,
            ),
            source=resolved_source,
        )

    def get_climate_profile(self, latitude: float, longitude: float) -> ClimateProfileResponse:
        """Analyze long-term climate profile from CHIRPS data (30 years)."""
        end_date = date.today()
        start_date = end_date.replace(year=end_date.year - 30)

        try:
            series = self._fetch_chirps_daily_series(latitude, longitude, start_date, end_date)
            monthly_totals = self._aggregate_to_monthly(series)

            annual_mean = sum(monthly_totals.values()) / 12 if monthly_totals else 0.0
            wettest_month = max(monthly_totals, key=monthly_totals.get) if monthly_totals else "6"
            driest_month = min(monthly_totals, key=monthly_totals.get) if monthly_totals else "1"

            values_list = list(monthly_totals.values())
            mean_val = sum(values_list) / len(values_list) if values_list else 1.0
            variance = (
                sum((x - mean_val) ** 2 for x in values_list) / len(values_list)
                if values_list
                else 0.0
            )
            std_dev = variance**0.5
            variability = (std_dev / mean_val) if mean_val > 0 else 0.0
            variability = min(1.0, max(0.0, variability))

            monsoon_rainfall = sum([monthly_totals.get(str(m), 0.0) for m in [9, 10, 11]])
            monsoon_strength = (monsoon_rainfall / annual_mean * 100) if annual_mean > 0 else 0.0
            monsoon_strength = min(100.0, max(0.0, monsoon_strength))

            reliability = max(0.0, 100.0 - variability * 100.0)

            climate_class = self._classify_climate(annual_mean, monsoon_strength)

            return ClimateProfileResponse(
                latitude=latitude,
                longitude=longitude,
                annual_rainfall_mm=round(annual_mean, 1),
                wettest_month=wettest_month,
                driest_month=driest_month,
                rainfall_variability=round(variability, 3),
                monsoon_strength=round(monsoon_strength, 1),
                climate_classification=climate_class,
                rainfall_reliability_score=round(reliability, 1),
                datasets=["CHIRPS Daily (UCSB-CHG)"],
            )
        except Exception as exc:
            logger.error("Climate profile analysis failed: %s", exc)
            raise ValueError(f"Unable to analyze climate profile: {exc}") from exc

    def get_anomaly(self, latitude: float, longitude: float, days: int = 30) -> AnomalyResponse:
        """Calculate rainfall anomaly for current period vs long-term average."""
        end_date = date.today()
        current_start = end_date - timedelta(days=days)

        try:
            current_series = self._fetch_chirps_daily_series(
                latitude, longitude, current_start, end_date
            )
            current_rainfall = sum(current_series.precipitation_mm)

            reference_start = end_date - timedelta(days=days + 365 * 10)
            reference_end = end_date - timedelta(days=365 * 10)
            reference_series = self._fetch_chirps_daily_series(
                latitude, longitude, reference_start, reference_end
            )
            reference_rainfall = sum(reference_series.precipitation_mm)
            reference_daily = reference_rainfall / (len(reference_series.precipitation_mm) or 1)
            reference_normal = reference_daily * days

            anomaly_pct = (
                ((current_rainfall - reference_normal) / reference_normal * 100)
                if reference_normal > 0
                else 0.0
            )

            if anomaly_pct < -50:
                category = "Very Dry"
            elif anomaly_pct < -10:
                category = "Dry"
            elif anomaly_pct <= 10:
                category = "Normal"
            elif anomaly_pct <= 50:
                category = "Wet"
            else:
                category = "Very Wet"

            return AnomalyResponse(
                latitude=latitude,
                longitude=longitude,
                period_label=f"Last {days} days",
                current_period_rainfall_mm=round(current_rainfall, 1),
                long_term_average_mm=round(reference_normal, 1),
                anomaly_percent=round(anomaly_pct, 1),
                anomaly_category=category,  # type: ignore[arg-type]
                datasets=["CHIRPS Daily (UCSB-CHG)"],
            )
        except Exception as exc:
            logger.error("Anomaly analysis failed: %s", exc)
            raise ValueError(f"Unable to calculate anomaly: {exc}") from exc

    def get_seasonality(self, latitude: float, longitude: float) -> SeasonalityResponse:
        """Analyze seasonal rainfall patterns from 10-year CHIRPS data."""
        end_date = date.today()
        start_date = end_date.replace(year=end_date.year - 10)

        try:
            series = self._fetch_chirps_daily_series(latitude, longitude, start_date, end_date)
            seasonal_totals = self._aggregate_to_seasonal(series)

            total_annual = sum(seasonal_totals.values())
            seasonal_pct = {
                k: (v / total_annual * 100) if total_annual > 0 else 0.0
                for k, v in seasonal_totals.items()
            }

            concentration = self._calculate_concentration_index(seasonal_totals.values())

            return SeasonalityResponse(
                latitude=latitude,
                longitude=longitude,
                summer_rainfall_mm=round(seasonal_totals.get("summer", 0.0), 1),
                monsoon_rainfall_mm=round(seasonal_totals.get("monsoon", 0.0), 1),
                winter_rainfall_mm=round(seasonal_totals.get("winter", 0.0), 1),
                spring_rainfall_mm=round(seasonal_totals.get("spring", 0.0), 1),
                seasonal_distribution={k: round(v, 1) for k, v in seasonal_pct.items()},
                rainfall_concentration_index=round(concentration, 3),
                datasets=["CHIRPS Daily (UCSB-CHG)"],
            )
        except Exception as exc:
            logger.error("Seasonality analysis failed: %s", exc)
            raise ValueError(f"Unable to analyze seasonality: {exc}") from exc

    def get_site_analysis(
        self, latitude: float, longitude: float, radius_meters: int = 5000
    ) -> SiteAnalysisResponse:
        """Comprehensive site analysis for SAT: rainfall, trends, suitability, and recommendations."""
        end_date = date.today()
        start_10yr = end_date.replace(year=end_date.year - 10)
        start_5yr = end_date.replace(year=end_date.year - 5)
        start_1yr = end_date.replace(year=end_date.year - 1)

        try:
            series_1yr = self._fetch_chirps_daily_series(latitude, longitude, start_1yr, end_date)
            series_5yr = self._fetch_chirps_daily_series(latitude, longitude, start_5yr, end_date)
            series_10yr = self._fetch_chirps_daily_series(latitude, longitude, start_10yr, end_date)

            annual_rainfall_mm = sum(series_1yr.precipitation_mm)
            seasonal_totals = self._aggregate_to_seasonal(series_1yr)

            trend_5yr = self._calculate_trend_percent_per_year(series_5yr)
            trend_10yr = self._calculate_trend_percent_per_year(series_10yr)

            if trend_5yr > 2.0:
                trend_dir = "increasing"
            elif trend_5yr < -2.0:
                trend_dir = "decreasing"
            else:
                trend_dir = "stable"

            dry_day_freq = (
                sum(1 for v in series_1yr.precipitation_mm if v < 0.1)
                / len(series_1yr.precipitation_mm)
                * 100
                if series_1yr.precipitation_mm
                else 0.0
            )

            drought_risk = self._assess_drought_risk(dry_day_freq, annual_rainfall_mm, trend_5yr)
            runoff_potential = self._calculate_runoff_potential(annual_rainfall_mm, seasonal_totals)
            flood_susceptibility = self._calculate_flood_susceptibility(
                annual_rainfall_mm, seasonal_totals, dry_day_freq
            )
            water_availability = self._calculate_water_availability(
                annual_rainfall_mm, dry_day_freq
            )

            suitability = self._calculate_suitability_scores(
                annual_rainfall_mm, seasonal_totals, dry_day_freq, trend_5yr
            )

            recommendations = self._generate_recommendations(
                annual_rainfall_mm,
                seasonal_totals,
                drought_risk,
                runoff_potential,
                water_availability,
            )

            return SiteAnalysisResponse(
                latitude=latitude,
                longitude=longitude,
                radius_meters=radius_meters,
                annual_rainfall_mm=round(annual_rainfall_mm, 1),
                summer_rainfall_mm=round(seasonal_totals.get("summer", 0.0), 1),
                monsoon_rainfall_mm=round(seasonal_totals.get("monsoon", 0.0), 1),
                winter_rainfall_mm=round(seasonal_totals.get("winter", 0.0), 1),
                spring_rainfall_mm=round(seasonal_totals.get("spring", 0.0), 1),
                rainfall_trend_5yr_percent=round(trend_5yr, 2),
                rainfall_trend_10yr_percent=round(trend_10yr, 2),
                trend_direction=trend_dir,  # type: ignore[arg-type]
                drought_risk_level=drought_risk,  # type: ignore[arg-type]
                dry_day_frequency=round(dry_day_freq, 1),
                runoff_potential=round(runoff_potential, 1),
                flood_susceptibility_contribution=round(flood_susceptibility, 1),
                water_availability_score=round(water_availability, 1),
                suitability_scores=suitability,
                recommendations=recommendations,
                datasets=["CHIRPS Daily (UCSB-CHG)"],
            )
        except Exception as exc:
            logger.error("Site analysis failed: %s", exc)
            raise ValueError(f"Unable to perform site analysis: {exc}") from exc

    # Helper analytics methods

    def _aggregate_to_monthly(self, series: DailySeries) -> dict[str, float]:
        """Aggregate daily series to monthly totals."""
        monthly = {}
        for date_str, value in zip(series.dates, series.precipitation_mm):
            try:
                d = date.fromisoformat(date_str)
                month_key = str(d.month)
                monthly[month_key] = monthly.get(month_key, 0.0) + value
            except ValueError:
                continue
        return monthly

    def _aggregate_to_seasonal(self, series: DailySeries) -> dict[str, float]:
        """Aggregate daily series to seasonal totals (Northern Hemisphere)."""
        seasonal = {"summer": 0.0, "monsoon": 0.0, "winter": 0.0, "spring": 0.0}
        for date_str, value in zip(series.dates, series.precipitation_mm):
            try:
                d = date.fromisoformat(date_str)
                month = d.month
                if month in [6, 7, 8]:
                    seasonal["summer"] += value
                elif month in [9, 10, 11]:
                    seasonal["monsoon"] += value
                elif month in [12, 1, 2]:
                    seasonal["winter"] += value
                else:
                    seasonal["spring"] += value
            except ValueError:
                continue
        return seasonal

    def _calculate_concentration_index(self, seasonal_values: list[float] | Any) -> float:
        """Calculate rainfall concentration index (0=uniform, 1=extreme)."""
        seasonal_list = list(seasonal_values) if seasonal_values else [0.0, 0.0, 0.0, 0.0]
        total = sum(seasonal_list)
        if total == 0:
            return 0.0
        normalized = [v / total for v in seasonal_list]
        sum_squared = sum(v**2 for v in normalized)
        concentration = (sum_squared - 0.25) / 0.75
        return min(1.0, max(0.0, concentration))

    def _calculate_trend_percent_per_year(self, series: DailySeries) -> float:
        """Calculate linear trend as % change per year."""
        if not series.precipitation_mm or len(series.precipitation_mm) < 2:
            return 0.0

        values = series.precipitation_mm
        n = len(values)
        x = list(range(n))
        mean_x = sum(x) / n
        mean_y = sum(values) / n

        numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))

        if denominator == 0:
            return 0.0

        slope = numerator / denominator
        days_per_year = 365.25
        trend_per_year = slope * days_per_year
        pct_change = (trend_per_year / mean_y * 100) if mean_y > 0 else 0.0
        return pct_change

    def _classify_climate(self, annual_rainfall_mm: float, monsoon_pct: float) -> str:
        """Classify climate using simplified Köppen-Geiger rules."""
        if annual_rainfall_mm < 250:
            return "BW (Desert)"
        if annual_rainfall_mm < 500:
            return "BS (Steppe)"
        if annual_rainfall_mm < 1000:
            if monsoon_pct > 40:
                return "Am (Monsoon)"
            return "Af (Tropical Wet)"
        if annual_rainfall_mm < 2000:
            if monsoon_pct > 50:
                return "Cw (Temperate Monsoon)"
            return "Cfa (Humid Subtropical)"
        return "Af (Tropical Rainforest)"

    def _assess_drought_risk(
        self, dry_day_freq: float, annual_rainfall_mm: float, trend_pct: float
    ) -> str:
        """Assess drought risk based on multiple factors."""
        if annual_rainfall_mm < 250 or dry_day_freq > 70 or trend_pct < -5:
            return "very_high"
        if annual_rainfall_mm < 500 or dry_day_freq > 60 or trend_pct < -2:
            return "high"
        if annual_rainfall_mm < 750 or dry_day_freq > 40 or trend_pct < 0:
            return "moderate"
        if annual_rainfall_mm < 1000 or dry_day_freq > 20:
            return "low"
        return "very_low"

    def _calculate_runoff_potential(
        self, annual_rainfall_mm: float, seasonal_totals: dict[str, float]
    ) -> float:
        """Calculate runoff potential (0-100). Higher = more runoff."""
        monsoon = seasonal_totals.get("monsoon", 0.0)
        summer = seasonal_totals.get("summer", 0.0)
        peak_season = max(monsoon, summer)

        runoff = (peak_season / max(annual_rainfall_mm, 1.0) * 100) + (annual_rainfall_mm / 100)
        return min(100.0, max(0.0, runoff))

    def _calculate_flood_susceptibility(
        self, annual_rainfall_mm: float, seasonal_totals: dict[str, float], dry_day_freq: float
    ) -> float:
        """Calculate flood susceptibility contribution (0-100)."""
        monsoon = seasonal_totals.get("monsoon", 0.0)
        intensity_factor = (monsoon / max(annual_rainfall_mm, 1.0)) * 100

        wet_season_intensity = intensity_factor * 0.6
        base_rainfall_factor = (annual_rainfall_mm / 100) * 0.3
        variability_factor = (100 - dry_day_freq) * 0.1

        susceptibility = wet_season_intensity + base_rainfall_factor + variability_factor
        return min(100.0, max(0.0, susceptibility))

    def _calculate_water_availability(
        self, annual_rainfall_mm: float, dry_day_freq: float
    ) -> float:
        """Calculate water availability score (0-100). Higher = more available."""
        rainfall_score = min(100.0, (annual_rainfall_mm / 500) * 100)
        reliability_score = (100 - dry_day_freq) * 0.5
        water_score = rainfall_score * 0.7 + reliability_score * 0.3
        return min(100.0, max(0.0, water_score))

    def _calculate_suitability_scores(
        self,
        annual_rainfall_mm: float,
        seasonal_totals: dict[str, float],
        dry_day_freq: float,
        trend_pct: float,
    ) -> SuitabilityScores:
        """Calculate multi-factor suitability scores for different site uses."""
        monsoon = seasonal_totals.get("monsoon", 0.0)
        winter = seasonal_totals.get("winter", 0.0)

        water_availability = self._calculate_water_availability(annual_rainfall_mm, dry_day_freq)

        agriculture_score = min(
            100.0,
            (annual_rainfall_mm / 600) * 100 * (1 + max(0, trend_pct) / 50)
            - abs(min(0, trend_pct)) * 2,
        )

        drainage_score = min(100.0, (dry_day_freq / 0.7) * 100)

        groundwater = min(
            100.0,
            (annual_rainfall_mm / 800) * 100 * (1 - (monsoon / max(annual_rainfall_mm, 1.0) * 0.5)),
        )

        infiltration_score = min(
            100.0, ((100 - dry_day_freq) / 2) + ((annual_rainfall_mm - winter) / 10)
        )

        return SuitabilityScores(
            water_availability_score=round(water_availability, 1),
            agriculture_score=round(agriculture_score, 1),
            drainage_score=round(drainage_score, 1),
            groundwater_recharge_score=round(groundwater, 1),
            infiltration_suitability_score=round(infiltration_score, 1),
        )

    def _generate_recommendations(
        self,
        annual_rainfall_mm: float,
        seasonal_totals: dict[str, float],
        drought_risk: str,
        runoff_potential: float,
        water_availability: float,
    ) -> list[str]:
        """Generate site-specific recommendations based on rainfall analysis."""
        recommendations: list[str] = []

        if drought_risk in ["very_high", "high"]:
            recommendations.append("High drought risk: implement water harvesting systems")
            recommendations.append("Consider drought-resistant vegetation and irrigation planning")

        if runoff_potential > 70:
            recommendations.append(
                "High runoff potential: implement stormwater management infrastructure"
            )
            recommendations.append("Design drainage systems for peak monsoon/summer flows")

        if water_availability > 70:
            recommendations.append(
                "Strong water availability: suitable for water-dependent activities"
            )
            recommendations.append("Consider rainwater harvesting and groundwater recharge")

        monsoon = seasonal_totals.get("monsoon", 0.0)
        if monsoon > annual_rainfall_mm * 0.4:
            recommendations.append(
                "Strong monsoon influence: plan for seasonal flooding and water abundance"
            )

        winter = seasonal_totals.get("winter", 0.0)
        if winter > monsoon and winter > annual_rainfall_mm * 0.4:
            recommendations.append("Winter rainfall dominant: plan irrigation for dry summer")

        if not recommendations:
            recommendations.append("Moderate rainfall with balanced seasonality")

        return recommendations

    def _fetch_chirps_daily_series(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> DailySeries:
        """Fetch CHIRPS Daily rainfall data from Google Earth Engine.

        Falls back to synthetic data if GEE is unavailable.
        """
        if end_date < start_date:
            raise ValueError("end_date must be on or after start_date")

        if self._gee_initialized and ee is not None:
            return self._fetch_chirps_from_gee(latitude, longitude, start_date, end_date)
        else:
            logger.warning("GEE not initialized; falling back to synthetic data")
            return self._generate_synthetic_series(latitude, longitude, start_date, end_date)

    def _fetch_chirps_from_gee(
        self, latitude: float, longitude: float, start_date: date, end_date: date
    ) -> DailySeries:
        """Fetch CHIRPS Daily data from GEE UCSB-CHG/CHIRPS/DAILY dataset."""
        try:
            point = ee.Geometry.Point([longitude, latitude])
            chirps = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterDate(
                start_date.isoformat(), (end_date + timedelta(days=1)).isoformat()
            )

            def extract_value(img: Any) -> dict[str, Any]:
                reduction = img.reduceRegion(reducer=ee.Reducer.first(), geometry=point, scale=5000)
                return reduction.set("date", img.date().format("YYYY-MM-dd"))

            daily_data = chirps.map(extract_value).getInfo()
            dates = []
            values = []
            if isinstance(daily_data, list):
                for feature in daily_data:
                    if isinstance(feature, dict):
                        date_str = feature.get("date")
                        precip = feature.get("precipitation")
                        if date_str and precip is not None:
                            dates.append(date_str)
                            values.append(max(0.0, float(precip)))
            return DailySeries(dates=dates, precipitation_mm=[round(v, 2) for v in values])
        except Exception as exc:
            logger.error("GEE CHIRPS fetch failed: %s; falling back to synthetic", exc)
            return self._generate_synthetic_series(latitude, longitude, start_date, end_date)

    def _generate_synthetic_series(
        self, latitude: float, longitude: float, start_date: date, end_date: date
    ) -> DailySeries:
        """Generate synthetic rainfall series as fallback."""
        import math

        if end_date < start_date:
            raise ValueError("end_date must be on or after start_date")
        dates: list[str] = []
        values: list[float] = []
        base = round((abs(latitude) + abs(longitude)) % 1.5, 2)
        current = start_date
        index = 0

        while current <= end_date:
            seasonal = math.sin(index / 3.5) + math.cos(index / 10.0)
            value = max(0.0, (seasonal + 1.5) * 2.0 + base)
            dates.append(current.isoformat())
            values.append(round(value, 2))
            current += timedelta(days=1)
            index += 1

        return DailySeries(dates=dates, precipitation_mm=values)

    def _resolve_point(self, request: RainfallSummaryRequest) -> tuple[float, float]:  # noqa: F841
        if request.latitude is not None and request.longitude is not None:
            return float(request.latitude), float(request.longitude)

        geometry = request.geometry
        if not geometry:
            raise ValueError("Either geometry or latitude/longitude must be provided")

        geom_type = str(geometry.get("type", ""))
        if geom_type == "Point":
            coords = geometry.get("coordinates", [])
            if not isinstance(coords, list) or len(coords) < 2:
                raise ValueError("Point geometry must include [lon, lat] coordinates")
            return float(coords[1]), float(coords[0])

        if geom_type == "Polygon":
            coords = geometry.get("coordinates", [])
            if not isinstance(coords, list) or not coords:
                raise ValueError("Polygon geometry must include coordinates")
            ring = coords[0]
            if not isinstance(ring, list) or len(ring) < 3:
                raise ValueError("Polygon geometry must include at least 3 points")
            lons = [float(pair[0]) for pair in ring if isinstance(pair, list) and len(pair) >= 2]
            lats = [float(pair[1]) for pair in ring if isinstance(pair, list) and len(pair) >= 2]
            if not lons or not lats:
                raise ValueError("Polygon geometry coordinates are invalid")
            return sum(lats) / len(lats), sum(lons) / len(lons)

        raise ValueError("Unsupported geometry type")
