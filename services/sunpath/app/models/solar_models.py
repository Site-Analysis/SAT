"""Pydantic models for solar analysis endpoints."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# ============= Request Models =============


class SolarPositionRequest(BaseModel):
    """Request model for solar position calculation."""

    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    start_datetime: datetime = Field(..., description="Start date and time (ISO 8601 format)")
    end_datetime: datetime | None = Field(
        None,
        description="End date and time for range queries (ISO 8601 format). If omitted, single timestamp query.",
    )

    @field_validator("end_datetime")
    @classmethod
    def validate_date_range(cls, v, info):
        """Validate that end_datetime is after start_datetime."""
        if v is not None and "start_datetime" in info.data:
            if v <= info.data["start_datetime"]:
                raise ValueError("end_datetime must be after start_datetime")
        return v


class SunpathDiagramRequest(BaseModel):
    """Request model for sunpath diagram generation."""

    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    year: int = Field(..., ge=1900, le=2100, description="Year for sunpath diagram")
    target_datetime: datetime = Field(
        ..., description="Specific date and time to highlight on the diagram (ISO 8601 format)"
    )
    output_format: Literal["svg", "json", "both"] = Field(
        default="both",
        description="Output format: 'svg' for SVG image, 'json' for plot data, 'both' for both formats",
    )


# ============= Response Models =============


class SolarPositionData(BaseModel):
    """Individual solar position data point."""

    timestamp: datetime = Field(..., description="Timestamp (UTC)")
    local_time: str = Field(..., description="Local time string with timezone")
    timezone: str = Field(..., description="IANA timezone name")

    # Solar angles
    azimuth: float = Field(..., description="Solar azimuth angle (degrees, North=0, East=90)")
    elevation: float = Field(..., description="Solar elevation angle (degrees above horizon)")
    zenith: float = Field(..., description="Solar zenith angle (degrees from vertical)")

    # Additional parameters
    hour_angle: float = Field(..., description="Solar hour angle (degrees)")
    declination: float = Field(..., description="Solar declination (degrees)")
    equation_of_time: float = Field(..., description="Equation of time (minutes)")
    true_solar_time: str = Field(..., description="True solar time (HH:MM:SS)")

    # Daily events
    sunrise: str | None = Field(None, description="Sunrise time (local timezone)")
    sunset: str | None = Field(None, description="Sunset time (local timezone)")
    solar_noon: str | None = Field(None, description="Solar noon time (local timezone)")
    day_length: float | None = Field(None, description="Day length in hours")


class SolarPositionResponse(BaseModel):
    """Response model for solar position calculation."""

    request: SolarPositionRequest = Field(..., description="Original request parameters")
    data: list[SolarPositionData] = Field(..., description="Solar position data points")
    count: int = Field(..., description="Number of data points returned")


class SunpathDataPoint(BaseModel):
    """Single point on sunpath diagram."""

    azimuth: float = Field(..., description="Azimuth angle (degrees)")
    elevation: float = Field(..., description="Elevation angle (degrees)")
    hour: int = Field(..., description="Hour of day (0-23)")
    timestamp: datetime = Field(..., description="Timestamp")


class SunpathCurve(BaseModel):
    """Sunpath curve for a specific day/month."""

    label: str = Field(..., description="Curve label (e.g., 'June 21', 'Dec 21')")
    date: str = Field(..., description="Date (YYYY-MM-DD)")
    points: list[SunpathDataPoint] = Field(..., description="Points along the sunpath")


class SunpathPlotData(BaseModel):
    """Plot data for sunpath diagram (JSON format)."""

    latitude: float = Field(..., description="Location latitude")
    longitude: float = Field(..., description="Location longitude")
    timezone: str = Field(..., description="Timezone")
    year: int = Field(..., description="Year")
    curves: list[SunpathCurve] = Field(..., description="Sunpath curves for different dates")
    sunrise_sunset_times: dict = Field(..., description="Sunrise/sunset times for key dates")


class SunpathDiagramResponse(BaseModel):
    """Response model for sunpath diagram."""

    request: SunpathDiagramRequest = Field(..., description="Original request parameters")
    svg: str | None = Field(None, description="SVG diagram (if requested)")
    data: dict | None = Field(
        None,
        description="Plot data in JSON format with analemma points and special day curves (if requested)",
    )
