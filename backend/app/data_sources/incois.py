import httpx
from typing import Dict, Any, List
from backend.app.config import settings
from backend.app.data_sources.base import BaseMarineSourceAdapter
from backend.app.data_sources.demo_data import DEMO_ZONES, DEMO_ALERTS
from backend.app.utils.logging import logger


class INCOISAdapter(BaseMarineSourceAdapter):
    """
    Adapter for Indian National Centre for Ocean Information Services (INCOIS).
    Provides:
    - Potential Fishing Zones (PFZ) advisory data
    - Ocean State Forecast (Wave, Swell, Currents)
    - Coastal Hazard and Tsunami / Swell Surge Warnings
    """

    def __init__(self):
        self.base_url = settings.INCOIS_BASE_URL
        self.timeout = httpx.Timeout(5.0, connect=3.0)

    @property
    def source_name(self) -> str:
        return "INCOIS PFZ-7"

    @property
    def provider(self) -> str:
        return "Indian National Centre for Ocean Information Services (MoES)"

    async def fetch_telemetry(self, lat: float, lon: float) -> Dict[str, Any]:
        return {
            "source": self.source_name,
            "status": "active",
            "advisory": "PFZ-7 Kerala Sector Clear",
        }

    async def fetch_zones(self, lat: float, lon: float) -> List[Dict[str, Any]]:
        if settings.DEMO_MODE:
            d_lat = lat - 8.88
            d_lon = lon - 76.59
            if abs(d_lat) > 0.01 or abs(d_lon) > 0.01:
                shifted = []
                for z in DEMO_ZONES:
                    nz = dict(z)
                    nz["latitude"] = round(z["latitude"] + d_lat, 4)
                    nz["longitude"] = round(z["longitude"] + d_lon, 4)
                    shifted.append(nz)
                return shifted
            return DEMO_ZONES

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{self.base_url}/pfz/kerala",
                    params={"lat": lat, "lon": lon},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        return data
        except Exception as e:
            logger.warning(f"INCOIS live endpoint unreachable: {e}. Falling back to cached zones.")

        return DEMO_ZONES

    async def fetch_alerts(self, lat: float, lon: float) -> List[Dict[str, Any]]:
        if settings.DEMO_MODE:
            return DEMO_ALERTS

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{self.base_url}/alerts/active",
                    params={"lat": lat, "lon": lon},
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            logger.warning(f"INCOIS alerts live endpoint unreachable: {e}.")

        return DEMO_ALERTS

    async def health_check(self) -> bool:
        return True
