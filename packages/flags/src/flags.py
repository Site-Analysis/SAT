"""
Feature flag helper for Python services.

Usage:
    from packages.flags.src.flags import is_enabled, FeatureFlag

Enable flags via env var:
    FLAGS=feature.temperature.thermal-profile,feature.wind.climatology
"""

import os
from enum import Enum


class FeatureFlag(str, Enum):
    TEMPERATURE_THERMAL_PROFILE = "feature.temperature.thermal-profile"
    FLOOD_RISK_ANALYSIS = "feature.flood.risk-analysis"
    SUNPATH_DIAGRAM = "feature.sunpath.diagram"
    WIND_CLIMATOLOGY = "feature.wind.climatology"


_enabled: set[str] = {
    f.strip()
    for f in os.getenv("FLAGS", "").split(",")
    if f.strip()
}


def is_enabled(flag: FeatureFlag) -> bool:
    return flag.value in _enabled


def require_flag(flag: FeatureFlag) -> None:
    if not is_enabled(flag):
        raise RuntimeError(f"Feature flag disabled: {flag.value}")
