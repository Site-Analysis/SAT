# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

from __future__ import annotations

import asyncio
import logging
import math
import os
from typing import Any

import httpx
from fastapi import HTTPException

from app.models.infrastructure import (
    InfraResult,
    InfraSubScores,
    RoadAccess,
    TransitStop,
    UtilityPresence,
)

logger = logging.getLogger("infrastructure")

OVERPASS_URL = os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter")
# User-Agent required — public Overpass mirrors 403/406 the default httpx UA.
_OVERPASS_HEADERS = {"User-Agent": "SAT-SiteAnalysisTool/1.0"}

# analyze() used to fire five Overpass queries back to back. overpass-api.de allots a
# couple of slots per client IP, so that burst exhausted them: queries 2-5 drew 429/504
# and the whole analysis 502'd. It now sends ONE request (see _merged_query), which
# removes the burst at source rather than pacing around it — five slots per analysis
# becomes one, and with ten services sharing a single production egress IP that is the
# difference that matters.
#
# Retry is kept regardless: one request can still be rate-limited when other services
# are competing for the same slots.
_OVERPASS_RETRY_STATUS = {429, 502, 503, 504}
_OVERPASS_ATTEMPTS = int(os.getenv("OVERPASS_ATTEMPTS", "2"))
_OVERPASS_BACKOFF_S = float(os.getenv("OVERPASS_BACKOFF_SECONDS", "2.0"))


async def _overpass_post(client: httpx.AsyncClient, query: str, label: str) -> dict[str, Any]:
    """POST one Overpass query, retrying the rate-limit statuses.

    The previous code called `.json()` straight off the response without looking at the
    status. A rate-limited Overpass replies 429/504 with an HTML body, so `.json()`
    raised and every upstream condition collapsed into one opaque 502 — which is why the
    logs showed a 504 from Overpass surfacing as a 502 with no indication of the cause.
    Checking the status explicitly is what makes the failure legible *and* retryable.
    """
    last_error: Exception | None = None
    for attempt in range(_OVERPASS_ATTEMPTS):
        try:
            resp = await client.post(OVERPASS_URL, data={"data": query})
            if resp.status_code in _OVERPASS_RETRY_STATUS:
                last_error = httpx.HTTPStatusError(
                    f"Overpass {resp.status_code} for {label}",
                    request=resp.request,
                    response=resp,
                )
                logger.warning(
                    "Overpass %s for %s (attempt %d/%d)",
                    resp.status_code,
                    label,
                    attempt + 1,
                    _OVERPASS_ATTEMPTS,
                )
            else:
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:  # noqa: BLE001 — retried below, re-raised if terminal
            last_error = exc
            logger.warning(
                "Overpass request failed for %s (attempt %d/%d): %s",
                label,
                attempt + 1,
                _OVERPASS_ATTEMPTS,
                exc,
            )
        if attempt < _OVERPASS_ATTEMPTS - 1:
            await asyncio.sleep(_OVERPASS_BACKOFF_S * (2**attempt))
    raise last_error if last_error else RuntimeError(f"Overpass failed for {label}")


def _merged_query(lat: float, lon: float, radius_m: float) -> str:
    """The five former queries as one request, using named sets.

    Each group keeps its own `out ... N` limit, so the element budget per group is
    unchanged (25/30/20/10/15) — verified against the live API: the merged form
    returns exactly 25 roads + 30 transit for a Bengaluru point, with no duplicates.
    Per-clause radii are unchanged too; they live in the clauses, not in the request.

    The timeout is the sum of the old per-query timeouts (20+20+20+15+15) because one
    request now does all the work.
    """
    return f"""
[out:json][timeout:90];
way[highway~"^(motorway|trunk|primary|secondary|tertiary|residential|service)$"](around:{radius_m},{lat},{lon})->.roads;
(
  node[railway~"^(station|subway_entrance|halt)$"](around:5000,{lat},{lon});
  node[public_transport=stop_position][network](around:2000,{lat},{lon});
  node[highway=bus_stop](around:1000,{lat},{lon});
)->.transit;
(
  node[amenity=water_works](around:3000,{lat},{lon});
  node[man_made=water_tower](around:3000,{lat},{lon});
  node[power=substation](around:2000,{lat},{lon});
  node[man_made~"^(wastewater_plant|sewage_works)$"](around:3000,{lat},{lon});
  way[waterway~"^(drain|ditch)$"](around:1000,{lat},{lon});
)->.utility;
(
  way[power=line](around:1000,{lat},{lon});
  way[power=cable](around:500,{lat},{lon});
)->.power;
(
  node[man_made=mast](around:2000,{lat},{lon});
  node[man_made=communications_tower](around:2000,{lat},{lon});
  node[man_made=tower]["tower:type"=communication](around:2000,{lat},{lon});
)->.telecom;
.roads out center tags 25;
.transit out center tags 30;
.utility out center tags 20;
.power out center tags 10;
.telecom out center tags 15;
"""


