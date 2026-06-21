# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

"""
Building extraction API endpoints.
Provides four methods to query buildings: bounding box, radius, polygon, and address.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.exceptions import (
    AreaLimitExceededError,
    BuildingExtractionError,
    GEEServiceError,
    GeocodingError,
)
from app.core.flags import require_sunpath_flag
from app.core.logging import get_logger
from app.models.building_models import (
    AddressRequest,
    BoundingBoxRequest,
    BuildingResponse,
    PolygonRequest,
    RadiusRequest,
)
from app.services.building_extractor import BuildingExtractor

logger = get_logger(__name__)

router = APIRouter(
    prefix="/buildings", tags=["buildings"], dependencies=[Depends(require_sunpath_flag)]
)

# Building extractor will be initialized with shared GEE service from main.py
# For now, create instance without GEE service (will initialize on demand if needed)
building_extractor = BuildingExtractor()


@router.post(
    "/bbox",
    response_model=BuildingResponse,
    summary="Extract buildings within a bounding box",
    description="""
    Extract buildings within a rectangular bounding box defined by min/max latitude and longitude.
    
    - Data sources: OpenStreetMap (via Overpass API) + Google Earth Engine Open Buildings
    - Overpass data takes priority and is shown in blue
    - GEE data fills gaps and is shown in orange
    - Buildings are enriched with height data from GEE Temporal dataset
    - Results are paginated with configurable page size
    - Maximum query area: 20 km²
    """,
)
async def extract_buildings_by_bbox(request: BoundingBoxRequest) -> BuildingResponse:
    """Extract buildings within a bounding box."""
    try:
        logger.info(f"Building extraction request (bbox): {request.model_dump()}")
        response = await building_extractor.extract_from_bbox(request)
        return response

    except AreaLimitExceededError as e:
        logger.warning(f"Area limit exceeded: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except GEEServiceError as e:
        logger.error(f"GEE service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google Earth Engine service error: {str(e)}",
        )

    except BuildingExtractionError as e:
        logger.error(f"Building extraction error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    except Exception as e:
        logger.exception(f"Unexpected error in building extraction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during building extraction",
        )


@router.post(
    "/radius",
    response_model=BuildingResponse,
    summary="Extract buildings within a radius",
    description="""
    Extract buildings within a circular area defined by a center point and radius in meters.
    
    - Data sources: OpenStreetMap (via Overpass API) + Google Earth Engine Open Buildings
    - Overpass data takes priority and is shown in blue
    - GEE data fills gaps and is shown in orange
    - Buildings are enriched with height data from GEE Temporal dataset
    - Results are paginated with configurable page size
    - Maximum query area: 20 km² (approximately 2.5 km radius)
    """,
)
async def extract_buildings_by_radius(request: RadiusRequest) -> BuildingResponse:
    """Extract buildings within a radius from a center point."""
    try:
        logger.info(f"Building extraction request (radius): {request.model_dump()}")
        response = await building_extractor.extract_from_radius(request)
        return response

    except AreaLimitExceededError as e:
        logger.warning(f"Area limit exceeded: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except GEEServiceError as e:
        logger.error(f"GEE service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google Earth Engine service error: {str(e)}",
        )

    except BuildingExtractionError as e:
        logger.error(f"Building extraction error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    except Exception as e:
        logger.exception(f"Unexpected error in building extraction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during building extraction",
        )


@router.post(
    "/polygon",
    response_model=BuildingResponse,
    summary="Extract buildings within a custom polygon",
    description="""
    Extract buildings within a custom polygon defined by a list of coordinates.
    
    - Data sources: OpenStreetMap (via Overpass API) + Google Earth Engine Open Buildings
    - Overpass data takes priority and is shown in blue
    - GEE data fills gaps and is shown in orange
    - Buildings are enriched with height data from GEE Temporal dataset
    - Results are paginated with configurable page size
    - Maximum query area: 20 km²
    - Polygon must be closed (first and last coordinates must be the same)
    """,
)
async def extract_buildings_by_polygon(request: PolygonRequest) -> BuildingResponse:
    """Extract buildings within a custom polygon."""
    try:
        logger.info(f"Building extraction request (polygon): {len(request.coordinates)} vertices")
        response = await building_extractor.extract_from_polygon(request)
        return response

    except AreaLimitExceededError as e:
        logger.warning(f"Area limit exceeded: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except GEEServiceError as e:
        logger.error(f"GEE service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google Earth Engine service error: {str(e)}",
        )

    except BuildingExtractionError as e:
        logger.error(f"Building extraction error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    except Exception as e:
        logger.exception(f"Unexpected error in building extraction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during building extraction",
        )


@router.post(
    "/address",
    response_model=BuildingResponse,
    summary="Extract buildings near an address",
    description="""
    Extract buildings within a radius from a geocoded address.
    
    - Address is geocoded using OpenStreetMap Nominatim
    - Data sources: OpenStreetMap (via Overpass API) + Google Earth Engine Open Buildings
    - Overpass data takes priority and is shown in blue
    - GEE data fills gaps and is shown in orange
    - Buildings are enriched with height data from GEE Temporal dataset
    - Results are paginated with configurable page size
    - Maximum query area: 20 km² (approximately 2.5 km radius)
    - Geocoding is rate-limited to 1 request per second
    """,
)
async def extract_buildings_by_address(request: AddressRequest) -> BuildingResponse:
    """Extract buildings near a geocoded address."""
    try:
        logger.info(f"Building extraction request (address): {request.address}")
        response = await building_extractor.extract_from_address(request)
        return response

    except GeocodingError as e:
        logger.warning(f"Geocoding error: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except AreaLimitExceededError as e:
        logger.warning(f"Area limit exceeded: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except GEEServiceError as e:
        logger.error(f"GEE service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google Earth Engine service error: {str(e)}",
        )

    except BuildingExtractionError as e:
        logger.error(f"Building extraction error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    except Exception as e:
        logger.exception(f"Unexpected error in building extraction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during building extraction",
        )


@router.get(
    "/health",
    summary="Check building API health",
    description="Health check endpoint to verify building extraction services are operational",
)
async def health_check() -> dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "building-extraction",
        "endpoints": ["/bbox", "/radius", "/polygon", "/address"],
    }
