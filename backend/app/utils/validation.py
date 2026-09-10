from datetime import datetime, timezone
from typing import Optional


def utcnow() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


def utcnow_str() -> str:
    """Return ISO formatted UTC string ending with Z."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_coordinates(lat: float, lon: float) -> bool:
    """Validate latitude [-90, 90] and longitude [-180, 180]."""
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0


def validate_marine_metrics(
    wind_kmh: Optional[float] = None,
    wave_m: Optional[float] = None,
    sst_c: Optional[float] = None,
) -> bool:
    """Check that marine observations fall within physically plausible physical bounds."""
    if wind_kmh is not None and not (0.0 <= wind_kmh <= 200.0):
        return False
    if wave_m is not None and not (0.0 <= wave_m <= 25.0):
        return False
    if sst_c is not None and not (10.0 <= sst_c <= 40.0):
        return False
    return True