# ── Response grouping ──────────────────────────────────────────────────────────
# The five queries are sent as one request (see _merged_query). Overpass returns a
# single flat element list, so the groups have to be reconstructed here.
#
# These predicates mirror each query's filter EXACTLY, and an element may land in
# more than one group — that is deliberate: sent as five separate queries, an element
# matching two filters came back in both responses, so multi-membership preserves the
# old behaviour rather than breaking it.
#
# Reconstructing the groups is not cosmetic. `road_access` picks the *nearest*
# element from its group, so a flat list would let a bus stop win the "nearest road"
# slot and silently change every road score.
_ROAD_HIGHWAYS = {
    "motorway",
    "trunk",
    "primary",
    "secondary",
    "tertiary",
    "residential",
    "service",
}
_TRANSIT_RAILWAYS = {"station", "subway_entrance", "halt"}
_UTILITY_MAN_MADE = {"water_tower", "wastewater_plant", "sewage_works"}
_TELECOM_MAN_MADE = {"mast", "communications_tower"}


def _groups_for(el: dict[str, Any]) -> set[str]:
    """Which of the five original queries would have returned this element."""
    kind = el.get("type")
    tags = el.get("tags") or {}
    groups: set[str] = set()

    if kind == "way" and tags.get("highway") in _ROAD_HIGHWAYS:
        groups.add("road")

    if kind == "node" and (
        tags.get("railway") in _TRANSIT_RAILWAYS
        or (tags.get("public_transport") == "stop_position" and tags.get("network"))
        or tags.get("highway") == "bus_stop"
    ):
        groups.add("transit")

    if (
        kind == "node"
        and (
            tags.get("amenity") == "water_works"
            or tags.get("man_made") in _UTILITY_MAN_MADE
            or tags.get("power") == "substation"
        )
    ) or (kind == "way" and tags.get("waterway") in {"drain", "ditch"}):
        groups.add("utility")

    if kind == "way" and tags.get("power") in {"line", "cable"}:
        groups.add("power")

    if kind == "node" and (
        tags.get("man_made") in _TELECOM_MAN_MADE
        or (tags.get("man_made") == "tower" and tags.get("tower:type") == "communication")
    ):
        groups.add("telecom")

    return groups


