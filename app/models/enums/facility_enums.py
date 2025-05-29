"""Facility-related enumerations."""

from enum import Enum as PyEnum


class ActivityFacilityType(str, PyEnum):
    """Types of facilities that can perform activities."""
    HOSPITAL = "hospital"
    HEALTH_CENTER = "health_center"
    BOTH = "both"


class FacilityType(str, PyEnum):
    """Healthcare facility types."""
    HOSPITAL = "hospital"
    HEALTH_CENTER = "health_center"