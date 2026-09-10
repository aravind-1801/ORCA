from typing import List, Dict, Any
from backend.app.utils.geo import (
    haversine_distance_km,
    calculate_bearing,
    bearing_to_direction,
    format_zone_vector,
)


class GeospatialService:
    """
    Geospatial calculation engine for fishing zones and vessel courses.
    """

    @staticmethod
    def calculate_zone_vector(user_lat: float, user_lon: float, zone_lat: float, zone_lon: float) -> Dict[str, Any]:
        dist_km = haversine_distance_km(user_lat, user_lon, zone_lat, zone_lon)
        bearing = calculate_bearing(user_lat, user_lon, zone_lat, zone_lon)
        label, heading = format_zone_vector(dist_km, bearing)
        # Average fishing boat speed: ~10 knots (~18.5 km/h)
        est_minutes = int(round((dist_km / 18.5) * 60))

        return {
            "distance_km": dist_km,
            "bearing_deg": bearing,
            "direction": bearing_to_direction(bearing, short=False),
            "course_heading": heading,
            "vector_label": label,
            "est_run_time_min": max(est_minutes, 10),
        }

    @classmethod
    def process_and_rank_zones(cls, user_lat: float, user_lon: float, raw_zones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        processed = []
        for z in raw_zones:
            c_lat = z.get("latitude") or z.get("centroid_latitude", user_lat)
            c_lon = z.get("longitude") or z.get("centroid_longitude", user_lon)
            vector = cls.calculate_zone_vector(user_lat, user_lon, c_lat, c_lon)

            item = dict(z)
            item["distance_km"] = vector["distance_km"]
            item["course_deg"] = vector["bearing_deg"]
            item["direction"] = vector["direction"]
            item["course_heading"] = vector["course_heading"]
            item["est_run_time_min"] = vector["est_run_time_min"]
            processed.append(item)

        # Sort: high potential first, then closest distance
        potential_weights = {"high": 3, "moderate": 2, "low": 1}
        processed.sort(
            key=lambda x: (
                -potential_weights.get(str(x.get("potential", "low")).lower(), 1),
                x["distance_km"],
            )
        )
        return processed


geospatial_service = GeospatialService()