def _split_by_group(elements: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Rebuild the five per-query responses the parser below already expects.

    Deduplicated per group by (type, id): an element appearing under two `out`
    statements must not be counted twice within one group.
    """
    seen: dict[str, set[tuple[str, int]]] = {}
    out: dict[str, list[dict[str, Any]]] = {
        "road": [],
        "transit": [],
        "utility": [],
        "power": [],
        "telecom": [],
    }
    for el in elements:
        key = (str(el.get("type")), int(el.get("id", 0)))
        for group in _groups_for(el):
            if key in seen.setdefault(group, set()):
                continue
            seen[group].add(key)
            out[group].append(el)
    return {group: {"elements": els} for group, els in out.items()}


# Paved road surfaces get a score bonus; unpaved get a penalty.
_PAVED_SURFACES = {"paved", "asphalt", "concrete", "tarmac", "tar", "bituminous"}
_UNPAVED_SURFACES = {"unpaved", "dirt", "gravel", "ground", "grass", "sand", "mud", "track"}


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000
    p = math.pi / 180
    a = (
        math.sin((lat2 - lat1) * p / 2) ** 2
        + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))


def _center(el: dict[str, Any]) -> tuple[float, float] | None:
    c = el.get("center") or el
    lat = c.get("lat")
    lon = c.get("lon")
    if lat is None or lon is None:
        return None
    return float(lat), float(lon)


def _parse_float(val: str | None) -> float | None:
    if not val:
        return None
    try:
        return float(val.split()[0])
    except (ValueError, AttributeError):
        return None


def _parse_int(val: str | None) -> int | None:
    if not val:
        return None
    try:
        return int(val.split()[0])
    except (ValueError, AttributeError):
        return None


def _transit_score(metro_dists: list[float], other_dists: list[float]) -> float:
    """
    Linear decay transit scoring — avoids the cliff at exact threshold distances.

    Metro (higher capacity): 30 → 0 over 0–5 km
    Other transit (bus/rail): 15 → 0 over 0–3 km
    Returns the best single contribution (not additive — transit is one network).
    """
    best = 0.0

    if metro_dists:
        d = min(metro_dists)
        if d <= 5000:
            # Full 30 at 0m, decays linearly to 0 at 5000m
            metro_contribution = max(0.0, 30.0 * (1.0 - d / 5000.0))
            best = max(best, metro_contribution)

    if other_dists:
        d = min(other_dists)
        if d <= 3000:
            other_contribution = max(0.0, 15.0 * (1.0 - d / 3000.0))
            best = max(best, other_contribution)

    return round(best, 1)


def _road_score(nearest_road_m: float, road_type: str | None, surface: str | None) -> float:
    """
    Road proximity + type + surface quality → 0-50.

    Proximity (0-40):
      <5m: 40, <20m: 35, <100m: 25, <500m: 15, else: 5
    Road type bonus (up to +5):
      motorway/trunk/primary: +5
    Surface quality (±5):
      paved/asphalt/concrete: +5
      unpaved/dirt/gravel: -5
    """
    # Proximity
    if nearest_road_m < 5:
        score = 40.0
    elif nearest_road_m < 20:
        score = 35.0
    elif nearest_road_m < 100:
        score = 25.0
    elif nearest_road_m < 500:
        score = 15.0
    else:
        score = 5.0

    # Road type bonus
    if road_type in ("motorway", "trunk", "primary"):
        score += 5.0

    # Surface quality
    surf = (surface or "").lower()
    if surf in _PAVED_SURFACES:
        score += 5.0
    elif surf in _UNPAVED_SURFACES:
        score -= 5.0

    return min(50.0, max(0.0, score))


class InfrastructureService:
    async def analyze(self, lat: float, lon: float, radius_m: float = 2000) -> InfraResult:
        # Aerodromes excluded from transit — airport proximity is in Planning service.
        query = _merged_query(lat, lon, radius_m)
        try:
            async with httpx.AsyncClient(timeout=35, headers=_OVERPASS_HEADERS) as c:
                payload = await _overpass_post(c, query, "infrastructure")
        except Exception as exc:  # noqa: BLE001 — surfaced as 502 below
            logger.error("Overpass unavailable after retries: %s", exc)
            raise HTTPException(status_code=502, detail="OSM upstream unavailable") from exc

        results = _split_by_group(payload.get("elements", []))
        r_road = results["road"]
        r_transit = results["transit"]
        r_util = results["utility"]
        r_power = results["power"]
        r_telecom = results["telecom"]

        # ── Road access ────────────────────────────────────────────────────
        road_elements = r_road.get("elements", [])
        road_access: RoadAccess | None = None
        if road_elements:
            best = min(
                (el for el in road_elements if _center(el) is not None),
                key=lambda el: _haversine(lat, lon, *_center(el)),  # type: ignore[arg-type]
                default=None,
            )
            if best:
                c_pos = _center(best)
                dist = _haversine(lat, lon, c_pos[0], c_pos[1]) if c_pos else 9999.0
                tags = best.get("tags", {})
                raw_lanes = _parse_int(tags.get("lanes"))
                raw_width = _parse_float(tags.get("width"))
                raw_speed = _parse_int(tags.get("maxspeed"))
                road_access = RoadAccess(
                    nearest_road_m=round(dist, 1),
                    road_type=tags.get("highway"),
                    road_name=tags.get("name"),
                    road_ref=tags.get("ref"),
                    road_surface=tags.get("surface"),
                    road_lanes=raw_lanes,
                    road_width_m=raw_width,
                    road_maxspeed_kmh=raw_speed,
                    frontage_present=dist < 15,
                )

        # ── Transit ────────────────────────────────────────────────────────
        transit_elements = r_transit.get("elements", [])
        transit_stops: list[TransitStop] = []
        for el in transit_elements:
            c_pos = _center(el)
            if c_pos is None:
                continue
            tags = el.get("tags", {})
            dist = _haversine(lat, lon, c_pos[0], c_pos[1])
            railway = tags.get("railway", "")
            subway = tags.get("subway", "")
            pt = tags.get("public_transport", "")
            hw = tags.get("highway", "")
            station = tags.get("station", "")
            if (
                railway in ("subway_entrance", "station") and subway == "yes"
            ) or station == "subway":
                ttype: str = "metro"
            elif railway in ("station", "halt"):
                ttype = "railway"
            elif hw == "bus_stop" or pt == "stop_position":
                ttype = "bus"
            else:
                ttype = "bus"
            transit_stops.append(
                TransitStop(
                    type=ttype,  # type: ignore[arg-type]
                    name=tags.get("name"),
                    distance_m=round(dist, 1),
                    line=tags.get("line") or tags.get("network") or tags.get("ref"),
                )
            )
        transit_stops.sort(key=lambda t: t.distance_m)

        # ── Utilities ──────────────────────────────────────────────────────
        util_elements = r_util.get("elements", [])
        util_tags_set: set[tuple[str, str]] = set()
        for el in util_elements:
            for k, v in el.get("tags", {}).items():
                util_tags_set.add((k, v))

        # ── Power lines ────────────────────────────────────────────────────
        power_elements = r_power.get("elements", [])
        power_line_nearby = False
        power_line_voltage_kv: float | None = None
        power_line_dist: float | None = None

        for el in power_elements:
            c_pos = _center(el)
            if c_pos is None:
                continue
            dist = _haversine(lat, lon, c_pos[0], c_pos[1])
            power_line_nearby = True
            if power_line_dist is None or dist < power_line_dist:
                power_line_dist = round(dist, 1)
                voltage_str = el.get("tags", {}).get("voltage")
                if voltage_str:
                    try:
                        # Voltage tag: "11000" or "11000;33000" (multi-voltage) or "11000-33000"
                        raw = voltage_str.split(";")[0].split("-")[0].strip()
                        v_kv = float(raw) / 1000
                        if power_line_voltage_kv is None or v_kv > power_line_voltage_kv:
                            power_line_voltage_kv = round(v_kv, 1)
                    except (ValueError, AttributeError):
                        pass

        # ── Telecom towers ─────────────────────────────────────────────────
        telecom_elements = r_telecom.get("elements", [])
        telecom_nearby = False
        telecom_dist: float | None = None

        for el in telecom_elements:
            c_pos = _center(el)
            if c_pos is None:
                continue
            dist = _haversine(lat, lon, c_pos[0], c_pos[1])
            telecom_nearby = True
            if telecom_dist is None or dist < telecom_dist:
                telecom_dist = round(dist, 1)

        utilities = UtilityPresence(
            water_supply_nearby=any(
                t in util_tags_set
                for t in [("amenity", "water_works"), ("man_made", "water_tower")]
            ),
            power_substation_nearby=("power", "substation") in util_tags_set,
            power_line_nearby=power_line_nearby,
            power_line_voltage_kv=power_line_voltage_kv,
            power_line_distance_m=power_line_dist,
            storm_drainage_nearby=any(
                t in util_tags_set for t in [("waterway", "drain"), ("waterway", "ditch")]
            ),
            sewage_works_nearby=any(
                t in util_tags_set
                for t in [("man_made", "wastewater_plant"), ("man_made", "sewage_works")]
            ),
            telecom_tower_nearby=telecom_nearby,
            telecom_tower_distance_m=telecom_dist,
        )

        # ── Sub-scores ─────────────────────────────────────────────────────
        nearest_road_m = road_access.nearest_road_m if road_access else 9999.0
        road_type = road_access.road_type if road_access else None
        road_surface = road_access.road_surface if road_access else None

        # Road: 0-50 (proximity 0-40, type bonus 0-5, surface quality ±5)
        computed_road_score = _road_score(nearest_road_m, road_type, road_surface)

        # Transit: 0-30 (linear decay; metro weighted higher)
        metro_dists = [t.distance_m for t in transit_stops if t.type == "metro"]
        other_dists = [t.distance_m for t in transit_stops if t.type in ("bus", "railway")]
        computed_transit_score = _transit_score(metro_dists, other_dists)

        # Power: 0-20 (substation + line presence; better-mapped than water/telecom in India)
        power_score = 0.0
        if utilities.power_substation_nearby:
            power_score += 10.0
        if utilities.power_line_nearby:
            # Distance decay for power line
            pl_dist = utilities.power_line_distance_m or 1000
            power_score += max(0.0, 10.0 * (1.0 - pl_dist / 1000.0))
        power_score = min(20.0, round(power_score, 1))

        # Water/telecom: detected and reported but NOT scored —
        # OSM utility coverage in Indian cities is <20% and silence ≠ absence.
        water_score = 0.0
        telecom_score = 0.0

        sub_scores = InfraSubScores(
            road=computed_road_score,
            transit=computed_transit_score,
            power=power_score,
            water=water_score,
            telecom=telecom_score,
        )
        score = min(100.0, computed_road_score + computed_transit_score + power_score)
        severity = "low" if score >= 65 else "moderate" if score >= 40 else "high"

        return InfraResult(
            road_access=road_access,
            transit=transit_stops[:10],
            utilities=utilities,
            sub_scores=sub_scores,
            score=round(score, 1),
            severity=severity,  # type: ignore[arg-type]
            data_source="OpenStreetMap (Overpass API) — roads, transit, power",
        )
