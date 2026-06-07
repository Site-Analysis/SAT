"""Solar position calculation engine using pvlib."""

from datetime import datetime

import pandas as pd
import pvlib
import pytz
import tzfpy
from app.core.exceptions import SolarCalculationError, TimezoneDetectionError, ValidationError
from app.core.logging import get_logger
from app.models.solar_models import SolarPositionData

logger = get_logger(__name__)


class SolarEngine:
    """Service for solar position calculations using pvlib."""

    def __init__(self):
        """Initialize the solar engine."""
        pass

    def detect_timezone(self, latitude: float, longitude: float) -> str:
        """
        Detect timezone from coordinates using timezonefinder.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees

        Returns:
            IANA timezone string (e.g., 'America/New_York')

        Raises:
            TimezoneDetectionError: If timezone detection fails
        """
        try:
            timezone_str = tzfpy.get_tz(longitude, latitude)

            if timezone_str is None or timezone_str == "":
                logger.warning(
                    f"Could not detect timezone for coordinates ({latitude}, {longitude}), using UTC"
                )
                timezone_str = "UTC"

            logger.info(
                f"Detected timezone: {timezone_str} for coordinates ({latitude}, {longitude})"
            )
            return timezone_str

        except Exception as e:
            logger.error(f"Timezone detection failed: {str(e)}")
            raise TimezoneDetectionError(f"Failed to detect timezone: {str(e)}")

    def calculate_solar_position(
        self,
        latitude: float,
        longitude: float,
        start_datetime: datetime,
        end_datetime: datetime | None = None,
    ) -> list[SolarPositionData]:
        """
        Calculate solar position data for given location and time range.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            start_datetime: Start datetime (naive or timezone-aware)
            end_datetime: End datetime for range queries (optional)

        Returns:
            List of SolarPositionData objects

        Raises:
            SolarCalculationError: If calculation fails
        """
        try:
            # Detect timezone
            timezone_str = self.detect_timezone(latitude, longitude)
            tz = pytz.timezone(timezone_str)

            # Create time range
            if end_datetime is None:
                # Single timestamp query
                times = pd.DatetimeIndex([start_datetime])
            else:
                # Range query with hourly frequency
                if start_datetime >= end_datetime:
                    raise ValidationError("start_datetime must be before end_datetime")

                times = pd.date_range(
                    start=start_datetime,
                    end=end_datetime,
                    freq="h",  # Hourly frequency
                    tz=None,  # Will localize separately
                )

            # Localize to timezone if naive
            if times.tz is None:
                times = times.tz_localize(tz, ambiguous="infer", nonexistent="shift_forward")
            else:
                times = times.tz_convert(tz)

            # Calculate solar position using pvlib
            logger.info(f"Calculating solar position for {len(times)} timestamps")
            solar_position = pvlib.solarposition.get_solarposition(
                time=times,
                latitude=latitude,
                longitude=longitude,
                method="nrel_numpy",  # NREL SPA algorithm
            )

            # Calculate equation of time - convert to Series first
            day_of_year = pd.Series(times.dayofyear, index=times)
            equation_of_time = pvlib.solarposition.equation_of_time_spencer71(day_of_year)

            # Calculate declination for all timestamps
            declination_values = pvlib.solarposition.declination_spencer71(day_of_year)

            # Calculate hour angle manually: hour_angle = 15 * (solar_time - 12)
            # Solar time approximation using equation of time
            # For accurate hour angle, we need to calculate it based on local solar time
            hour_angles = []
            for i, t in enumerate(times):
                # Get hour of day in decimal
                hour_decimal = t.hour + t.minute / 60.0 + t.second / 3600.0
                # Calculate hour angle (degrees): HA = 15 * (solar_time - 12)
                # Approximate solar time = local time + equation_of_time/60 + longitude_correction
                eot_hours = equation_of_time.iloc[i] / 60.0  # Convert minutes to hours
                # Longitude correction: 4 minutes per degree from standard meridian
                # Standard meridian approximation based on timezone
                std_meridian = round(longitude / 15) * 15
                lng_correction = 4 * (longitude - std_meridian) / 60.0  # in hours
                solar_time = hour_decimal + eot_hours + lng_correction
                hour_angle = 15.0 * (solar_time - 12.0)
                hour_angles.append(hour_angle)

            # Calculate sunrise, sunset, solar noon for each unique day
            unique_dates = times.normalize().unique()
            daily_events = {}

            for date in unique_dates:
                try:
                    # Calculate sunrise and sunset
                    sunrise_sunset = pvlib.solarposition.sun_rise_set_transit_spa(
                        times=pd.DatetimeIndex([date]),
                        latitude=latitude,
                        longitude=longitude,
                    )

                    daily_events[date] = {
                        "sunrise": sunrise_sunset["sunrise"].iloc[0],
                        "sunset": sunrise_sunset["sunset"].iloc[0],
                        "transit": sunrise_sunset["transit"].iloc[0],
                    }
                except Exception as e:
                    logger.warning(f"Could not calculate daily events for {date}: {str(e)}")
                    daily_events[date] = {
                        "sunrise": None,
                        "sunset": None,
                        "transit": None,
                    }

            # Build response data
            results = []
            for idx, timestamp in enumerate(times):
                date_key = timestamp.normalize()
                events = daily_events.get(date_key, {})

                # Calculate day length
                day_length = None
                if events.get("sunrise") and events.get("sunset"):
                    sunrise_time = events["sunrise"]
                    sunset_time = events["sunset"]
                    if pd.notna(sunrise_time) and pd.notna(sunset_time):
                        day_length = (sunset_time - sunrise_time).total_seconds() / 3600

                # Get solar position values for this timestamp
                azimuth = solar_position["azimuth"].iloc[idx]
                elevation = solar_position["apparent_elevation"].iloc[idx]  # Use apparent elevation
                zenith = solar_position["apparent_zenith"].iloc[idx]  # Use apparent zenith
                hour_angle = hour_angles[idx]  # Use our calculated hour angle

                # Get equation of time for this timestamp
                eot_minutes = equation_of_time.iloc[idx] if idx < len(equation_of_time) else 0

                # Get declination for this timestamp
                declination = declination_values.iloc[idx] if idx < len(declination_values) else 0

                # Calculate True Solar Time
                # TST = Local Time + EOT + 4*(Longitude - Local Standard Meridian)
                # For simplicity, we'll use: TST = 12:00 + (hour_angle / 15)
                tst_hours = 12.0 + (hour_angle / 15.0)

                # Handle negative and > 24 hours
                if tst_hours < 0:
                    tst_hours += 24
                elif tst_hours >= 24:
                    tst_hours -= 24

                # Convert to HH:MM:SS format
                tst_h = int(tst_hours)
                tst_m = int((tst_hours - tst_h) * 60)
                tst_s = int(((tst_hours - tst_h) * 60 - tst_m) * 60)
                tst_str = f"{tst_h:02d}:{tst_m:02d}:{tst_s:02d}"

                # Format times
                sunrise_str = (
                    events["sunrise"].strftime("%H:%M:%S")
                    if events.get("sunrise") and pd.notna(events["sunrise"])
                    else None
                )
                sunset_str = (
                    events["sunset"].strftime("%H:%M:%S")
                    if events.get("sunset") and pd.notna(events["sunset"])
                    else None
                )
                solar_noon_str = (
                    events["transit"].strftime("%H:%M:%S")
                    if events.get("transit") and pd.notna(events["transit"])
                    else None
                )

                position_data = SolarPositionData(
                    timestamp=timestamp.tz_convert("UTC"),
                    local_time=timestamp.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    timezone=timezone_str,
                    azimuth=round(float(azimuth), 4) if pd.notna(azimuth) else 0.0,
                    elevation=round(float(elevation), 4) if pd.notna(elevation) else 0.0,
                    zenith=round(float(zenith), 4) if pd.notna(zenith) else 90.0,
                    hour_angle=round(float(hour_angle), 4),
                    declination=round(float(declination), 4),
                    equation_of_time=round(float(eot_minutes), 4),
                    true_solar_time=tst_str,
                    sunrise=sunrise_str,
                    sunset=sunset_str,
                    solar_noon=solar_noon_str,
                    day_length=round(day_length, 4) if day_length else None,
                )

                results.append(position_data)

            logger.info(f"Successfully calculated {len(results)} solar position data points")
            return results

        except ValidationError:
            raise
        except TimezoneDetectionError:
            raise
        except Exception as e:
            logger.error(f"Solar calculation failed: {str(e)}", exc_info=True)
            raise SolarCalculationError(f"Failed to calculate solar position: {str(e)}")

    def get_sunpath_data(
        self,
        latitude: float,
        longitude: float,
        year: int,
    ) -> dict:
        """
        Calculate sunpath data for the entire year.

        This generates sunpath curves for key dates:
        - Summer solstice (June 21)
        - Winter solstice (December 21)
        - Equinoxes (March 20, September 22)
        - Monthly 21st day curves

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            year: Year for calculation

        Returns:
            Dictionary containing sunpath curves and metadata

        Raises:
            SolarCalculationError: If calculation fails
        """
        try:
            timezone_str = self.detect_timezone(latitude, longitude)
            tz = pytz.timezone(timezone_str)

            # Key dates for sunpath diagram
            key_dates = [
                (f"{year}-01-21", "Jan 21"),
                (f"{year}-02-21", "Feb 21"),
                (f"{year}-03-20", "Mar 20 (Equinox)"),
                (f"{year}-04-21", "Apr 21"),
                (f"{year}-05-21", "May 21"),
                (f"{year}-06-21", "Jun 21 (Solstice)"),
                (f"{year}-07-21", "Jul 21"),
                (f"{year}-08-21", "Aug 21"),
                (f"{year}-09-22", "Sep 22 (Equinox)"),
                (f"{year}-10-21", "Oct 21"),
                (f"{year}-11-21", "Nov 21"),
                (f"{year}-12-21", "Dec 21 (Solstice)"),
            ]

            curves = []
            sunrise_sunset_times = {}

            for date_str, label in key_dates:
                try:
                    # Create hourly timestamps for the day
                    start = pd.Timestamp(date_str, tz=tz).normalize()
                    times = pd.date_range(start, periods=24, freq="h")

                    # Calculate solar position
                    solar_position = pvlib.solarposition.get_solarposition(
                        time=times, latitude=latitude, longitude=longitude, method="nrel_numpy"
                    )

                    # Calculate sunrise/sunset
                    sunrise_sunset = pvlib.solarposition.sun_rise_set_transit_spa(
                        times=pd.DatetimeIndex([start]),
                        latitude=latitude,
                        longitude=longitude,
                    )

                    # Filter points above horizon
                    points = []
                    for idx, timestamp in enumerate(times):
                        elevation = solar_position["elevation"].iloc[idx]
                        if elevation > 0:  # Only include points above horizon
                            points.append(
                                {
                                    "azimuth": round(solar_position["azimuth"].iloc[idx], 2),
                                    "elevation": round(elevation, 2),
                                    "hour": timestamp.hour,
                                    "timestamp": timestamp.isoformat(),
                                }
                            )

                    if points:  # Only add curve if there are visible points
                        curves.append(
                            {
                                "label": label,
                                "date": date_str,
                                "points": points,
                            }
                        )

                    # Store sunrise/sunset times
                    sunrise = sunrise_sunset["sunrise"].iloc[0]
                    sunset = sunrise_sunset["sunset"].iloc[0]
                    transit = sunrise_sunset["transit"].iloc[0]

                    sunrise_sunset_times[date_str] = {
                        "sunrise": sunrise.strftime("%H:%M:%S") if pd.notna(sunrise) else None,
                        "sunset": sunset.strftime("%H:%M:%S") if pd.notna(sunset) else None,
                        "solar_noon": transit.strftime("%H:%M:%S") if pd.notna(transit) else None,
                    }

                except Exception as e:
                    logger.warning(f"Could not calculate sunpath for {date_str}: {str(e)}")
                    continue

            logger.info(f"Successfully calculated sunpath data for {len(curves)} dates")

            return {
                "latitude": latitude,
                "longitude": longitude,
                "timezone": timezone_str,
                "year": year,
                "curves": curves,
                "sunrise_sunset_times": sunrise_sunset_times,
            }

        except Exception as e:
            logger.error(f"Sunpath data calculation failed: {str(e)}", exc_info=True)
            raise SolarCalculationError(f"Failed to calculate sunpath data: {str(e)}")
