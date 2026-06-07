from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta

from app.models.rainfall import (
    RainfallArchiveDaily,
    RainfallArchiveDailyUnits,
    RainfallArchiveResponse,
    RainfallDateRange,
    RainfallSummaryRequest,
    RainfallSummaryResponse,
)
from app.settings import RainfallSettings


@dataclass(frozen=True)
class DailySeries:
    dates: list[str]
    precipitation_mm: list[float]


class RainfallService:
    def __init__(self, settings: RainfallSettings | None = None) -> None:
        self.settings = settings or RainfallSettings()

    def get_archive(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        source: str | None = None,
    ) -> RainfallArchiveResponse:
        resolved_source = source or self.settings.default_source
        series = self._generate_daily_series(latitude, longitude, start_date, end_date)

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
        series = self._generate_daily_series(latitude, longitude, start_date, end_date)

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

    def _generate_daily_series(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> DailySeries:
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

    def _resolve_point(self, request: RainfallSummaryRequest) -> tuple[float, float]:
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
