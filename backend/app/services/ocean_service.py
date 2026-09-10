from datetime import datetime, timezone
from typing import Dict, Any
from backend.app.config import settings
from backend.app.data_sources.isro import ISROAdapter
from backend.app.data_sources.mosdac import MOSDACAdapter
from backend.app.data_sources.demo_data import DEMO_TELEMETRY
from backend.app.services.cache_service import cache_service


class OceanService:
    def __init__(self):
        self.isro = ISROAdapter()
        self.mosdac = MOSDACAdapter()

    async def get_ocean(self, lat: float, lon: float) -> Dict[str, Any]:
        cache_key = f"ocean:{lat:.2f}:{lon:.2f}"
        cached = await cache_service.get(cache_key)
        if cached:
            cached["data_mode"] = "cached"
            return cached

        isro_data = await self.isro.fetch_telemetry(lat, lon)
        mosdac_data = await self.mosdac.fetch_telemetry(lat, lon)

        sst = isro_data.get("sst_c", 28.4)
        current = mosdac_data.get("ocean_current_knots", 0.4)

        # Condition logic based on optimal pelagic fish temperatures (26-29°C)
        if 26.0 <= sst <= 29.5 and current <= 1.5:
            condition = "favorable"
        elif 24.0 <= sst <= 31.0:
            condition = "moderate"
        else:
            condition = "unfavorable"

        result = {
            "sea_surface_temperature_c": sst,
            "chlorophyll_density": isro_data.get("chlorophyll", "Favorable"),
            "chlorophyll_mg_m3": isro_data.get("chlorophyll_val", 1.85),
            "ocean_current_knots": current,
            "condition": condition,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": f"{self.isro.source_name} / {self.mosdac.source_name}",
            "confidence": "high",
            "data_mode": isro_data.get("data_mode", "demo" if settings.DEMO_MODE else "live"),
        }

        await cache_service.set(cache_key, result, ttl_sec=settings.CACHE_DEFAULT_TTL_SEC)
        return result


ocean_service = OceanService()
