from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
import logging
import math
import os
import threading
import time
from typing import Any, Dict, List, Tuple

import httpx
from fastapi import APIRouter, Query, HTTPException

# Feature flag — enabled by including "feature.temperature.thermal-profile" in
# the FLAGS env var (comma-separated). All endpoints check this at request time.
_TEMPERATURE_FLAG = "feature.temperature.thermal-profile"


def _require_flag() -> None:
    enabled = {f.strip() for f in os.getenv("FLAGS", "").split(",") if f.strip()}
    if _TEMPERATURE_FLAG not in enabled:
        raise HTTPException(status_code=403, detail=f"Feature flag disabled: {_TEMPERATURE_FLAG}")

from app.models.climate import (
    ClimateRecommendations,
    ClimateReport,
    ClimateSummary,
    MonthlyTemperature,
    ThermalGridRequest,
    ThermalGridResponse,
)
from app.services.climate_analytics import ClimateAnalyticsService

logger = logging.getLogger(__name__)

service = ClimateAnalyticsService()

router = APIRouter(prefix="/weather", tags=["weather"])
weather_router = router

# In-flight deduplication for the wind endpoint.
# Key: cache key string → threading.Event that is set once the result is written.
# Concurrent requests for the same location wait on the event then read from cache.
_wind_inflight_lock = threading.Lock()
_wind_inflight: Dict[str, threading.Event] = {}


def get_default_year() -> int:
    """Return the default year (last completed year)."""
    return date.today().year - 1


def _extract_polygon_ring(geometry: Dict[str, Any]) -> List[Tuple[float, float]]:
    geometry_type = str(geometry.get("type", ""))
    if geometry_type != "Polygon":
        raise HTTPException(status_code=422, detail="geometry.type must be 'Polygon'")

    coords = geometry.get("coordinates")
    if not isinstance(coords, list) or len(coords) == 0:
        raise HTTPException(status_code=422, detail="geometry.coordinates must contain at least one ring")

    outer_ring = coords[0]
    if not isinstance(outer_ring, list) or len(outer_ring) < 4:
        raise HTTPException(status_code=422, detail="Polygon outer ring must have at least 4 coordinates")

    ring: List[Tuple[float, float]] = []
    for pair in outer_ring:
        if not isinstance(pair, list) or len(pair) < 2:
            raise HTTPException(status_code=422, detail="Invalid polygon coordinate pair")
        ring.append((float(pair[0]), float(pair[1])))  # (lon, lat)

    # Ensure ring is closed
    if ring[0] != ring[-1]:
        ring.append(ring[0])

    return ring


def _point_in_polygon(lon: float, lat: float, ring: List[Tuple[float, float]]) -> bool:
    # Ray-casting algorithm on outer ring
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        intersects = ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / ((yj - yi) + 1e-12) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def _estimated_climate_report(lat: float, lon: float, year: int, reason: str | None = None) -> ClimateReport:
    """Generate an estimated thermal profile when upstream weather APIs are unavailable.

    This keeps analysis workflows functional under provider throttling/outage.
    """
    # India-focused heuristic baseline and seasonal amplitude.
    lat_abs = abs(lat)
    baseline = 30.0 - min(lat_abs, 35.0) * 0.2
    continentality = min(abs(lon - 78.0), 12.0) * 0.05
    amplitude = 5.0 + min(lat_abs, 30.0) * 0.08 + continentality

    monthly_data: List[MonthlyTemperature] = []
    for month in range(1, 13):
        # Peak heat around May in Indian climate contexts.
        angle = ((month - 5) / 12.0) * 2.0 * math.pi
        mean_temp = baseline + (amplitude * math.cos(angle))
        daily_range = 8.0 + (1.5 if month in (3, 4, 5) else 0.0)
        avg_tmax = mean_temp + (daily_range / 2.0)
        avg_tmin = mean_temp - (daily_range / 2.0)
        monthly_data.append(
            MonthlyTemperature(
                month=month,
                avg_tmax=float(round(avg_tmax, 2)),
                avg_tmin=float(round(avg_tmin, 2)),
            )
        )

    annual_means = [((m.avg_tmax + m.avg_tmin) / 2.0) for m in monthly_data]
    peak_max = max(m.avg_tmax for m in monthly_data)
    lowest_min = min(m.avg_tmin for m in monthly_data)
    annual_avg = sum(annual_means) / len(annual_means)

    if annual_avg > 24.0:
        status = "Hot / Estimated"
    elif annual_avg < 18.0:
        status = "Cold / Estimated"
    else:
        status = "Moderate / Estimated"

    reason_suffix = f" ({reason})" if reason else ""
    recommendations = ClimateRecommendations(
        material_suggestion=f"Estimated fallback profile used due upstream weather limits{reason_suffix}.",
        insulation_strategy="Retry later for measured historical profile; current values are estimated.",
        thermal_comfort_status=status,
    )

    return ClimateReport(
        monthly_data=monthly_data,
        summary=ClimateSummary(
            annual_avg_temp=float(round(annual_avg, 2)),
            peak_max_temp=float(round(peak_max, 2)),
            lowest_min_temp=float(round(lowest_min, 2)),
        ),
        recommendations=recommendations,
    )


