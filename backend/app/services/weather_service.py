from datetime import datetime, timezone
from typing import Dict, Any
from backend.app.config import settings
from backend.app.data_sources.weather import WeatherAdapter
from backend.app.data_sources.demo_data import DEMO_TELEMETRY
from backend.app.services.cache_service import cache_service


class WeatherService:
    def __init__(self):
        self.adapter = WeatherAdapter()

    async def get_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        cache_key = f"weather:{lat:.2f}:{lon:.2f}"
        cached = await cache_service.get(cache_key)
        if cached:
            cached["data_mode"] = "cached"
            return cached

        telemetry = await self.adapter.fetch_telemetry(lat, lon)
        # Determine status
        wave = telemetry.get("wave_m", 0.8)
        wind = telemetry.get("wind_kmh", 14.0)

        if wave >= settings.SAFETY_WAVE_DANGER_M or wind >= settings.SAFETY_WIND_DANGER_KMH:
            status = "danger"
            risk = "high"
        elif wave >= settings.SAFETY_WAVE_CAUTION_M or wind >= settings.SAFETY_WIND_CAUTION_KMH:
            status = "caution"
            risk = "moderate"
        else:
            status = "safe"
            risk = "low"

        result = {
            "status": status,
            "wind_kmh": wind,
            "wind_speed_knots": round(wind * 0.539957, 1),
            "wind_direction": "West-Southwest",
            "wave_m": wave,
            "rain": telemetry.get("rain", "Low"),
            "water_temp_c": telemetry.get("water_temp_c", 28.4),
            "risk_level": risk,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": telemetry.get("source", "IMD Coastal Radar"),
            "data_mode": telemetry.get("data_mode", "demo" if settings.DEMO_MODE else "live"),
        }

        await cache_service.set(cache_key, result, ttl_sec=settings.CACHE_DEFAULT_TTL_SEC)
        return result


weather_service = WeatherService()
