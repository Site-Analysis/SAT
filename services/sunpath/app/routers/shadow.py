"""Shadow analysis API endpoints (Phase 4a)."""

import time
from datetime import date, datetime
from typing import Any

import pandas as pd
import pvlib
import pytz
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.exceptions import AreaLimitExceededError, BuildingExtractionError, GeocodingError
from app.core.flags import require_sunpath_flag
from app.core.logging import get_logger
from app.models.building_models import (
    AddressRequest,
    BoundingBoxRequest,
    PolygonRequest,
    RadiusRequest,
)
from app.models.shadow_models import (
    ShadowAddressRequest,
    ShadowBBoxRequest,
    ShadowCumulativeBBoxRequest,
    ShadowCumulativeResponse,
    ShadowMetadata,
    ShadowPolygonRequest,
    ShadowRadiusRequest,
    ShadowResponse,
    ShadowTimeseriesBBoxRequest,
    ShadowTimeseriesMetadata,
    ShadowTimeseriesPolygonRequest,
    ShadowTimeseriesRadiusRequest,
    ShadowTimeseriesResponse,
)
from app.services.building_extractor import BuildingExtractor
from app.services.shadow_engine import ShadowEngine
from app.services.shadow_timeseries import ShadowTimeseriesService
from app.services.sunlight_hours import compute_sunlight_hours

router = APIRouter(prefix="/shadow", tags=["shadow"], dependencies=[Depends(require_sunpath_flag)])
logger = get_logger(__name__)


@router.get(
    "/sunlight-hours", summary="Ground sunshine-hours grid (pybdshadow method, pvlib-driven)"
)
async def sunlight_hours(
    lat: float = Query(...),
    lon: float = Query(...),
    date_str: str | None = Query(None, alias="date", description="ISO date (default today)"),
    radius_meters: float = Query(250.0),
) -> dict[str, Any]:
    day = date.fromisoformat(date_str) if date_str else date.today()

    # Best-effort building extraction (OSM/GEE). Any failure → open-sky grid.
    buildings = None
    try:
        resp = await building_extractor.extract_from_radius(
            RadiusRequest(latitude=lat, longitude=lon, radius_meters=radius_meters)
        )
        extracted = []
        for feature in resp.features:
            # height + osm_id live on feature.properties, not the feature itself.
            height = feature.properties.height
            if not height:
                continue
            rings = feature.geometry.coordinates
            if not rings:
                continue
            extracted.append(
                {"footprint": rings[0], "height": height, "id": feature.properties.osm_id or "b"}
            )
        buildings = extracted or None
    except Exception as exc:  # noqa: BLE001
        logger.warning("sunlight-hours building extraction failed (%s); open-sky grid", exc)
        buildings = None

    grid = compute_sunlight_hours(lat, lon, day, radius_meters=radius_meters, buildings=buildings)
    return {
        "latitude": lat,
        "longitude": lon,
        "date": day.isoformat(),
        "grid": grid,
        "attribution": "pybdshadow (BSD-3-Clause) — sunshine-duration grid method",
    }


# Initialize services
building_extractor = BuildingExtractor()
shadow_engine = ShadowEngine()
shadow_timeseries = ShadowTimeseriesService(shadow_engine)


def get_timezone_aware_datetime(dt: datetime, latitude: float, longitude: float) -> pd.Timestamp:
    """
    Convert naive datetime to timezone-aware datetime based on location.

    Args:
        dt: Naive datetime object
        latitude: Latitude for timezone detection
        longitude: Longitude for timezone detection

    Returns:
        Timezone-aware pandas Timestamp
    """
    # Detect timezone from coordinates
    tz_name = shadow_engine.detect_timezone(latitude, longitude)
    tz = pytz.timezone(tz_name)

    # Localize the datetime to the detected timezone
    if dt.tzinfo is None:
        dt_aware = tz.localize(dt)
    else:
        dt_aware = dt.astimezone(tz)

    logger.info(f"Converted timestamp to {tz_name}: {dt_aware.isoformat()}")
    return pd.Timestamp(dt_aware)