@router.get("/thermal-profile", response_model=ClimateReport)
def get_thermal_profile(
    lat: float = Query(..., description="Latitude in decimal degrees"),
    lon: float = Query(..., description="Longitude in decimal degrees"),
    # Change Depends -> Query(default_factory=...)
    year: int = Query(default_factory=get_default_year, description="Target year"),
) -> ClimateReport:
    """Return an annual thermal profile (monthly aggregates, summary, recommendations)."""
    _require_flag()
    try:
        report = service.get_annual_thermal_profile(lat=lat, lon=lon, year=year)
        return report
    except Exception as exc:
        logger.warning(
            "Falling back to estimated thermal profile for %s,%s @ %s: %s",
            lat,
            lon,
            year,
            exc,
        )
        return _estimated_climate_report(lat=lat, lon=lon, year=year, reason=str(exc))


@router.post("/thermal-grid", response_model=ThermalGridResponse)
def get_thermal_grid(request: ThermalGridRequest) -> ThermalGridResponse:
    """Return a coarse spatial thermal grid for a polygon ROI.

    Each grid cell stores annual average temperature (deg C) at its centroid.
    """
    _require_flag()
    try:
        target_year = request.year if request.year is not None else get_default_year()
        ring = _extract_polygon_ring(request.geometry)

        lons = [p[0] for p in ring]
        lats = [p[1] for p in ring]
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)

        if min_lon == max_lon or min_lat == max_lat:
            raise HTTPException(status_code=422, detail="Polygon has zero area")

        grid_size = int(request.grid_size)
        lon_step = (max_lon - min_lon) / grid_size
        lat_step = (max_lat - min_lat) / grid_size

        candidate_cells: List[Dict[str, Any]] = []
        for row in range(grid_size):
            for col in range(grid_size):
                lon0 = min_lon + col * lon_step
                lon1 = lon0 + lon_step
                lat0 = min_lat + row * lat_step
                lat1 = lat0 + lat_step
                center_lon = lon0 + (lon_step / 2.0)
                center_lat = lat0 + (lat_step / 2.0)

                if not _point_in_polygon(center_lon, center_lat, ring):
                    continue

                candidate_cells.append(
                    {
                        "id": f"cell-{row}-{col}",
                        "row": row,
                        "col": col,
                        "center_lon": center_lon,
                        "center_lat": center_lat,
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[
                                [lon0, lat0],
                                [lon1, lat0],
                                [lon1, lat1],
                                [lon0, lat1],
                                [lon0, lat0],
                            ]],
                        },
                    }
                )

        if not candidate_cells:
            raise HTTPException(status_code=422, detail="No grid cells intersect polygon")

        # Fetch a small set of sample points and interpolate temperatures per cell.
        # This avoids rate-limit failures caused by external requests per grid cell.
        sample_candidates = [
            (min_lat, min_lon),
            (min_lat, max_lon),
            (max_lat, min_lon),
            (max_lat, max_lon),
            ((min_lat + max_lat) / 2.0, (min_lon + max_lon) / 2.0),
            (min_lat, (min_lon + max_lon) / 2.0),
            (max_lat, (min_lon + max_lon) / 2.0),
            ((min_lat + max_lat) / 2.0, min_lon),
            ((min_lat + max_lat) / 2.0, max_lon),
        ]
        unique_samples: List[Tuple[float, float]] = []
        seen_samples = set()
        for lat, lon in sample_candidates:
            key = (round(lat, 6), round(lon, 6))
            if key in seen_samples:
                continue
            seen_samples.add(key)
            unique_samples.append((lat, lon))

        def _sample_annual_avg_temp(point: Tuple[float, float]) -> Tuple[float, float, float]:
            sample_lat, sample_lon = point
            report = service.get_annual_thermal_profile(lat=sample_lat, lon=sample_lon, year=target_year)
            return sample_lat, sample_lon, float(report.summary.annual_avg_temp)

        sampled_temps: List[Tuple[float, float, float]] = []
        max_workers = min(6, max(1, len(unique_samples)))
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            future_map = {pool.submit(_sample_annual_avg_temp, point): point for point in unique_samples}
            for fut in as_completed(future_map):
                point = future_map[fut]
                try:
                    sampled_temps.append(fut.result())
                except Exception:
                    logger.warning(
                        "Failed thermal sample at (%s, %s)",
                        point[0],
                        point[1],
                        exc_info=True,
                    )

        if not sampled_temps:
            logger.warning(
                "Thermal grid sampling failed for all points; using estimated fallback field for %s",
                target_year,
            )
            centroid_lat = (min_lat + max_lat) / 2.0
            centroid_lon = (min_lon + max_lon) / 2.0
            fallback_profile = _estimated_climate_report(
                lat=centroid_lat,
                lon=centroid_lon,
                year=target_year,
                reason="all sample requests failed",
            )
            fallback_mean = float(fallback_profile.summary.annual_avg_temp)
            lat_span = max(max_lat - min_lat, 1e-9)
            lon_span = max(max_lon - min_lon, 1e-9)
            for s_lat, s_lon in unique_samples:
                lat_norm = ((s_lat - min_lat) / lat_span) - 0.5
                lon_norm = ((s_lon - min_lon) / lon_span) - 0.5
                gradient_temp = fallback_mean + (lon_norm * 1.4) - (lat_norm * 1.1)
                sampled_temps.append((s_lat, s_lon, gradient_temp))

        sample_avg = sum(temp for _, _, temp in sampled_temps) / len(sampled_temps)

        def _distance_sq(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
            # Longitude distance shrinks with latitude.
            lon_scale = math.cos(math.radians((a_lat + b_lat) / 2.0))
            d_lat = a_lat - b_lat
            d_lon = (a_lon - b_lon) * lon_scale
            return (d_lat * d_lat) + (d_lon * d_lon)

        def _interpolated_temp(lat: float, lon: float) -> float:
            weighted_sum = 0.0
            weight_total = 0.0
            for s_lat, s_lon, s_temp in sampled_temps:
                dist_sq = _distance_sq(lat, lon, s_lat, s_lon)
                if dist_sq < 1e-14:
                    return s_temp
                weight = 1.0 / dist_sq
                weighted_sum += s_temp * weight
                weight_total += weight
            if weight_total <= 0:
                return sample_avg
            return weighted_sum / weight_total

        features: List[Dict[str, Any]] = []
        temps: List[float] = []
        for cell in candidate_cells:
            temp = _interpolated_temp(cell["center_lat"], cell["center_lon"])
            temps.append(temp)
            features.append(
                {
                    "type": "Feature",
                    "geometry": cell["geometry"],
                    "properties": {
                        "id": cell["id"],
                        "row": cell["row"],
                        "col": cell["col"],
                        "center_lat": cell["center_lat"],
                        "center_lon": cell["center_lon"],
                        "annual_avg_temp": temp,
                    },
                }
            )

        if not features:
            raise HTTPException(status_code=500, detail="Thermal grid generation failed for all cells")

        return ThermalGridResponse(
            type="FeatureCollection",
            features=features,
            min_temp=min(temps),
            max_temp=max(temps),
            year=target_year,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to produce thermal grid")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/analyze-wind", tags=["weather"])
def analyze_wind(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
) -> Dict[str, Any]:
    """
    Wind rose analysis using ERA5 5-year daily data via Open-Meteo Archive API.

    Parameters:
      - lat: Latitude (decimal degrees)
      - lon: Longitude (decimal degrees)

    Returns raw daily ERA5 wind data (speed, gusts, direction) for the last 5 years.
    5 years captures all 4 India seasons multiple times and is sufficient for climate
    normals, while halving query time vs 10-year window.
    The frontend windApi.ts processes this into WindAnalysis/WindRose format.

    Data source: archive-api.open-meteo.com — ERA5-Land reanalysis, ~10 km grid.
    """
    _require_flag()
    from datetime import date as _date

    end_year = _date.today().year - 1
    start_year = end_year - 4  # 5-year window: enough for India seasonal normals
    start_date = f"{start_year}-01-01"
    end_date = f"{end_year}-12-31"

    url = (
        f"https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={lat}&longitude={lon}"
        f"&start_date={start_date}&end_date={end_date}"
        f"&daily=wind_speed_10m_max,wind_gusts_10m_max,wind_direction_10m_dominant"
        f"&timezone=auto"
    )

    import hashlib, json, pathlib

    cache_dir = pathlib.Path(__file__).resolve().parent.parent.parent / "_climate_cache"
    cache_dir.mkdir(exist_ok=True)

    key = f"wind_{round(lat, 4)}_{round(lon, 4)}_{start_date}_{end_date}"
    cache_file = cache_dir / f"{hashlib.sha256(key.encode()).hexdigest()[:16]}.json"

    # Fast path: already cached on disk
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text())
        except Exception:
            cache_file.unlink(missing_ok=True)

    # Deduplication: if another thread is already fetching this key, wait for it
    # then serve from disk cache — avoids stacking concurrent Open-Meteo requests.
    with _wind_inflight_lock:
        if key in _wind_inflight:
            wait_event = _wind_inflight[key]
            is_leader = False
        else:
            wait_event = threading.Event()
            _wind_inflight[key] = wait_event
            is_leader = True

    if not is_leader:
        logger.info("Wind: waiting for in-flight fetch for %s,%s", lat, lon)
        wait_event.wait(timeout=180)
        if cache_file.exists():
            try:
                return json.loads(cache_file.read_text())
            except Exception:
                pass
        raise HTTPException(status_code=503, detail="Wind data unavailable — upstream fetch failed")

    try:
        last_err: str | None = None
        for attempt in range(7):
            if attempt > 0:
                delay = min(15 * (2 ** (attempt - 1)), 120)
                logger.info("Open-Meteo wind retry %d/6 in %ds", attempt, delay)
                time.sleep(delay)
            try:
                resp = httpx.get(url, timeout=60)
                if resp.status_code == 429:
                    last_err = f"429 rate limit (attempt {attempt + 1})"
                    continue
                resp.raise_for_status()
                data = resp.json()
                cache_file.write_text(json.dumps(data))
                return data
            except httpx.HTTPStatusError:
                raise HTTPException(status_code=502, detail=f"Open-Meteo wind error: {resp.status_code}")
            except Exception as exc:
                last_err = str(exc)
                if "429" not in str(exc) and "rate" not in str(exc).lower():
                    logger.warning("Wind fetch failed for %s,%s: %s", lat, lon, exc)
                    raise HTTPException(status_code=502, detail=f"Open-Meteo wind fetch failed: {exc}")

        raise HTTPException(status_code=429, detail=f"Open-Meteo rate limited after all retries: {last_err}")
    finally:
        with _wind_inflight_lock:
            _wind_inflight.pop(key, None)
        wait_event.set()


