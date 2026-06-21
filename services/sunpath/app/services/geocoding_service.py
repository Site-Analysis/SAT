# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

"""Geocoding service using Nominatim API."""

import time

from app.core.config import settings
from app.core.exceptions import GeocodingError
from app.core.logging import get_logger
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import Nominatim

logger = get_logger(__name__)


class GeocodingService:
    """Service for geocoding addresses using Nominatim (OpenStreetMap)."""

    def __init__(self):
        """Initialize the geocoding service."""
        self.geocoder = Nominatim(
            user_agent=settings.NOMINATIM_USER_AGENT, timeout=settings.NOMINATIM_TIMEOUT_SECONDS
        )
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Nominatim requires 1 request per second

    def _rate_limit(self):
        """Ensure we respect Nominatim's rate limit (1 request/second)."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def geocode_address(self, address: str) -> tuple[float, float]:
        """
        Geocode an address to latitude/longitude coordinates.

        Args:
            address: Address string to geocode

        Returns:
            Tuple of (latitude, longitude)

        Raises:
            GeocodingError: If geocoding fails
        """
        try:
            logger.info(f"Geocoding address: {address}")

            # Apply rate limiting
            self._rate_limit()

            # Geocode the address
            location = self.geocoder.geocode(address)

            if location is None:
                logger.warning(f"Address not found: {address}")
                raise GeocodingError(f"Address not found: {address}")

            latitude = location.latitude
            longitude = location.longitude

            logger.info(f"Geocoded '{address}' to ({latitude:.6f}, {longitude:.6f})")
            return latitude, longitude

        except GeocoderTimedOut:
            logger.error(f"Geocoding timeout for address: {address}")
            raise GeocodingError(f"Geocoding service timed out for address: {address}")

        except GeocoderServiceError as e:
            logger.error(f"Geocoding service error: {str(e)}")
            raise GeocodingError(f"Geocoding service error: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected geocoding error: {str(e)}", exc_info=True)
            raise GeocodingError(f"Failed to geocode address: {str(e)}")

    def reverse_geocode(self, latitude: float, longitude: float) -> str | None:
        """
        Reverse geocode coordinates to an address.

        Args:
            latitude: Latitude
            longitude: Longitude

        Returns:
            Address string or None if not found
        """
        try:
            logger.debug(f"Reverse geocoding ({latitude:.6f}, {longitude:.6f})")

            # Apply rate limiting
            self._rate_limit()

            # Reverse geocode
            location = self.geocoder.reverse((latitude, longitude))

            if location is None:
                return None

            return location.address

        except Exception as e:
            logger.warning(f"Reverse geocoding failed: {str(e)}")
            return None
