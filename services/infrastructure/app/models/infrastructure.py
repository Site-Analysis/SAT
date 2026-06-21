# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["low", "moderate", "high", "none"]
TransitType = Literal["metro", "railway", "bus"]


class InfraRequest(BaseModel):
    latitude: float
    longitude: float
    radius_m: float = Field(2000, ge=0)


class RoadAccess(BaseModel):
    nearest_road_m: float
    road_type: str | None = None
    road_name: str | None = None
    road_ref: str | None = None  # NH-44, SH-17, MDR-12
    road_surface: str | None = None  # paved/asphalt/unpaved/dirt
    road_lanes: int | None = None
    road_width_m: float | None = None  # from OSM width tag
    road_maxspeed_kmh: int | None = None
    frontage_present: bool


class TransitStop(BaseModel):
    type: TransitType
    name: str | None = None
    distance_m: float
    line: str | None = None


class UtilityPresence(BaseModel):
    water_supply_nearby: bool
    power_substation_nearby: bool
    power_line_nearby: bool = False
    power_line_voltage_kv: float | None = None
    power_line_distance_m: float | None = None
    storm_drainage_nearby: bool
    sewage_works_nearby: bool
    telecom_tower_nearby: bool = False
    telecom_tower_distance_m: float | None = None


class InfraSubScores(BaseModel):
    road: float  # 0-50 (proximity + type bonus + surface quality)
    transit: float  # 0-30 (linear decay; metro weighted higher)
    power: float  # 0-20 (substation + line, distance-decayed)
    water: float  # always 0 — OSM water coverage <20% in India, not scored
    telecom: float  # always 0 — OSM telecom coverage <20% in India, not scored


class InfraResult(BaseModel):
    road_access: RoadAccess | None = None
    transit: list[TransitStop] = []
    utilities: UtilityPresence
    sub_scores: InfraSubScores
    score: float
    severity: Severity
    data_source: str
    data_disclaimer: str = (
        "Road access and transit data from OSM — generally well-mapped for Indian urban areas. "
        "Power line proximity from OSM voltage tags — directional indicator only. "
        "Water supply, sewage, and telecom are detected but NOT scored: OSM utility coverage "
        "in India is <20%. 'Not detected' does NOT confirm absence — verify with BWSSB (water), "
        "BESCOM (power), and BBMP (drainage) before design. Aerodromes are excluded from transit "
        "scoring — see Planning module for airport proximity and ICAO height restrictions."
    )