@router.post("/calculate/bbox", response_model=ShadowResponse)
async def calculate_shadows_bbox(request: ShadowBBoxRequest):
    """Calculate shadows for buildings within a bounding box at a specific time."""
    start_time = time.time()

    try:
        # Fetch buildings using building extractor
        logger.info(f"Fetching buildings for bbox at {request.timestamp}")
        building_request = BoundingBoxRequest(
            min_lat=request.min_lat,
            min_lon=request.min_lon,
            max_lat=request.max_lat,
            max_lon=request.max_lon,
            page=request.page,
            page_size=request.page_size,
        )

        building_response = await building_extractor.extract_from_bbox(building_request)
        buildings = building_response.features

        if not buildings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No buildings found in specified area"
            )

        # Calculate solar position with timezone awareness (Bug #1 Fix)
        centroid_lat = (request.min_lat + request.max_lat) / 2
        centroid_lon = (request.min_lon + request.max_lon) / 2

        # Convert to timezone-aware datetime
        dt_aware = get_timezone_aware_datetime(request.timestamp, centroid_lat, centroid_lon)

        solar_pos = pvlib.solarposition.get_solarposition(
            pd.DatetimeIndex([dt_aware]), centroid_lat, centroid_lon
        ).iloc[0]

        elevation = float(solar_pos["elevation"])
        azimuth = float(solar_pos["azimuth"])

        # Check if sun is above horizon
        if elevation <= shadow_engine.min_solar_elevation:
            # Return empty shadows
            shadows_geojson = {"type": "FeatureCollection", "features": []}
            metadata = ShadowMetadata(
                total_buildings=len(buildings),
                buildings_with_shadows=0,
                buildings_without_height=0,
                total_shadow_area_sq_meters=0.0,
                timestamp=request.timestamp.isoformat(),
                solar_elevation=elevation,
                solar_azimuth=azimuth,
                query_time_seconds=round(time.time() - start_time, 2),
            )

            return ShadowResponse(
                buildings=building_response.model_dump(), shadows=shadows_geojson, metadata=metadata
            )

        # Calculate shadows
        logger.info(f"Calculating shadows for {len(buildings)} buildings")
        shadows = await shadow_engine.calculate_shadows_for_buildings(
            buildings=buildings,
            solar_elevation=elevation,
            solar_azimuth=azimuth,
            timestamp=request.timestamp.isoformat(),
            enrich_missing_heights=True,
        )

        # Create response
        shadows_geojson = {"type": "FeatureCollection", "features": shadows}

        buildings_without_height = sum(
            1 for b in buildings if b.properties.height is None or b.properties.height <= 0
        )

        total_shadow_area = shadow_engine.calculate_total_shadow_area(shadows)

        metadata = ShadowMetadata(
            total_buildings=len(buildings),
            buildings_with_shadows=len(shadows),
            buildings_without_height=buildings_without_height,
            total_shadow_area_sq_meters=round(total_shadow_area, 2),
            timestamp=request.timestamp.isoformat(),
            solar_elevation=round(elevation, 2),
            solar_azimuth=round(azimuth, 2),
            query_time_seconds=round(time.time() - start_time, 2),
        )

        return ShadowResponse(
            buildings=building_response.model_dump(), shadows=shadows_geojson, metadata=metadata
        )

    except AreaLimitExceededError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BuildingExtractionError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"Shadow calculation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Shadow calculation failed: {str(e)}",
        )


