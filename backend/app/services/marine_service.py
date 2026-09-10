from datetime import datetime, timezone
from typing import Dict, Any
from backend.app.config import settings
from backend.app.schemas.common import DataMode
from backend.app.services.weather_service import weather_service
from backend.app.services.ocean_service import ocean_service
from backend.app.services.fishing_zone_service import fishing_zone_service
from backend.app.services.safety_service import safety_service
from backend.app.services.alert_service import alert_service
from backend.app.data_sources.demo_data import DEMO_TELEMETRY


class MarineService:
    async def get_status(self, lat: float, lon: float, location_name: str = "Kollam Coast") -> Dict[str, Any]:
        weather = await weather_service.get_weather(lat, lon)
        ocean = await ocean_service.get_ocean(lat, lon)
        best_zone = await fishing_zone_service.get_best_zone(lat, lon)
        alerts = await alert_service.get_active_alerts(lat, lon)

        # Deterministic safety evaluation
        safety = safety_service.evaluate_safety(
            wave_m=weather["wave_m"],
            wind_kmh=weather["wind_kmh"],
            active_alerts=alerts,
            ocean_condition=ocean["condition"],
        )

        # Determine recommendation summary
        if safety["status"] == "safe":
            recommendation_text = (
                f"Conditions are safe today. Recommended zone: {best_zone['distance_km']:.0f} km {best_zone['direction'].lower()} "
                f"based on satellite chlorophyll and thermal current convergence."
            )
        elif safety["status"] == "caution":
            recommendation_text = (
                f"Caution advised today. Moderate sea state ({weather['wave_m']}m swell). "
                f"Verify latest coastal warning before sailing."
            )
        else:
            recommendation_text = (
                f"DANGER: Unsafe sea conditions detected. Stay within harbor. "
                f"{safety['reasons'][0] if safety['reasons'] else 'Hazard warning active.'}"
            )

        data_mode = DataMode.DEMO if settings.DEMO_MODE else DataMode.LIVE

        return {
            "location": {
                "name": location_name,
                "latitude": lat,
                "longitude": lon,
                "harbor": settings.DEFAULT_HARBOR,
            },
            "connectivity": "online",
            "data_mode": data_mode,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "safety": {
                "status": safety["status"],
                "label": safety["label"],
                "favorable_text": safety["favorable_text"],
                "color_hex": safety["color_hex"],
            },
            "weather": {
                "wind_kmh": weather["wind_kmh"],
                "wind_speed_knots": weather["wind_speed_knots"],
                "wind_direction": weather["wind_direction"],
                "wave_m": weather["wave_m"],
                "rain": weather["rain"],
                "water_temp_c": weather["water_temp_c"],
                "risk_level": weather["risk_level"],
                "timestamp": weather["timestamp"],
                "source": weather["source"],
            },
            "ocean": {
                "sea_surface_temperature_c": ocean["sea_surface_temperature_c"],
                "chlorophyll_density": ocean["chlorophyll_density"],
                "chlorophyll_mg_m3": ocean["chlorophyll_mg_m3"],
                "ocean_current_knots": ocean["ocean_current_knots"],
                "condition": ocean["condition"],
                "timestamp": ocean["timestamp"],
                "source": ocean["source"],
                "confidence": ocean["confidence"],
            },
            "best_zone": {
                "id": best_zone.get("id", "A12"),
                "name": best_zone.get("name", "Zone A-12"),
                "distance_km": best_zone.get("distance_km", 12.0),
                "direction": best_zone.get("direction", "Southwest"),
                "potential": best_zone.get("potential", "high"),
                "course": best_zone.get("course_deg", 218),
                "depth_m": best_zone.get("depth_m", 44),
                "target_species": best_zone.get("target_species", ["Indian Mackerel & Sardines"])[0] if isinstance(best_zone.get("target_species"), list) else "Indian Mackerel & Sardines",
                "est_run_time_min": best_zone.get("est_run_time_min", 42),
            },
            "recommendation": {
                "text": recommendation_text,
            },
            "active_alerts_count": len(alerts),
        }


marine_service = MarineService()
