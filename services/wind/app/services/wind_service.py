from __future__ import annotations

import math

from app.models.wind import (
    BuildingImpact,
    ComfortAnalysis,
    SeasonalAnalysis,
    WindAnalysis,
    WindMetadata,
    WindRequest,
)
from app.settings import WindSettings


class WindAnalysisService:
    def __init__(self, settings: WindSettings | None = None) -> None:
        self.settings = settings or WindSettings()

    def analyze(self, request: WindRequest) -> WindAnalysis:
        # TODO: Replace deterministic scoring with ERA5-Land or GEE wind climatology data
        avg_speed = self._average_wind_speed(request)
        max_speed = self._max_wind_speed(avg_speed)
        direction = self._prevailing_direction(request)
        category = self._wind_category(avg_speed)
        gust_risk = self._gust_risk(avg_speed)
        seasonal = self._seasonal_analysis(request)
        comfort = self._comfort_analysis(avg_speed)
        building = self._building_impact(avg_speed, direction)
        recommendations = self._recommendations(avg_speed, category, direction)

        metadata = WindMetadata(
            latitude=request.latitude,
            longitude=request.longitude,
            radius_meters=request.radius_meters,
            data_source=self.settings.data_source,
        )

        return WindAnalysis(
            average_wind_speed=round(avg_speed, 2),
            max_wind_speed=round(max_speed, 2),
            prevailing_direction=direction,
            wind_category=category,
            gust_risk=gust_risk,
            seasonal_analysis=seasonal,
            comfort_analysis=comfort,
            building_impact=building,
            recommendations=recommendations,
            metadata=metadata,
        )

    def _average_wind_speed(self, request: WindRequest) -> float:
        seed = abs(request.latitude) * 0.5 + abs(request.longitude) * 0.3
        seed += request.radius_meters / 1000.0
        raw = math.sin(seed * 0.37 + 1.2) * 0.5 + 0.5
        base = 3.0 + raw * 12.0
        return max(0.5, min(20.0, base))

    def _max_wind_speed(self, avg: float) -> float:
        return avg * 1.8 + 2.0

    def _prevailing_direction(self, request: WindRequest) -> str:
        directions = ["North", "Northeast", "East", "Southeast", "South", "Southwest", "West", "Northwest"]
        seed = (abs(request.latitude) + abs(request.longitude)) % 8.0
        idx = int(seed) % len(directions)
        return directions[idx]

    def _wind_category(self, speed: float) -> str:
        if speed < 2.0:
            return "Calm"
        if speed < 4.0:
            return "Light"
        if speed < 8.0:
            return "Moderate"
        if speed < 12.0:
            return "Strong"
        return "Very Strong"

    def _gust_risk(self, speed: float) -> str:
        if speed < 5.0:
            return "Low"
        if speed < 10.0:
            return "Moderate"
        return "High"

    def _seasonal_analysis(self, request: WindRequest) -> SeasonalAnalysis:
        base = self._average_wind_speed(request)
        summer = base * (0.8 + (abs(request.latitude) % 3) * 0.1)
        monsoon = base * (1.3 + (abs(request.longitude) % 2) * 0.1)
        winter = base * (1.1 + (abs(request.latitude) % 2) * 0.05)
        return SeasonalAnalysis(
            summer=round(summer, 2),
            monsoon=round(monsoon, 2),
            winter=round(winter, 2),
        )

    def _comfort_analysis(self, speed: float) -> ComfortAnalysis:
        if speed < 4.0:
            ped_comfort = "Excellent"
            ventilation = "Excellent"
            outdoor = "Excellent"
        elif speed < 8.0:
            ped_comfort = "Good"
            ventilation = "Good"
            outdoor = "Good"
        elif speed < 12.0:
            ped_comfort = "Fair"
            ventilation = "Excellent"
            outdoor = "Fair"
        else:
            ped_comfort = "Poor"
            ventilation = "Good"
            outdoor = "Poor"
        return ComfortAnalysis(
            pedestrian_comfort=ped_comfort,
            natural_ventilation_potential=ventilation,
            outdoor_usability=outdoor,
        )

    def _building_impact(self, speed: float, direction: str) -> BuildingImpact:
        cross_vent = min(100.0, speed * 6.0)
        if speed < 5.0:
            load_risk = "Low"
        elif speed < 10.0:
            load_risk = "Moderate"
        elif speed < 15.0:
            load_risk = "High"
        else:
            load_risk = "Very High"

        dir_idx = ["North", "Northeast", "East", "Southeast", "South", "Southwest", "West", "Northwest"].index(direction)
        recommended = ["Southeast", "South", "Southwest", "South", "Southwest", "West", "Northwest", "North"][dir_idx]

        return BuildingImpact(
            cross_ventilation_score=round(cross_vent, 2),
            wind_load_risk=load_risk,
            recommended_orientation=recommended,
        )

    def _recommendations(self, speed: float, category: str, direction: str) -> list[str]:
        recs = [
            f"Prevailing winds from {direction}; orient living spaces for cross-ventilation opportunity.",
            "Plan window placement to maximize natural ventilation during moderate seasons.",
        ]
        if speed > 10.0:
            recs.append("Design wind-resistant details (roof tiedowns, cladding bracing) for high wind load.")
            recs.append("Consider wind breaks or shelterbelts on windward sides.")
        elif speed > 6.0:
            recs.append("Standard wind-resistant construction practices are recommended.")
        else:
            recs.append("Low wind exposure; standard ventilation strategies sufficient.")
        return recs