@router.post("/calculate/radius", response_model=ShadowResponse)
async def calculate_shadows_radius(request: ShadowRadiusRequest):
    """Calculate shadows for buildings within a radius at a specific time."""
    start_time = time.time()

    try:
        # Fetch buildings
        building_request = RadiusRequest(
            latitude=request.latitude,
            longitude=request.longitude,
            radius_meters=request.radius_meters,
            page=request.page,
            page_size=request.page_size,
        )

        building_response = await building_extractor.extract_from_radius(building_request)
        buildings = building_response.features

        if not buildings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No buildings found in specified area"
            )

        # Calculate solar position with timezone awareness (Bug #1 Fix)
        dt_aware = get_timezone_aware_datetime(
            request.timestamp, request.latitude, request.longitude
        )

        solar_pos = pvlib.solarposition.get_solarposition(
            pd.DatetimeIndex([dt_aware]), request.latitude, request.longitude
        ).iloc[0]

        elevation = float(solar_pos["elevation"])
        azimuth = float(solar_pos["azimuth"])

        # Check if sun is above horizon
        if elevation <= shadow_engine.min_solar_elevation:
            shadows_geojson = {"type": "FeatureCollection", "features": []}
            metadata = ShadowMetadata(
                total_buildings=len(buildings),
                buildings_with_shadows=0,
                buildings_without_height=0,
                total_shadow_area_sq_meters=0.0,
                timestamp=request.timestamp.isoformat(),
                solar_elevation=elevation,
                solar_azimuth=azimuth,
                query_time_seconds=round(time.time() - start_time, 2),
            )

            return ShadowResponse(
                buildings=building_response.model_dump(), shadows=shadows_geojson, metadata=metadata
            )

        # Calculate shadows
        shadows = await shadow_engine.calculate_shadows_for_buildings(
            buildings=buildings,
            solar_elevation=elevation,
            solar_azimuth=azimuth,
            timestamp=request.timestamp.isoformat(),
            enrich_missing_heights=True,
        )

        shadows_geojson = {"type": "FeatureCollection", "features": shadows}

        buildings_without_height = sum(
            1 for b in buildings if b.properties.height is None or b.properties.height <= 0
        )

        total_shadow_area = shadow_engine.calculate_total_shadow_area(shadows)

        metadata = ShadowMetadata(
            total_buildings=len(buildings),
            buildings_with_shadows=len(shadows),
            buildings_without_height=buildings_without_height,
            total_shadow_area_sq_meters=round(total_shadow_area, 2),
            timestamp=request.timestamp.isoformat(),
            solar_elevation=round(elevation, 2),
            solar_azimuth=round(azimuth, 2),
            query_time_seconds=round(time.time() - start_time, 2),
        )

        return ShadowResponse(
            buildings=building_response.model_dump(), shadows=shadows_geojson, metadata=metadata
        )

    except AreaLimitExceededError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BuildingExtractionError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"Shadow calculation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Shadow calculation failed: {str(e)}",
        )


