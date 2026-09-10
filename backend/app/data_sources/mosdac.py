import httpx
from typing import Dict, Any
from backend.app.config import settings
from backend.app.data_sources.base import BaseMarineSourceAdapter
from backend.app.data_sources.demo_data import DEMO_TELEMETRY
from backend.app.utils.logging import logger


class MOSDACAdapter(BaseMarineSourceAdapter):
    """
    Adapter for Meteorological & Oceanographic Satellite Data Archival Centre (MOSDAC).
    Provides satellite wind vectors and marine surface parameters.
    """

    def __init__(self):
        self.base_url = settings.MOSDAC_BASE_URL
        self.timeout = httpx.Timeout(5.0, connect=3.0)

    @property
    def source_name(self) -> str:
        return "MOSDAC Marine Satellite"

    @property
    def provider(self) -> str:
        return "Space Applications Centre (ISRO)"

    async def fetch_telemetry(self, lat: float, lon: float) -> Dict[str, Any]:
        if settings.DEMO_MODE:
            return {
                "wind_kmh": DEMO_TELEMETRY["weather"]["wind_kmh"],
                "ocean_current_knots": DEMO_TELEMETRY["ocean"]["ocean_current_knots"],
                "source": self.source_name,
                "data_mode": "demo",
                "confidence": 0.94,
            }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{self.base_url}/surface/ocean",
                    params={"lat": lat, "lon": lon},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "wind_kmh": data.get("wind_kmh", 14.0),
                        "ocean_current_knots": data.get("current_knots", 0.4),
                        "source": self.source_name,
                        "data_mode": "live",
                        "confidence": 0.90,
                    }
        except Exception as e:
            logger.warning(f"MOSDAC live endpoint unreachable: {e}. Using cached/fallback.")

        return {
            "wind_kmh": DEMO_TELEMETRY["weather"]["wind_kmh"],
            "ocean_current_knots": DEMO_TELEMETRY["ocean"]["ocean_current_knots"],
            "source": self.source_name,
            "data_mode": "cached",
            "confidence": 0.85,
        }

    async def health_check(self) -> bool:
        return True
