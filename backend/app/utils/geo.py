import math
from typing import Tuple

# Earth radius in kilometers
EARTH_RADIUS_KM = 6371.0
KM_TO_NM = 0.539957


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees) using Haversine formula.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(EARTH_RADIUS_KM * c, 1)


def haversine_distance_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in Nautical Miles."""
    return round(haversine_distance_km(lat1, lon1, lat2, lon2) * KM_TO_NM, 1)


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    """
    Calculate initial compass bearing from (lat1, lon1) to (lat2, lon2).
    Returns an integer degrees value between 0 and 359.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)

    bearing_rad = math.atan2(y, x)
    bearing_deg = (math.degrees(bearing_rad) + 360.0) % 360.0
    return int(round(bearing_deg))


CARDINAL_DIRECTIONS = [
    "North", "North-Northeast", "Northeast", "East-Northeast",
    "East", "East-Southeast", "Southeast", "South-Southeast",
    "South", "South-Southwest", "Southwest", "West-Southwest",
    "West", "West-Northwest", "Northwest", "North-Northwest"
]

CARDINAL_ABBREVIATIONS = [
    "N", "NNE", "NE", "ENE",
    "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW",
    "W", "WNW", "NW", "NNW"
]


def bearing_to_direction(bearing: float, short: bool = False) -> str:
    """
    Convert compass bearing (0-360 deg) to 16-point compass direction.
    """
    val = int((bearing / 22.5) + 0.5) % 16
    return CARDINAL_ABBREVIATIONS[val] if short else CARDINAL_DIRECTIONS[val]


def format_zone_vector(distance_km: float, bearing_deg: int) -> Tuple[str, str]:
    """
    Returns (human_readable_label, compact_heading), e.g.:
    ("12 km Southwest", "218° SSW")
    """
    full_dir = bearing_to_direction(bearing_deg, short=False)
    short_dir = bearing_to_direction(bearing_deg, short=True)
    label = f"{int(round(distance_km))} km {full_dir}"
    heading = f"{bearing_deg}° {short_dir}"
    return label, heading
