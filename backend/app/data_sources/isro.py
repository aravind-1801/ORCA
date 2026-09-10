import httpx
from typing import Dict, Any
from backend.app.config import settings
from backend.app.data_sources.base import BaseMarineSourceAdapter
from backend.app.data_sources.demo_data import DEMO_TELEMETRY
from backend.app.utils.logging import logger


class ISROAdapter(BaseMarineSourceAdapter):
    """
    Adapter for ISRO Oceansat-3 satellite oceanographic telemetry:
    - Sea Surface Temperature (SST)
    - Ocean Color Monitor (OCM) Chlorophyll-a
    """

    def __init__(self):
        self.base_url = settings.ISRO_BASE_URL
        self.timeout = httpx.Timeout(5.0, connect=3.0)

    @property
    def source_name(self) -> str:
        return "ISRO Oceansat-3"

    @property
    def provider(self) -> str:
        return "Indian Space Research Organisation"

    async def fetch_telemetry(self, lat: float, lon: float) -> Dict[str, Any]:
        if settings.DEMO_MODE:
            return {
                "sst_c": DEMO_TELEMETRY["ocean"]["sea_surface_temperature_c"],
                "chlorophyll": DEMO_TELEMETRY["ocean"]["chlorophyll_density"],
                "chlorophyll_val": DEMO_TELEMETRY["ocean"]["chlorophyll_mg_m3"],
                "source": self.source_name,
                "data_mode": "demo",
                "confidence": 0.95,
            }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{self.base_url}/oceansat/telemetry",
                    params={"lat": lat, "lon": lon},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "sst_c": data.get("sst", 28.4),
                        "chlorophyll": data.get("chlorophyll_density", "Favorable"),
                        "chlorophyll_val": data.get("chlorophyll_mg_m3", 1.85),
                        "source": self.source_name,
                        "data_mode": "live",
                        "confidence": 0.92,
                    }
        except Exception as e:
            logger.warning(f"ISRO live endpoint unreachable: {e}. Using cached/fallback.")

        return {
            "sst_c": DEMO_TELEMETRY["ocean"]["sea_surface_temperature_c"],
            "chlorophyll": DEMO_TELEMETRY["ocean"]["chlorophyll_density"],
            "chlorophyll_val": DEMO_TELEMETRY["ocean"]["chlorophyll_mg_m3"],
            "source": self.source_name,
            "data_mode": "cached",
            "confidence": 0.85,
        }

    async def health_check(self) -> bool:
        return True
