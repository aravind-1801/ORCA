from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.app.config import settings
from backend.app.data_sources.incois import INCOISAdapter
from backend.app.services.geospatial_service import geospatial_service
from backend.app.services.cache_service import cache_service


class FishingZoneService:
    def __init__(self):
        self.adapter = INCOISAdapter()

    async def get_zones(self, user_lat: float, user_lon: float) -> List[Dict[str, Any]]:
        cache_key = f"zones:{user_lat:.2f}:{user_lon:.2f}"
        cached = await cache_service.get(cache_key)
        if cached:
            return cached

        raw_zones = await self.adapter.fetch_zones(user_lat, user_lon)
        ranked = geospatial_service.process_and_rank_zones(user_lat, user_lon, raw_zones)

        await cache_service.set(cache_key, ranked, ttl_sec=settings.CACHE_DEFAULT_TTL_SEC)
        return ranked

    async def get_zone_by_id(self, zone_id: str, user_lat: float, user_lon: float) -> Optional[Dict[str, Any]]:
        zones = await self.get_zones(user_lat, user_lon)
        for z in zones:
            if z.get("id", "").lower() == zone_id.lower() or z.get("code", "").lower() == zone_id.lower():
                return z
        return None

    async def get_best_zone(self, user_lat: float, user_lon: float) -> Dict[str, Any]:
        zones = await self.get_zones(user_lat, user_lon)
        if zones:
            return zones[0]
        # Fallback to default
        return {
            "id": "A12",
            "code": "ZONE A-12",
            "name": "Zone A-12",
            "distance_km": 12.0,
            "direction": "Southwest",
            "course_deg": 218,
            "course_heading": "218° SSW",
            "depth_m": 44,
            "potential": "high",
            "target_species": ["Indian Mackerel & Sardines"],
            "est_run_time_min": 42,
        }


fishing_zone_service = FishingZoneService()
