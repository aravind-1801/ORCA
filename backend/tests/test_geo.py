import pytest
from backend.app.utils.geo import (
    haversine_distance_km,
    calculate_bearing,
    bearing_to_direction,
    format_zone_vector,
)


def test_haversine_distance():
    # Kollam Harbor (8.88, 76.59) to Zone A-12 (8.78, 76.49)
    dist = haversine_distance_km(8.88, 76.59, 8.78, 76.49)
    assert 13.0 <= dist <= 17.0 or dist == 15.6 or abs(dist - 15.6) < 3.0


def test_bearing_calculation():
    # Southwest vector from Kollam
    bearing = calculate_bearing(8.88, 76.59, 8.78, 76.49)
    assert 200 <= bearing <= 240
    direction = bearing_to_direction(bearing)
    assert "South" in direction or "West" in direction


def test_format_zone_vector():
    label, heading = format_zone_vector(12.0, 218)
    assert "12 km" in label
    assert "218°" in heading
    assert "Southwest" in label or "SSW" in heading
