# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

from __future__ import annotations

import statistics
from collections import Counter
from datetime import date, timedelta

import httpx
from app.models.wind import (
    BuildingImpact,
    ComfortAnalysis,
    SeasonalAnalysis,
    SeasonData,
    WindAnalysis,
    WindMetadata,
    WindRequest,
)
from app.settings import WindSettings

_OPENMETEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
_COMPASS = [
    "North",
    "Northeast",
    "East",
    "Southeast",
    "South",
    "Southwest",
    "West",
    "Northwest",
]


def _bearing_to_compass(deg: float) -> str:
    return _COMPASS[round(deg / 45) % 8]


def _month_of(date_str: str) -> int:
    return int(date_str[5:7])


class WindAnalysisService:
    def __init__(self, settings: WindSettings | None = None) -> None:
        self.settings = settings or WindSettings()

    def analyze(self, request: WindRequest) -> WindAnalysis:
        # ERA5 reanalysis lags real time by ~5 days; back off a week so the tail of
        # the window is never empty. Five years so each season below is averaged over
        # five realisations rather than one — a single monsoon is noise, not climate.
        end = date.today() - timedelta(days=7)
        start = end - timedelta(days=5 * 365)

        with httpx.Client(timeout=30) as client:
            resp = client.get(
                _OPENMETEO_ARCHIVE,
                params={
                    "latitude": request.latitude,
                    "longitude": request.longitude,
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                    "daily": "windspeed_10m_max,windgusts_10m_max,winddirection_10m_dominant",
                    "timezone": "auto",
                    "wind_speed_unit": "ms",
                },
            )
            resp.raise_for_status()
            raw = resp.json()

        daily = raw.get("daily", {})
        times = daily.get("time", [])
        speeds = [v for v in daily.get("windspeed_10m_max", []) if v is not None]
        gusts = [v for v in daily.get("windgusts_10m_max", []) if v is not None]
        dirs = [v for v in daily.get("winddirection_10m_dominant", []) if v is not None]

        if not speeds:
            raise ValueError(
                f"Open-Meteo returned no wind data for ({request.latitude}, {request.longitude})"
            )

        avg_speed = round(statistics.mean(speeds), 2)
        max_speed = round(max(gusts) if gusts else max(speeds) * 1.5, 2)

        # Overall direction distribution — % frequency per compass point
        dir_counts = Counter(_bearing_to_compass(d) for d in dirs)
        total_dirs_count = len(dirs) or 1
        overall_dist = {
            comp: round((dir_counts[comp] / total_dirs_count) * 100, 2) for comp in _COMPASS
        }
        prevailing = dir_counts.most_common(1)[0][0] if dir_counts else "North"

        # Seasonal breakdown — India meteorological seasons. Filtering by month pools
        # every occurrence of that season across the whole window, so a 5-year fetch
        # gives each season five monsoons/summers/winters to average over.
        def _season_stats(months: set[int]) -> SeasonData:
            indices = [i for i, t in enumerate(times) if _month_of(t) in months]
            season_speeds = [speeds[i] for i in indices if i < len(speeds)]
            season_dirs = [dirs[i] for i in indices if i < len(dirs)]
            season_gusts = [gusts[i] for i in indices if i < len(gusts)]

            s_avg = round(statistics.mean(season_speeds), 2) if season_speeds else avg_speed
            s_max = round(
                max(season_gusts)
                if season_gusts
                else (max(season_speeds) * 1.5 if season_speeds else max_speed),
                2,
            )

            s_counts = Counter(_bearing_to_compass(d) for d in season_dirs)
            s_total = len(season_dirs) or 1
            s_dist = {comp: round((s_counts[comp] / s_total) * 100, 2) for comp in _COMPASS}
            s_prevailing = s_counts.most_common(1)[0][0] if s_counts else prevailing

            return SeasonData(
                average_wind_speed=s_avg,
                max_wind_speed=s_max,
                prevailing_direction=s_prevailing,  # type: ignore[arg-type]
                direction_distribution=s_dist,
                gust_risk=self._gust_risk(s_max),
                recommended_orientation=self._building_impact(
                    s_avg, s_prevailing
                ).recommended_orientation,
            )

        seasonal = SeasonalAnalysis(
            summer=_season_stats({3, 4, 5}),
            monsoon=_season_stats({6, 7, 8, 9}),
            winter=_season_stats({10, 11, 12, 1, 2}),
        )

        category = self._wind_category(avg_speed)
        gust_risk = self._gust_risk(max_speed)
        comfort = self._comfort_analysis(avg_speed)
        building = self._building_impact(avg_speed, prevailing)
        recs = self._recommendations(avg_speed, category, prevailing)

        metadata = WindMetadata(
            latitude=request.latitude,
            longitude=request.longitude,
            radius_meters=request.radius_meters,
            data_source="Open-Meteo Archive API · ERA5 reanalysis · 10 m wind speed · 5-year daily",
        )

        return WindAnalysis(
            average_wind_speed=avg_speed,
            max_wind_speed=max_speed,
            prevailing_direction=prevailing,  # type: ignore[arg-type]
            direction_distribution=overall_dist,
            wind_category=category,
            gust_risk=gust_risk,
            seasonal_analysis=seasonal,
            comfort_analysis=comfort,
            building_impact=building,
            recommendations=recs,
            metadata=metadata,
        )

    # ── helpers ────────────────────────────────────────────────────────────

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

    def _gust_risk(self, max_speed: float) -> str:
        if max_speed < 8.0:
            return "Low"
        if max_speed < 15.0:
            return "Moderate"
        return "High"

    def _comfort_analysis(self, speed: float) -> ComfortAnalysis:
        if speed < 4.0:
            return ComfortAnalysis(
                pedestrian_comfort="Excellent",
                natural_ventilation_potential="Excellent",
                outdoor_usability="Excellent",
            )
        if speed < 8.0:
            return ComfortAnalysis(
                pedestrian_comfort="Good",
                natural_ventilation_potential="Good",
                outdoor_usability="Good",
            )
        if speed < 12.0:
            return ComfortAnalysis(
                pedestrian_comfort="Fair",
                natural_ventilation_potential="Excellent",
                outdoor_usability="Fair",
            )
        return ComfortAnalysis(
            pedestrian_comfort="Poor",
            natural_ventilation_potential="Good",
            outdoor_usability="Poor",
        )

    def _building_impact(self, speed: float, direction: str) -> BuildingImpact:
        load_risk = (
            "Low"
            if speed < 5.0
            else "Moderate"
            if speed < 10.0
            else "High"
            if speed < 15.0
            else "Very High"
        )
        dir_idx = _COMPASS.index(direction) if direction in _COMPASS else 0
        recommended = _COMPASS[(dir_idx + 2) % 8]
        return BuildingImpact(
            wind_load_risk=load_risk,  # type: ignore[arg-type]
            recommended_orientation=recommended,  # type: ignore[arg-type]
        )

    def _recommendations(self, speed: float, category: str, direction: str) -> list[str]:
        recs = [
            f"Prevailing winds from {direction} — orient habitable rooms toward the prevailing wind path.",
            f"5-year mean wind speed: {speed:.1f} m/s (Open-Meteo ERA5, 10 m AGL).",
        ]
        if speed > 10.0:
            recs.extend(
                [
                    "Design wind-resistant details per IS 875 Part 3:2015 (roof tie-downs, cladding bracing).",
                    "Consider windbreaks or shelterbelts on windward side.",
                ]
            )
        elif speed > 6.0:
            recs.append(
                "Standard wind-resistant construction practices recommended (IS 875 Part 3)."
            )
        else:
            recs.append("Low wind exposure — standard ventilation strategies sufficient.")
        return recs
