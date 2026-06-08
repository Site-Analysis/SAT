from __future__ import annotations

import math
from dataclasses import dataclass

from app.models.flood import (
    ElevationAnalysis,
    FloodComponentScores,
    FloodHistory,
    FloodMetadata,
    FloodReport,
    FloodRequest,
    HydrologyAnalysis,
    LowLyingAreaIndex,
)
from app.settings import FloodSettings


@dataclass(frozen=True)
class FloodScores:
    elevation: float
    hydrology: float
    historical: float
    llai: float


class FloodRiskService:
    def __init__(self, settings: FloodSettings | None = None) -> None:
        self.settings = settings or FloodSettings()

    def analyze(self, request: FloodRequest) -> FloodReport:
        # TODO: Replace deterministic scoring with GEE datasets (MERIT DEM, ALOS, SRTM,
        # MERIT Hydro, HydroSHEDS, JRC GSW, DFO Flood Archive, CHIRPS, MODIS LULC).
        scores = self._compute_scores(request)
        overall = self._weighted_overall(scores)
        risk_category = self._risk_category(overall)

        elevation = self._elevation_analysis(request, scores.elevation)
        hydrology = self._hydrology_analysis(request, scores.hydrology)
        history = self._history_analysis(request, scores.historical)
        llai = self._llai_analysis(scores.llai)

        recommendations = self._recommendations(risk_category)
        visualization_urls = {
            "risk_map": "",
            "components_map": "",
        }

        metadata = FloodMetadata(
            latitude=request.latitude,
            longitude=request.longitude,
            radius_meters=request.radius_meters,
            data_source=self.settings.data_source,
            gee_enabled=self._gee_enabled(),
        )

        return FloodReport(
            overall_score=overall,
            risk_category=risk_category,
            component_scores=FloodComponentScores(
                elevation_risk=scores.elevation,
                hydrology_risk=scores.hydrology,
                historical_risk=scores.historical,
                llai_risk=scores.llai,
            ),
            elevation=elevation,
            hydrology=hydrology,
            flood_history=history,
            llai=llai,
            recommendations=recommendations,
            visualization_urls=visualization_urls,
            metadata=metadata,
        )

    def _compute_scores(self, request: FloodRequest) -> FloodScores:
        seed = abs(request.latitude) * 0.7 + abs(request.longitude) * 0.3
        seed += request.radius_meters / 1000.0

        elevation = self._score_from_seed(seed, factor=0.35, offset=0.4)
        hydrology = self._score_from_seed(seed, factor=0.55, offset=1.2)
        historical = self._score_from_seed(seed, factor=0.25, offset=2.1)
        llai = self._score_from_seed(seed, factor=0.75, offset=0.8)

        return FloodScores(
            elevation=elevation, hydrology=hydrology, historical=historical, llai=llai
        )

    def _score_from_seed(self, seed: float, factor: float, offset: float) -> float:
        raw = math.sin(seed * factor + offset) * 0.5 + 0.5
        score = max(0.0, min(1.0, raw)) * 100.0
        return round(score, 2)

    def _weighted_overall(self, scores: FloodScores) -> float:
        overall = (
            0.30 * scores.elevation
            + 0.25 * scores.hydrology
            + 0.25 * scores.historical
            + 0.20 * scores.llai
        )
        return round(max(0.0, min(100.0, overall)), 2)

    def _risk_category(self, score: float) -> str:
        if score < 20:
            return "Very Low"
        if score < 40:
            return "Low"
        if score < 60:
            return "Moderate"
        if score < 80:
            return "High"
        return "Very High"

    def _elevation_analysis(
        self, request: FloodRequest, elevation_score: float
    ) -> ElevationAnalysis:
        mean_m = 80.0 + (abs(request.latitude) % 30) * 6.0 + (request.radius_meters / 1000.0)
        min_m = max(0.0, mean_m - (12.0 + (abs(request.longitude) % 8) * 2.0))
        max_m = mean_m + (14.0 + (abs(request.latitude) % 10) * 2.5)
        range_m = max_m - min_m
        slope = min(35.0, 2.0 + (abs(request.longitude) % 15) * 1.1)
        low_lying_pct = min(100.0, 15.0 + elevation_score * 0.6)

        if mean_m < 200.0:
            terrain = "flat"
        elif mean_m < 600.0:
            terrain = "hilly"
        else:
            terrain = "mountainous"

        return ElevationAnalysis(
            mean_m=round(mean_m, 2),
            min_m=round(min_m, 2),
            max_m=round(max_m, 2),
            range_m=round(range_m, 2),
            slope_degrees=round(slope, 2),
            low_lying_area_pct=round(low_lying_pct, 2),
            terrain_classification=terrain,
        )

    def _hydrology_analysis(
        self, request: FloodRequest, hydrology_score: float
    ) -> HydrologyAnalysis:
        flow_accumulation = round(hydrology_score / 100.0, 3)
        nearest_river_distance = 200.0 + (1.0 - hydrology_score / 100.0) * 800.0
        water_occurrence = min(100.0, hydrology_score * 0.8)
        drainage_density = 0.1 + (hydrology_score / 100.0) * 2.5

        if nearest_river_distance < 250.0:
            river_risk = "High"
        elif nearest_river_distance < 500.0:
            river_risk = "Moderate"
        else:
            river_risk = "Low"

        return HydrologyAnalysis(
            flow_accumulation=flow_accumulation,
            nearest_river_distance_m=round(nearest_river_distance, 2),
            water_occurrence_pct=round(water_occurrence, 2),
            drainage_density=round(drainage_density, 3),
            river_proximity_risk=river_risk,
        )

    def _history_analysis(self, request: FloodRequest, historical_score: float) -> FloodHistory:
        events = max(0, int(historical_score // 15))
        rainfall = 600.0 + historical_score * 8.0

        return FloodHistory(
            historical_events_count=events,
            annual_rainfall_mm=round(rainfall, 2),
            flood_history_score=round(historical_score, 2),
        )

    def _llai_analysis(self, llai_score: float) -> LowLyingAreaIndex:
        llai_min = max(0.0, llai_score - 12.0)
        llai_max = min(100.0, llai_score + 12.0)

        return LowLyingAreaIndex(
            mean=round(llai_score, 2),
            min=round(llai_min, 2),
            max=round(llai_max, 2),
            primary_risk_category=self._risk_category(llai_score),
        )

    def _recommendations(self, category: str) -> list[str]:
        base = [
            "Review site grading and stormwater discharge routes.",
            "Plan drainage capacity for 1-in-100 year rainfall events.",
        ]
        if category in {"High", "Very High"}:
            base.extend(
                [
                    "Elevate critical infrastructure above projected flood levels.",
                    "Prioritize flood barriers and onsite retention basins.",
                ]
            )
        elif category == "Moderate":
            base.append("Improve surface permeability and runoff capture.")
        else:
            base.append("Maintain clear runoff paths and regular drainage maintenance.")
        return base

    def _gee_enabled(self) -> bool:
        return bool(self.settings.gee_project_id and self.settings.gee_service_account_key_path)