@router.get("/climate-archive", tags=["weather"])
def climate_archive_proxy(
    latitude: float = Query(...),
    longitude: float = Query(...),
    start_date: str = Query(...),
    end_date: str = Query(...),
    daily: str = Query(...),
    timezone: str = Query("auto"),
) -> Dict[str, Any]:
    """Caching proxy for Open-Meteo archive API.

    Saves responses to disk so identical requests never hit the upstream API
    twice — survives server restarts + browser cache clears.
    """
    _require_flag()
    import hashlib, json, pathlib

    cache_dir = pathlib.Path(__file__).resolve().parent.parent.parent / "_climate_cache"
    cache_dir.mkdir(exist_ok=True)

    key = f"{round(latitude, 4)}_{round(longitude, 4)}_{start_date}_{end_date}_{daily}"
    cache_file = cache_dir / f"{hashlib.sha256(key.encode()).hexdigest()[:16]}.json"

    # Return from disk cache instantly
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text())
        except Exception:
            cache_file.unlink(missing_ok=True)

    url = (
        f"https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={latitude}&longitude={longitude}"
        f"&start_date={start_date}&end_date={end_date}"
        f"&daily={daily}&timezone={timezone}"
    )

    # Retry with long backoff — handled server-side so browser doesn't spin
    last_err: str | None = None
    for attempt in range(7):
        if attempt > 0:
            delay = min(15 * (2 ** (attempt - 1)), 120)
            logger.info("Open-Meteo climate-archive retry %d/6 in %ds", attempt, delay)
            time.sleep(delay)
        try:
            resp = httpx.get(url, timeout=60)
            if resp.status_code == 429:
                last_err = f"429 rate limit (attempt {attempt + 1})"
                continue
            resp.raise_for_status()
            data = resp.json()
            # Persist to disk
            cache_file.write_text(json.dumps(data))
            return data
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=502, detail=f"Open-Meteo error: {resp.status_code}")
        except Exception as exc:
            last_err = str(exc)
            if "429" not in str(exc) and "rate" not in str(exc).lower():
                raise HTTPException(status_code=502, detail=f"Open-Meteo fetch failed: {exc}")

    raise HTTPException(status_code=429, detail=f"Open-Meteo rate limited after all retries: {last_err}")