@router.post("/calculate/polygon", response_model=ShadowResponse)
async def calculate_shadows_polygon(request: ShadowPolygonRequest):
    """Calculate shadows for buildings within a polygon at a specific time."""
    start_time = time.time()

    try:
        # Fetch buildings
        building_request = PolygonRequest(
            coordinates=request.coordinates, page=request.page, page_size=request.page_size
        )

        building_response = await building_extractor.extract_from_polygon(building_request)
        buildings = building_response.features

        if not buildings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No buildings found in specified area"
            )

        # Calculate centroid for solar position
        coords = request.coordinates
        centroid_lat = sum(c[1] for c in coords) / len(coords)
        centroid_lon = sum(c[0] for c in coords) / len(coords)

        # Calculate solar position with timezone awareness (Bug #1 Fix)
        dt_aware = get_timezone_aware_datetime(request.timestamp, centroid_lat, centroid_lon)

        solar_pos = pvlib.solarposition.get_solarposition(
            pd.DatetimeIndex([dt_aware]), centroid_lat, centroid_lon
        ).iloc[0]

        elevation = float(solar_pos["elevation"])
        azimuth = float(solar_pos["azimuth"])

        if elevation <= shadow_engine.min_solar_elevation:
            shadows_geojson = {"type": "FeatureCollection", "features": []}
            metadata = ShadowMetadata(
                total_buildings=len(buildings),
                buildings_with_shadows=0,
                buildings_without_height=0,
                total_shadow_area_sq_meters=0.0,
                timestamp=request.timestamp.isoformat(),
                solar_elevation=elevation,
                solar_azimuth=azimuth,
                query_time_seconds=round(time.time() - start_time, 2),
            )

            return ShadowResponse(
                buildings=building_response.model_dump(), shadows=shadows_geojson, metadata=metadata
            )

        shadows = await shadow_engine.calculate_shadows_for_buildings(
            buildings=buildings,
            solar_elevation=elevation,
            solar_azimuth=azimuth,
            timestamp=request.timestamp.isoformat(),
            enrich_missing_heights=True,
        )

        shadows_geojson = {"type": "FeatureCollection", "features": shadows}

        buildings_without_height = sum(
            1 for b in buildings if b.properties.height is None or b.properties.height <= 0
        )

        total_shadow_area = shadow_engine.calculate_total_shadow_area(shadows)

        metadata = ShadowMetadata(
            total_buildings=len(buildings),
            buildings_with_shadows=len(shadows),
            buildings_without_height=buildings_without_height,
            total_shadow_area_sq_meters=round(total_shadow_area, 2),
            timestamp=request.timestamp.isoformat(),
            solar_elevation=round(elevation, 2),
            solar_azimuth=round(azimuth, 2),
            query_time_seconds=round(time.time() - start_time, 2),
        )

        return ShadowResponse(
            buildings=building_response.model_dump(), shadows=shadows_geojson, metadata=metadata
        )

    except AreaLimitExceededError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BuildingExtractionError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"Shadow calculation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Shadow calculation failed: {str(e)}",
        )


@router.post("/calculate/address", response_model=ShadowResponse)
async def calculate_shadows_address(request: ShadowAddressRequest):
    """Calculate shadows for buildings near an address at a specific time."""
    start_time = time.time()

    try:
        # Fetch buildings
        building_request = AddressRequest(
            address=request.address,
            radius_meters=request.radius_meters,
            page=request.page,
            page_size=request.page_size,
        )

        building_response = await building_extractor.extract_from_address(building_request)
        buildings = building_response.features

        if not buildings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No buildings found near address"
            )

        # Calculate centroid for solar position
        coords_list = [b.geometry.coordinates[0] for b in buildings]
        all_lats = [c[1] for coords in coords_list for c in coords]
        all_lons = [c[0] for coords in coords_list for c in coords]
        centroid_lat = sum(all_lats) / len(all_lats)
        centroid_lon = sum(all_lons) / len(all_lons)

        # Calculate solar position with timezone awareness (Bug #1 Fix)
        dt_aware = get_timezone_aware_datetime(request.timestamp, centroid_lat, centroid_lon)

        solar_pos = pvlib.solarposition.get_solarposition(
            pd.DatetimeIndex([dt_aware]), centroid_lat, centroid_lon
        ).iloc[0]

        elevation = float(solar_pos["elevation"])
        azimuth = float(solar_pos["azimuth"])

        if elevation <= shadow_engine.min_solar_elevation:
            shadows_geojson = {"type": "FeatureCollection", "features": []}
            metadata = ShadowMetadata(
                total_buildings=len(buildings),
                buildings_with_shadows=0,
                buildings_without_height=0,
                total_shadow_area_sq_meters=0.0,
                timestamp=request.timestamp.isoformat(),
                solar_elevation=elevation,
                solar_azimuth=azimuth,
                query_time_seconds=round(time.time() - start_time, 2),
            )

            return ShadowResponse(
                buildings=building_response.model_dump(), shadows=shadows_geojson, metadata=metadata
            )

        shadows = await shadow_engine.calculate_shadows_for_buildings(
            buildings=buildings,
            solar_elevation=elevation,
            solar_azimuth=azimuth,
            timestamp=request.timestamp.isoformat(),
            enrich_missing_heights=True,
        )

        shadows_geojson = {"type": "FeatureCollection", "features": shadows}

        buildings_without_height = sum(
            1 for b in buildings if b.properties.height is None or b.properties.height <= 0
        )

        total_shadow_area = shadow_engine.calculate_total_shadow_area(shadows)

        metadata = ShadowMetadata(
            total_buildings=len(buildings),
            buildings_with_shadows=len(shadows),
            buildings_without_height=buildings_without_height,
            total_shadow_area_sq_meters=round(total_shadow_area, 2),
            timestamp=request.timestamp.isoformat(),
            solar_elevation=round(elevation, 2),
            solar_azimuth=round(azimuth, 2),
            query_time_seconds=round(time.time() - start_time, 2),
        )

        return ShadowResponse(
            buildings=building_response.model_dump(), shadows=shadows_geojson, metadata=metadata
        )

    except GeocodingError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AreaLimitExceededError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BuildingExtractionError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"Shadow calculation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Shadow calculation failed: {str(e)}",
        )


