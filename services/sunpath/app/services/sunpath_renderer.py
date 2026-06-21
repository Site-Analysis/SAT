# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

"""Sunpath diagram renderer for SVG and JSON formats."""

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")  # Use non-interactive backend
import io

import matplotlib.pyplot as plt
import pvlib
import pytz
from app.core.exceptions import SunpathRenderError
from app.core.logging import get_logger

logger = get_logger(__name__)


class SunpathRenderer:
    """Service for rendering sunpath diagrams in SVG and JSON formats."""

    def __init__(self):
        """Initialize the sunpath renderer."""
        pass

    def render_svg(
        self,
        latitude: float,
        longitude: float,
        year: int,
        timezone_str: str,
        custom_datetime: pd.Timestamp,
    ) -> str:
        """
        Render sunpath diagram as SVG following pvlib reference implementation.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            year: Year for the diagram
            timezone_str: IANA timezone string
            custom_datetime: Custom date and time to highlight on the diagram

        Returns:
            SVG string

        Raises:
            SunpathRenderError: If rendering fails
        """
        try:
            logger.info(f"Rendering polar sunpath diagram for year {year}")

            tz = pytz.timezone(timezone_str)

            # Generate full year of hourly data for analemma
            times = pd.date_range(f"{year}-01-01 00:00:00", f"{year + 1}-01-01", freq="h", tz=tz)

            # Calculate solar position for all times
            solpos = pvlib.solarposition.get_solarposition(times, latitude, longitude)

            # Remove nighttime (only keep points above horizon)
            solpos = solpos.loc[solpos["apparent_elevation"] > 0, :]

            # Create figure with polar projection
            fig = plt.figure(figsize=(12, 12))
            ax = fig.add_subplot(111, projection="polar")

            # Draw the analemma loops (hourly points colored by day of year)
            points = ax.scatter(
                np.radians(solpos.azimuth),
                solpos.apparent_zenith,
                s=2,
                label=None,
                c=solpos.index.dayofyear,
                cmap="twilight_shifted_r",
            )

            # Add and format colorbar
            cbar = ax.figure.colorbar(points)
            times_ticks = pd.date_range(f"{year}-01-01", f"{year + 1}-01-01", freq="MS", tz=tz)
            cbar.set_ticks(ticks=times_ticks.dayofyear, labels=[], minor=False)
            cbar.set_ticks(
                ticks=times_ticks.dayofyear + 15, labels=times_ticks.strftime("%b"), minor=True
            )
            cbar.ax.tick_params(which="minor", width=0)

            # Draw hour labels
            for hour in np.unique(solpos.index.hour):
                # Choose label position by the smallest radius for each hour
                subset = solpos.loc[solpos.index.hour == hour, :]
                r = subset.apparent_zenith
                pos = solpos.loc[r.idxmin(), :]
                ax.text(
                    np.radians(pos["azimuth"]),
                    pos["apparent_zenith"],
                    str(hour).zfill(2),
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    fontweight="bold",
                )

            # Draw individual days (equinoxes and solstices)
            special_dates = [
                (f"{year}-03-21", "Mar 21 (Equinox)"),
                (f"{year}-06-21", "Jun 21 (Solstice)"),
                (f"{year}-12-21", "Dec 21 (Solstice)"),
            ]

            for date_str, label in special_dates:
                date = pd.to_datetime(date_str)
                times_day = pd.date_range(date, date + pd.Timedelta("24h"), freq="5min", tz=tz)
                solpos_day = pvlib.solarposition.get_solarposition(times_day, latitude, longitude)
                solpos_day = solpos_day.loc[solpos_day["apparent_elevation"] > 0, :]

                if len(solpos_day) > 0:
                    ax.plot(
                        np.radians(solpos_day.azimuth),
                        solpos_day.apparent_zenith,
                        label=label,
                        linewidth=2,
                    )

            # Draw custom date line
            custom_dt_localized = (
                custom_datetime.tz_localize(tz)
                if custom_datetime.tz is None
                else custom_datetime.tz_convert(tz)
            )
            custom_date_start = custom_dt_localized.normalize()
            times_custom = pd.date_range(
                custom_date_start, custom_date_start + pd.Timedelta("24h"), freq="5min", tz=tz
            )
            solpos_custom = pvlib.solarposition.get_solarposition(times_custom, latitude, longitude)
            solpos_custom = solpos_custom.loc[solpos_custom["apparent_elevation"] > 0, :]

            if len(solpos_custom) > 0:
                ax.plot(
                    np.radians(solpos_custom.azimuth),
                    solpos_custom.apparent_zenith,
                    label=f"{custom_date_start.strftime('%b %d, %Y')} (Custom Date)",
                    linewidth=2.5,
                    color="magenta",
                    linestyle="-",
                    zorder=10,
                )

                # Add time point marker if time is during daylight
                solpos_time = pvlib.solarposition.get_solarposition(
                    custom_dt_localized, latitude, longitude
                )

                if solpos_time["apparent_elevation"].iloc[0] > 0:
                    ax.plot(
                        np.radians(solpos_time["azimuth"].iloc[0]),
                        solpos_time["apparent_zenith"].iloc[0],
                        marker="o",
                        markersize=12,
                        color="red",
                        markeredgecolor="darkred",
                        markeredgewidth=2,
                        zorder=15,
                        label=f"Time: {custom_dt_localized.strftime('%H:%M')}",
                    )

            # Add legend
            ax.figure.legend(loc="upper left", fontsize=10)

            # Configure polar plot to be like a compass
            ax.set_theta_zero_location("N")
            ax.set_theta_direction(-1)
            ax.set_rmax(90)

            # Set title
            ax.set_title(
                f"Sun Path Diagram (Polar)\n"
                f"Latitude: {latitude:.4f}°, Longitude: {longitude:.4f}°\n"
                f"Year: {year} ({timezone_str})",
                pad=20,
                fontsize=12,
                fontweight="bold",
            )

            # Add grid
            ax.grid(True, linestyle="--", alpha=0.5)

            # Save to SVG
            svg_buffer = io.StringIO()
            plt.savefig(svg_buffer, format="svg", bbox_inches="tight", dpi=150)
            plt.close(fig)

            svg_string = svg_buffer.getvalue()
            svg_buffer.close()

            logger.info("Successfully rendered polar sunpath diagram")
            return svg_string

        except Exception as e:
            logger.error(f"SVG rendering failed: {str(e)}", exc_info=True)
            raise SunpathRenderError(f"Failed to render SVG: {str(e)}")

    def generate_plot_data(
        self,
        latitude: float,
        longitude: float,
        year: int,
        timezone_str: str,
        custom_datetime: pd.Timestamp,
    ) -> dict:
        """
        Generate plot data for sunpath diagram.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            year: Year for calculation
            timezone_str: IANA timezone string
            custom_datetime: Custom date and time to include

        Returns:
            Dictionary with plot data
        """
        try:
            tz = pytz.timezone(timezone_str)

            # Generate full year of hourly data
            times = pd.date_range(f"{year}-01-01 00:00:00", f"{year + 1}-01-01", freq="h", tz=tz)

            # Calculate solar position
            solpos = pvlib.solarposition.get_solarposition(times, latitude, longitude)
            solpos = solpos.loc[solpos["apparent_elevation"] > 0, :]

            # Analemma data
            analemma_points = []
            for idx, row in solpos.iterrows():
                analemma_points.append(
                    {
                        "timestamp": idx.isoformat(),
                        "azimuth": round(float(row["azimuth"]), 2),
                        "elevation": round(float(row["apparent_elevation"]), 2),
                        "zenith": round(float(row["apparent_zenith"]), 2),
                        "day_of_year": idx.dayofyear,
                        "hour": idx.hour,
                    }
                )

            # Special day curves
            special_dates = [
                (f"{year}-03-21", "Mar 21 (Equinox)"),
                (f"{year}-06-21", "Jun 21 (Solstice)"),
                (f"{year}-12-21", "Dec 21 (Solstice)"),
            ]

            curves = []
            for date_str, label in special_dates:
                date = pd.to_datetime(date_str)
                times_day = pd.date_range(date, date + pd.Timedelta("24h"), freq="5min", tz=tz)
                solpos_day = pvlib.solarposition.get_solarposition(times_day, latitude, longitude)
                solpos_day = solpos_day.loc[solpos_day["apparent_elevation"] > 0, :]

                points = []
                for idx, row in solpos_day.iterrows():
                    points.append(
                        {
                            "timestamp": idx.isoformat(),
                            "azimuth": round(float(row["azimuth"]), 2),
                            "elevation": round(float(row["apparent_elevation"]), 2),
                            "zenith": round(float(row["apparent_zenith"]), 2),
                            "hour": idx.hour,
                            "minute": idx.minute,
                        }
                    )

                if points:
                    curves.append({"label": label, "date": date_str, "points": points})

            # Custom date curve
            custom_dt_localized = (
                custom_datetime.tz_localize(tz)
                if custom_datetime.tz is None
                else custom_datetime.tz_convert(tz)
            )
            custom_date_start = custom_dt_localized.normalize()
            times_custom = pd.date_range(
                custom_date_start, custom_date_start + pd.Timedelta("24h"), freq="5min", tz=tz
            )
            solpos_custom = pvlib.solarposition.get_solarposition(times_custom, latitude, longitude)
            solpos_custom = solpos_custom.loc[solpos_custom["apparent_elevation"] > 0, :]

            custom_points = []
            for idx, row in solpos_custom.iterrows():
                custom_points.append(
                    {
                        "timestamp": idx.isoformat(),
                        "azimuth": round(float(row["azimuth"]), 2),
                        "elevation": round(float(row["apparent_elevation"]), 2),
                        "zenith": round(float(row["apparent_zenith"]), 2),
                        "hour": idx.hour,
                        "minute": idx.minute,
                    }
                )

            custom_curve = {
                "label": f"{custom_date_start.strftime('%b %d, %Y')} (Custom Date)",
                "date": custom_date_start.strftime("%Y-%m-%d"),
                "points": custom_points,
            }

            # Custom time point
            solpos_time = pvlib.solarposition.get_solarposition(
                custom_dt_localized, latitude, longitude
            )

            custom_time_point = None
            if solpos_time["apparent_elevation"].iloc[0] > 0:
                custom_time_point = {
                    "timestamp": custom_dt_localized.isoformat(),
                    "azimuth": round(float(solpos_time["azimuth"].iloc[0]), 2),
                    "elevation": round(float(solpos_time["apparent_elevation"].iloc[0]), 2),
                    "zenith": round(float(solpos_time["apparent_zenith"].iloc[0]), 2),
                    "time": custom_dt_localized.strftime("%H:%M:%S"),
                }

            return {
                "latitude": latitude,
                "longitude": longitude,
                "timezone": timezone_str,
                "year": year,
                "analemma_points": analemma_points,
                "special_day_curves": curves,
                "custom_date_curve": custom_curve,
                "custom_time_point": custom_time_point,
            }

        except Exception as e:
            logger.error(f"Plot data generation failed: {str(e)}", exc_info=True)
            raise SunpathRenderError(f"Failed to generate plot data: {str(e)}")

    def render_diagram(
        self,
        latitude: float,
        longitude: float,
        year: int,
        timezone_str: str,
        custom_datetime: pd.Timestamp,
        output_format: str = "both",
    ) -> tuple[str | None, dict | None]:
        """
        Render sunpath diagram in requested format(s).

        Args:
            latitude: Latitude
            longitude: Longitude
            year: Year
            timezone_str: Timezone
            custom_datetime: Custom date and time to highlight
            output_format: 'svg', 'json', or 'both'

        Returns:
            Tuple of (svg_string, plot_data_dict)

        Raises:
            SunpathRenderError: If rendering fails
        """
        svg_output = None
        json_output = None

        try:
            if output_format in ["svg", "both"]:
                svg_output = self.render_svg(
                    latitude, longitude, year, timezone_str, custom_datetime
                )

            if output_format in ["json", "both"]:
                json_output = self.generate_plot_data(
                    latitude, longitude, year, timezone_str, custom_datetime
                )

            return svg_output, json_output

        except Exception as e:
            logger.error(f"Diagram rendering failed: {str(e)}", exc_info=True)
            raise SunpathRenderError(f"Failed to render diagram: {str(e)}")
