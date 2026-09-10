from datetime import datetime, timezone
from typing import List, Dict, Any
from backend.app.data_sources.incois import INCOISAdapter
from backend.app.data_sources.demo_data import DEMO_ALERTS
from backend.app.services.cache_service import cache_service
from backend.app.config import settings


class AlertService:
    def __init__(self):
        self.adapter = INCOISAdapter()

    async def get_active_alerts(self, lat: float, lon: float) -> List[Dict[str, Any]]:
        cache_key = f"alerts:{lat:.2f}:{lon:.2f}"
        cached = await cache_service.get(cache_key)
        if cached is not None:
            return cached

        raw_alerts = await self.adapter.fetch_alerts(lat, lon)
        now = datetime.now(timezone.utc)

        valid_alerts = []
        for a in raw_alerts:
            # Filter expired
            valid_until = a.get("valid_until")
            if valid_until:
                if isinstance(valid_until, str):
                    try:
                        dt = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
                        if dt.timestamp() < now.timestamp():
                            continue
                    except Exception:
                        pass
            valid_alerts.append(a)

        # Sort: DANGER -> CAUTION -> INFO
        severity_order = {"danger": 1, "caution": 2, "info": 3}
        valid_alerts.sort(key=lambda x: severity_order.get(str(x.get("severity", "")).lower(), 4))

        await cache_service.set(cache_key, valid_alerts, ttl_sec=settings.CACHE_ALERT_TTL_SEC)
        return valid_alerts


alert_service = AlertService()