# ====================
# TIMESERIES ENDPOINTS
# ====================


@router.post("/timeseries/bbox", response_model=ShadowTimeseriesResponse)
async def calculate_shadows_timeseries_bbox(request: ShadowTimeseriesBBoxRequest):
    """Calculate shadows for buildings over time within a bounding box."""
    start_time = time.time()

    try:
        # Fetch buildings
        building_request = BoundingBoxRequest(
            min_lat=request.min_lat,
            min_lon=request.min_lon,
            max_lat=request.max_lat,
            max_lon=request.max_lon,
            page=1,
            page_size=1000,
        )

        building_response = await building_extractor.extract_from_bbox(building_request)
        buildings = building_response.features

        if not buildings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No buildings found in specified area"
            )

        # Generate timestamps
        timestamps = shadow_timeseries.generate_time_range(
            request.start_datetime, request.end_datetime, request.interval_minutes
        )

        # Calculate centroid
        centroid_lat = (request.min_lat + request.max_lat) / 2
        centroid_lon = (request.min_lon + request.max_lon) / 2

        # Calculate timeseries shadows
        snapshots = await shadow_timeseries.calculate_timeseries_shadows(
            buildings=buildings,
            timestamps=timestamps,
            latitude=centroid_lat,
            longitude=centroid_lon,
            enrich_missing_heights=True,
        )

        metadata = ShadowTimeseriesMetadata(
            start_datetime=request.start_datetime.isoformat(),
            end_datetime=request.end_datetime.isoformat(),
            interval_minutes=request.interval_minutes,
            total_snapshots=len(snapshots),
            total_buildings=len(buildings),
            query_time_seconds=round(time.time() - start_time, 2),
        )

        return ShadowTimeseriesResponse(
            buildings=building_response.model_dump(), snapshots=snapshots, metadata=metadata
        )

    except Exception as e:
        logger.error(f"Timeseries shadow calculation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Timeseries calculation failed: {str(e)}",
        )


@router.post("/timeseries/radius", response_model=ShadowTimeseriesResponse)
async def calculate_shadows_timeseries_radius(request: ShadowTimeseriesRadiusRequest):
    """Calculate shadows for buildings over time within a radius."""
    start_time = time.time()

    try:
        building_request = RadiusRequest(
            latitude=request.latitude,
            longitude=request.longitude,
            radius_meters=request.radius_meters,
            page=1,
            page_size=1000,
        )

        building_response = await building_extractor.extract_from_radius(building_request)
        buildings = building_response.features

        if not buildings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No buildings found in specified area"
            )

        timestamps = shadow_timeseries.generate_time_range(
            request.start_datetime, request.end_datetime, request.interval_minutes
        )

        snapshots = await shadow_timeseries.calculate_timeseries_shadows(
            buildings=buildings,
            timestamps=timestamps,
            latitude=request.latitude,
            longitude=request.longitude,
            enrich_missing_heights=True,
        )

        metadata = ShadowTimeseriesMetadata(
            start_datetime=request.start_datetime.isoformat(),
            end_datetime=request.end_datetime.isoformat(),
            interval_minutes=request.interval_minutes,
            total_snapshots=len(snapshots),
            total_buildings=len(buildings),
            query_time_seconds=round(time.time() - start_time, 2),
        )

        return ShadowTimeseriesResponse(
            buildings=building_response.model_dump(), snapshots=snapshots, metadata=metadata
        )

    except Exception as e:
        logger.error(f"Timeseries shadow calculation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Timeseries calculation failed: {str(e)}",
        )


