"""Custom API exceptions."""

from fastapi import HTTPException, status


class SolarAPIException(HTTPException):
    """Base exception for Solar API errors."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class ValidationError(SolarAPIException):
    """Exception for input validation errors."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


class TimezoneDetectionError(SolarAPIException):
    """Exception for timezone detection failures."""

    def __init__(self, detail: str = "Failed to detect timezone for given coordinates"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class SolarCalculationError(SolarAPIException):
    """Exception for solar calculation errors."""

    def __init__(self, detail: str = "Failed to calculate solar position"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class SunpathRenderError(SolarAPIException):
    """Exception for sunpath diagram rendering errors."""

    def __init__(self, detail: str = "Failed to generate sunpath diagram"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class ResourceNotFoundError(SolarAPIException):
    """Exception for resource not found errors."""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class RateLimitExceededError(SolarAPIException):
    """Exception for rate limit violations."""

    def __init__(self, detail: str = "Rate limit exceeded. Please try again later."):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
        )


class BuildingExtractionError(SolarAPIException):
    """Exception for building extraction errors."""

    def __init__(self, detail: str = "Failed to extract building data"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class AreaLimitExceededError(SolarAPIException):
    """Exception when query area exceeds maximum allowed."""

    def __init__(self, detail: str = "Query area exceeds maximum limit of 20 km²"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class GeocodingError(SolarAPIException):
    """Exception for geocoding failures."""

    def __init__(self, detail: str = "Failed to geocode address"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class GEEServiceError(SolarAPIException):
    """Exception for Google Earth Engine service errors."""

    def __init__(self, detail: str = "Google Earth Engine service error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )
