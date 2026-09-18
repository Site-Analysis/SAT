# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

from __future__ import annotations

from datetime import datetime
import math
import os
import re
import pyproj

# Ensure PROJ_DATA environment variable is safely resolved to avoid Windows PROJ version conflicts
os.environ["PROJ_DATA"] = pyproj.datadir.get_data_dir()

from typing import Any
from shapely.geometry import Point, shape


def _parse_year(val: str | None) -> int | None:
    """Extract 4-digit year integer from date string or ISO timestamp."""
    if not val or not str(val).strip():
        return None
    val_str = str(val).strip()
    try:
        return datetime.fromisoformat(val_str.replace("Z", "+00:00")).year
    except Exception:
        pass
    match = re.search(r"\b(19\d\d|20\d\d)\b", val_str)
    if match:
        return int(match.group(1))
    return None
from app.data.cyclone_dataset import cyclone_index, haversine_distance_km
from app.models.wind_cyclone import (
    PrioritizedMitigation,
    SiteResilienceReport,
    SummaryMetrics,
    WindCycloneAnalysis,
    WindCycloneRequest,
)

# Coastline key coordinates for India to compute coastal proximity
INDIAN_COASTLINE_POINTS = [
    (13.0827, 80.2707),  # Chennai
    (17.6868, 83.2185),  # Vizag
    (21.6266, 87.5074),  # Digha / Bengal
    (19.8135, 85.8312),  # Puri / Odisha
    (10.7905, 79.8428),  # Nagapattinam
    (8.0883, 77.5385),   # Kanyakumari
    (9.9312, 76.2673),   # Kochi
    (12.9141, 74.8560),  # Mangalore
    (15.2993, 74.1240),  # Goa
    (18.9220, 72.8347),  # Mumbai
    (21.1702, 72.8311),  # Surat
    (22.2587, 68.9678),  # Dwarka / Gujarat
]

IMD_CATEGORIES = [
    ("Super Cyclonic Storm (>=62 m/s)", 62.0, "#7E22CE", 4.0),
    ("Extremely Severe Cyclonic Storm (47-61 m/s)", 47.0, "#EF4444", 3.5),
    ("Very Severe Cyclonic Storm (33-46 m/s)", 33.0, "#F97316", 3.0),
    ("Severe Cyclonic Storm (25-32 m/s)", 25.0, "#FBBF24", 2.5),
    ("Cyclonic Storm (17-24 m/s)", 17.0, "#34D399", 2.0),
    ("Depression / Deep Depression (<17 m/s)", 0.0, "#60A5FA", 1.5),
]


def categorize_imd(wind_ms: float) -> tuple[str, str, float]:
    """Return (category_name, hex_color, stroke_width) for a given wind speed in m/s."""
    for cat, threshold, color, width in IMD_CATEGORIES:
        if wind_ms >= threshold:
            return cat, color, width
    return "Depression / Deep Depression (<17 m/s)", "#60A5FA", 1.5


def distance_to_indian_coast_km(lat: float, lon: float) -> float:
    """Approximate minimum distance in km from site to Indian coastline."""
    return min(haversine_distance_km(lat, lon, clat, clon) for clat, clon in INDIAN_COASTLINE_POINTS)


def is_within_india_bounds(lat: float, lon: float) -> bool:
    """Check if coordinates fall within India spatial domain."""
    return 6.0 <= lat <= 37.5 and 68.0 <= lon <= 97.5


IS_875_WIND_ZONE_FEATURES: list[dict[str, Any]] = [
    # Zone 1 (33 m/s) - Inland Deccan & Southern Peninsula (Bengaluru / Mysore / Coimbatore / Hyderabad South)
    {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[75.2, 11.5], [78.2, 11.5], [78.6, 12.8], [78.5, 14.5], [77.2, 15.0], [75.5, 14.8], [74.8, 13.0], [75.2, 11.5]]],
        },
        "properties": {
            "zone_id": "Zone 1",
            "zone_speed": 33,
            "v_b_ms": 33.0,
            "name": "Zone 1 (33 m/s) - Low Wind Hazard",
            "color": "#60A5FA",
            "stroke": "#64748B",
            "fill_opacity": 0.18,
        },
    },
    # Zone 6 (55 m/s) - Coastal Odisha & Bengal Hotspot (Puri / Paradeep / Digha / Sundarbans)
    {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[84.8, 19.0], [86.2, 19.5], [87.5, 21.2], [89.2, 22.2], [89.0, 23.5], [87.2, 23.0], [85.5, 21.0], [84.5, 19.8], [84.8, 19.0]]],
        },
        "properties": {
            "zone_id": "Zone 6",
            "zone_speed": 55,
            "v_b_ms": 55.0,
            "name": "Zone 6 (55 m/s) - Extreme Wind Hazard",
            "color": "#7E22CE",
            "stroke": "#64748B",
            "fill_opacity": 0.18,
        },
    },
    # Zone 5 East (50 m/s) - East Coast Belt (Tamil Nadu coast: Chennai; AP coast: Nellore, Vizag)
    {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[79.0, 8.5], [80.5, 10.0], [80.8, 13.5], [82.8, 16.5], [84.2, 18.5], [84.8, 19.0], [84.5, 19.8], [83.0, 18.2], [81.5, 16.0], [79.6, 13.0], [78.8, 10.0], [77.5, 8.2], [79.0, 8.5]]],
        },
        "properties": {
            "zone_id": "Zone 5",
            "zone_speed": 50,
            "v_b_ms": 50.0,
            "name": "Zone 5 (50 m/s) - Very High Wind Hazard (East Coast)",
            "color": "#EF4444",
            "stroke": "#64748B",
            "fill_opacity": 0.18,
        },
    },
    # Zone 5 West (50 m/s) - Kathiawar / Gujarat Coast (Kutch, Saurashtra, Dwarka, Jamnagar)
    {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[68.0, 20.5], [72.5, 20.5], [73.5, 22.5], [72.0, 24.5], [68.0, 24.5], [68.0, 20.5]]],
        },
        "properties": {
            "zone_id": "Zone 5",
            "zone_speed": 50,
            "v_b_ms": 50.0,
            "name": "Zone 5 (50 m/s) - Very High Wind Hazard (Gujarat Coast)",
            "color": "#EF4444",
            "stroke": "#64748B",
            "fill_opacity": 0.18,
        },
    },
    # Zone 3 (44 m/s) - West Coast Belt & Konkan (Kerala / Goa / Coastal Karnataka / Mumbai / Konkan)
    {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[74.5, 8.0], [77.5, 8.2], [76.5, 10.5], [75.2, 12.0], [74.5, 14.5], [73.2, 18.0], [72.5, 20.5], [71.5, 20.5], [72.2, 18.5], [73.0, 15.0], [74.5, 8.0]]],
        },
        "properties": {
            "zone_id": "Zone 3",
            "zone_speed": 44,
            "v_b_ms": 44.0,
            "name": "Zone 3 (44 m/s) - High Wind Hazard",
            "color": "#FBBF24",
            "stroke": "#64748B",
            "fill_opacity": 0.18,
        },
    },
    # Zone 4 (47 m/s) - Northern Indo-Gangetic Plains & Desert Belt (Delhi NCR / Haryana / Punjab / Rajasthan / UP / Bihar)
    {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[69.5, 24.5], [75.0, 24.5], [82.0, 23.5], [88.5, 24.0], [88.5, 28.0], [81.0, 31.0], [74.0, 32.5], [73.0, 29.0], [69.5, 27.0], [69.5, 24.5]]],
        },
        "properties": {
            "zone_id": "Zone 4",
            "zone_speed": 47,
            "v_b_ms": 47.0,
            "name": "Zone 4 (47 m/s) - High Wind Hazard",
            "color": "#F97316",
            "stroke": "#64748B",
            "fill_opacity": 0.18,
        },
    },
    # Zone 2 (39 m/s) - Peninsular Shield & Central Inland (Maharashtra / Pune / Telangana / Hyderabad / MP / Bhopal)
    {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[73.0, 14.5], [78.5, 14.5], [82.0, 16.5], [85.0, 19.5], [85.5, 23.0], [81.5, 24.0], [75.0, 24.5], [73.0, 20.5], [73.2, 18.0], [73.0, 14.5]]],
        },
        "properties": {
            "zone_id": "Zone 2",
            "zone_speed": 39,
            "v_b_ms": 39.0,
            "name": "Zone 2 (39 m/s) - Moderate Wind Hazard",
            "color": "#34D399",
            "stroke": "#64748B",
            "fill_opacity": 0.18,
        },
    },
]


def get_is_875_wind_zones_for_point(lat: float, lon: float) -> dict[str, Any]:
    """Return strictly the GeoJSON FeatureCollection containing only the IS 875 polygon enclosing (lat, lon)."""
    pt = Point(lon, lat)
    matches = [f for f in IS_875_WIND_ZONE_FEATURES if shape(f["geometry"]).contains(pt)]
    if not matches:
        matches = [f for f in IS_875_WIND_ZONE_FEATURES if shape(f["geometry"]).intersects(pt)]
    if not matches:
        # Distance fallback if on margin
        sorted_zones = sorted(IS_875_WIND_ZONE_FEATURES, key=lambda f: shape(f["geometry"]).distance(pt))
        matches = [sorted_zones[0]]
    # Prioritize conservative highest design wind speed if point falls on an overlapping boundary
    matches.sort(key=lambda f: f["properties"]["v_b_ms"], reverse=True)
    return {"type": "FeatureCollection", "features": matches[:1]}


def get_statutory_wind_speed(lat: float, lon: float) -> float:
    """Determine statutory basic design wind speed Vb (IS 875 Part 3: 2015) via spatial polygon intersection."""
    zone_fc = get_is_875_wind_zones_for_point(lat, lon)
    if zone_fc["features"]:
        return float(zone_fc["features"][0]["properties"]["v_b_ms"])
    return 39.0


def get_is_875_wind_zones_geojson(lat: float | None = None, lon: float | None = None) -> dict[str, Any]:
    """Return GeoJSON FeatureCollection of IS 875 wind speed zones. Returns containing polygon when point is passed."""
    if lat is not None and lon is not None:
        return get_is_875_wind_zones_for_point(lat, lon)
    return {"type": "FeatureCollection", "features": IS_875_WIND_ZONE_FEATURES}


class WindCycloneService:

    def analyze(self, request: WindCycloneRequest) -> WindCycloneAnalysis:
        lat = request.latitude
        lon = request.longitude
        radius_km = request.buffer_radius_km

        # Dynamic Analysis Period resolution (defaults to 50-year lookback if omitted)
        current_year = datetime.now().year
        parsed_start = _parse_year(request.start_date)
        parsed_end = _parse_year(request.end_date)

        if parsed_end is None:
            end_year = current_year
        else:
            end_year = parsed_end

        if parsed_start is None:
            start_year = end_year - 50
        else:
            start_year = parsed_start

        if start_year > end_year:
            start_year, end_year = end_year, start_year

        period_years = max(1, end_year - start_year)

        in_bounds = is_within_india_bounds(lat, lon)
        if not in_bounds:
            # Return out-of-bounds structure
            return WindCycloneAnalysis(
                is_within_india=False,
                statutory_v_b_ms=0.0,
                damage_risk_category="Out of Bounds",
                is_coastal_buffer=False,
                coastal_penalty_applied=False,
                terrain_wind_profile={"10m": 0.0, "50m": 0.0, "100m": 0.0, "150m": 0.0, "200m": 0.0},
                metrics=SummaryMetrics(
                    total_historical_events=0,
                    annual_rate_50yr=0.0,
                    period_years=period_years,
                    max_recorded_wind_speed_ms=0.0,
                    max_recorded_wind_speed_kmh=0.0,
                    closest_recorded_distance_km=0.0,
                ),
                decadal_trend={"1970": 0, "1980": 0, "1990": 0, "2000": 0, "2010": 0, "2020": 0},
                intensity_distribution={cat: 0 for cat, _, _, _ in IMD_CATEGORIES},
                tracks={"type": "FeatureCollection", "features": []},
                wind_zones=get_is_875_wind_zones_geojson(),
                eye_points={"type": "FeatureCollection", "features": []},
            )

        # 1. Statutory Basic Wind Speed & Containing Polygon
        wind_zones_collection = get_is_875_wind_zones_for_point(lat, lon)
        raw_vb = float(wind_zones_collection["features"][0]["properties"]["v_b_ms"]) if wind_zones_collection["features"] else get_statutory_wind_speed(lat, lon)
        dist_coast = distance_to_indian_coast_km(lat, lon)
        is_coastal = dist_coast <= 10.0 or (lat < 22.0 and (lon > 80.0 or lon < 73.5))

        penalty_applied = False
        statutory_vb = raw_vb
        if is_coastal and statutory_vb < 39.0:
            statutory_vb = 39.0
            penalty_applied = True

        # Risk Classification
        if statutory_vb >= 50.0:
            risk_cat = f"Very High Wind Hazard ({statutory_vb:.0f} m/s)"
        elif statutory_vb >= 44.0:
            risk_cat = f"High Wind Hazard ({statutory_vb:.0f} m/s)"
        elif statutory_vb >= 39.0:
            risk_cat = f"Moderate Wind Hazard ({statutory_vb:.0f} m/s)"
        else:
            risk_cat = f"Low Wind Hazard ({statutory_vb:.0f} m/s)"

        # 2. Multi-Height Terrain Wind Speed Profile (Global Wind Atlas 250m approximation)
        profile_10m = round(statutory_vb * 0.70, 1)
        profile_50m = round(statutory_vb * 0.88, 1)
        profile_100m = round(statutory_vb * 1.00, 1)
        profile_150m = round(statutory_vb * 1.08, 1)
        profile_200m = round(statutory_vb * 1.14, 1)

        terrain_profile = {
            "10m": profile_10m,
            "50m": profile_50m,
            "100m": profile_100m,
            "150m": profile_150m,
            "200m": profile_200m,
        }

        # 3. Spatial Query for Historical Storms & Dynamic Year Range Filtering
        raw_storms = cyclone_index.query_radius(lat, lon, radius_km)
        storms = [s for s in raw_storms if start_year <= s["season"] <= end_year]
        total_events = len(storms)
        annual_rate = round(total_events / float(period_years), 2)

        max_wind_ms = max((s["max_wind_ms"] for s in storms), default=0.0)
        max_wind_kmh = round(max_wind_ms * 3.6, 1)
        closest_dist = cyclone_index.nearest_neighbor_distance_km(lat, lon)

        metrics = SummaryMetrics(
            total_historical_events=total_events,
            annual_rate_50yr=annual_rate,
            period_years=period_years,
            max_recorded_wind_speed_ms=max_wind_ms,
            max_recorded_wind_speed_kmh=max_wind_kmh,
            closest_recorded_distance_km=closest_dist,
        )

        # 4. Decadal Frequency & IMD Distribution
        decadal: dict[str, int] = {
            "1970": 0, "1980": 0, "1990": 0, "2000": 0, "2010": 0, "2020": 0
        }
        intensity: dict[str, int] = {cat: 0 for cat, _, _, _ in IMD_CATEGORIES}

        features: list[dict[str, Any]] = []
        eye_features: list[dict[str, Any]] = []

        for s in storms:
            season = s["season"]
            dec_key = f"{(season // 10) * 10}"
            if dec_key in decadal:
                decadal[dec_key] += 1
            elif season >= 2020:
                decadal["2020"] += 1

            cat_name, color, stroke_w = categorize_imd(s["max_wind_ms"])
            if cat_name in intensity:
                intensity[cat_name] += 1

            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": s["coords"],
                    },
                    "properties": {
                        "sid": s["sid"],
                        "name": s["name"],
                        "season": s["season"],
                        "max_wind_ms": s["max_wind_ms"],
                        "max_wind_kmh": round(s["max_wind_ms"] * 3.6, 1),
                        "min_pressure_hpa": s["min_pressure_hpa"],
                        "closest_distance_km": s["closest_distance_km"],
                        "category": cat_name,
                        "stroke": color,
                        "stroke_width": stroke_w,
                    },
                }
            )

            # Generate intermediate 6-hour storm eye point features
            for p_idx, (lon_pt, lat_pt) in enumerate(s["coords"]):
                eye_features.append(
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [lon_pt, lat_pt],
                        },
                        "properties": {
                            "sid": s["sid"],
                            "name": s["name"],
                            "season": s["season"],
                            "wind_ms": s["max_wind_ms"],
                            "category": cat_name,
                            "stroke": color,
                            "color": color,
                            "point_index": p_idx,
                        },
                    }
                )

        geojson_tracks = {
            "type": "FeatureCollection",
            "features": features,
        }

        geojson_eye_points = {
            "type": "FeatureCollection",
            "features": eye_features,
        }

        return WindCycloneAnalysis(
            is_within_india=True,
            statutory_v_b_ms=statutory_vb,
            damage_risk_category=risk_cat,
            is_coastal_buffer=is_coastal,
            coastal_penalty_applied=penalty_applied,
            terrain_wind_profile=terrain_profile,
            metrics=metrics,
            decadal_trend=decadal,
            intensity_distribution=intensity,
            tracks=geojson_tracks,
            wind_zones=wind_zones_collection,
            eye_points=geojson_eye_points,
        )

    def generate_recommendations(
        self, request: WindCycloneRequest
    ) -> SiteResilienceReport:
        analysis = self.analyze(request)
        statutory_vb = analysis.statutory_v_b_ms
        max_recorded = analysis.metrics.max_recorded_wind_speed_ms
        total_events = analysis.metrics.total_historical_events

        elevated = max_recorded > statutory_vb
        rec_design_speed = round(max(statutory_vb, math.ceil(max_recorded / 5.0) * 5.0), 1)

        is_low_hazard_inland = statutory_vb == 33.0 and total_events == 0

        if is_low_hazard_inland:
            reason = "Standard IS 875 Part 3 baseline of 33.0 m/s is adequate. Low cyclonic hazard."
            mitigations = [
                PrioritizedMitigation(
                    priority="HIGH",
                    category="Structural Frame & Anchorage",
                    standard_reference="IS 875 Part 3: 2015, NBC 2016",
                    recommendation_text="Design primary structural frame for 33.0 m/s standard basic wind speed with conventional foundation and roof truss anchorages.",
                ),
                PrioritizedMitigation(
                    priority="HIGH",
                    category="Site Drainage & Stormwater",
                    standard_reference="NBC 2016 Part 9",
                    recommendation_text="Ensure high-capacity stormwater conveyance and roof runoff drainage to handle intense monsoonal downpours.",
                ),
                PrioritizedMitigation(
                    priority="ADVISORY",
                    category="Building Envelope",
                    standard_reference="IS 875 Part 3",
                    recommendation_text="Standard exterior glazing and roofing fasteners conforming to standard non-cyclonic wind pressures.",
                ),
                PrioritizedMitigation(
                    priority="ADVISORY",
                    category="Operations & Maintenance",
                    standard_reference="NDMA Guidelines",
                    recommendation_text="Routine monsoon readiness inspections of roof drains, rainwater pipes, and perimeter trees.",
                ),
            ]
            early_warning = [
                "Standard roof gutter and downspout clearance prior to monsoon season",
                "Secure anchoring of rooftop HVAC and equipment units for 33 m/s baseline",
                "Inspection of perimeter tree branches near overhead power/utility lines",
                "Adequate sump pump and basement drainage maintenance",
                "Standard weatherproofing of exterior window and door seals",
            ]
        else:
            reason = (
                f"Historical recorded storm gusts ({max_recorded:.1f} m/s) exceed minimum statutory building code ({statutory_vb:.1f} m/s). Elevated design parameters are recommended."
                if elevated
                else f"Statutory basic wind speed of {statutory_vb:.1f} m/s is adequate for planning baseline."
            )

            mitigations = [
                PrioritizedMitigation(
                    priority="CRITICAL",
                    category="Structural Frame",
                    standard_reference="IS 875 Part 3: 2015, NBC 2016",
                    recommendation_text=f"Design primary structural frame for {rec_design_speed:.1f} m/s baseline wind speed with ductile detailing and terrain-specific risk coefficient (k1).",
                ),
                PrioritizedMitigation(
                    priority="CRITICAL",
                    category="Building Envelope",
                    standard_reference="IS 875 Part 3: 2015, NBC 2016",
                    recommendation_text="High-performance cladding, standing-seam roof anchorage, and parapet bracing rated for extreme suction zones.",
                ),
                PrioritizedMitigation(
                    priority="CRITICAL",
                    category="Fenestration & Openings",
                    standard_reference="IS 875 / NBC 2016",
                    recommendation_text="Laminated impact-resistant glazing and heavy-duty external storm shutter provisions for windward facades.",
                ),
                PrioritizedMitigation(
                    priority="HIGH",
                    category="Aerodynamics & Geometry",
                    standard_reference="IS 875 Appendix C",
                    recommendation_text="Recommended boundary-layer wind tunnel testing or CFD analysis for complex building geometry to minimize localized vortex shedding.",
                ),
                PrioritizedMitigation(
                    priority="ADVISORY",
                    category="Early Warning & Operations",
                    standard_reference="NDMA Guidelines",
                    recommendation_text="Real-time site anemometry integrated with automated IMD cyclone alert triggers and backup generator flood elevation.",
                ),
            ]

            early_warning = [
                "Motorized storm shutters tied to emergency power circuit",
                "Real-time site ultrasonic anemometer linked to IMD alert feeds",
                "Elevated diesel generator and flood barrier placement at +1.5m AGL",
                "Rooftop solar panel racking engineered for 60 m/s uplift forces",
                "Emergency site evacuation and communication protocol",
            ]

        return SiteResilienceReport(
            recommended_design_wind_speed_ms=rec_design_speed,
            statutory_wind_speed_ms=statutory_vb,
            is_design_speed_elevated=elevated,
            elevation_reason=reason,
            prioritized_mitigations=mitigations,
            early_warning_checklist=early_warning,
        )