@router.post("/timeseries/polygon", response_model=ShadowTimeseriesResponse)
async def calculate_shadows_timeseries_polygon(request: ShadowTimeseriesPolygonRequest):
    """Calculate shadows for buildings over time within a polygon."""
    start_time = time.time()

    try:
        building_request = PolygonRequest(coordinates=request.coordinates, page=1, page_size=1000)

        building_response = await building_extractor.extract_from_polygon(building_request)
        buildings = building_response.features

        if not buildings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No buildings found in specified area"
            )

        # Calculate centroid for solar position
        coords = request.coordinates
        centroid_lat = sum(c[1] for c in coords) / len(coords)
        centroid_lon = sum(c[0] for c in coords) / len(coords)

        timestamps = shadow_timeseries.generate_time_range(
            request.start_datetime, request.end_datetime, request.interval_minutes
        )

        snapshots = await shadow_timeseries.calculate_timeseries_shadows(
            buildings=buildings,
            timestamps=timestamps,
            latitude=centroid_lat,
            longitude=centroid_lon,
            enrich_missing_heights=True,
        )

        metadata = ShadowTimeseriesMetadata(
            start_datetime=request.start_datetime.isoformat(),
            end_datetime=request.end_datetime.isoformat(),
            interval_minutes=request.interval_minutes,
            total_snapshots=len(snapshots),
            total_buildings=len(buildings),
            query_time_seconds=round(time.time() - start_time, 2),
        )

        return ShadowTimeseriesResponse(
            buildings=building_response.model_dump(), snapshots=snapshots, metadata=metadata
        )

    except AreaLimitExceededError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BuildingExtractionError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"Timeseries shadow calculation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Timeseries calculation failed: {str(e)}",
        )


# ====================
# CUMULATIVE ENDPOINTS
# ====================


@router.post("/cumulative/bbox", response_model=ShadowCumulativeResponse)
async def calculate_shadows_cumulative_bbox(request: ShadowCumulativeBBoxRequest):
    """Calculate cumulative shadow coverage for a full day within a bounding box."""
    start_time = time.time()

    try:
        # Fetch buildings
        building_request = BoundingBoxRequest(
            min_lat=request.min_lat,
            min_lon=request.min_lon,
            max_lat=request.max_lat,
            max_lon=request.max_lon,
            page=1,
            page_size=1000,
        )

        building_response = await building_extractor.extract_from_bbox(building_request)
        buildings = building_response.features

        if not buildings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No buildings found in specified area"
            )

        # Calculate centroid
        centroid_lat = (request.min_lat + request.max_lat) / 2
        centroid_lon = (request.min_lon + request.max_lon) / 2

        # Calculate cumulative shadows
        result = await shadow_timeseries.calculate_cumulative_shadows(
            buildings=buildings,
            date=request.date,
            latitude=centroid_lat,
            longitude=centroid_lon,
            interval_minutes=request.interval_minutes,
            enrich_missing_heights=True,
        )

        result["metadata"]["query_time_seconds"] = round(time.time() - start_time, 2)

        return ShadowCumulativeResponse(
            buildings=building_response.model_dump(),
            coverage_zones=result["coverage_zones"],
            metadata=result["metadata"],
        )

    except Exception as e:
        logger.error(f"Cumulative shadow calculation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cumulative calculation failed: {str(e)}",
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for shadow analysis service."""
    return {
        "status": "healthy",
        "service": "shadow-analysis",
        "endpoints": {
            "calculate": ["bbox", "radius", "polygon", "address"],
            "timeseries": ["bbox", "radius"],
            "cumulative": ["bbox"],
        },
    }
