from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from backend.app.schemas.common import DataMode


class BaseMarineSourceAdapter(ABC):
    """
    Abstract interface for all marine and atmospheric data source adapters.
    Ensures clear separation between LIVE external data, CACHED data, and DEMO mode.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        pass

    @property
    @abstractmethod
    def provider(self) -> str:
        pass

    @abstractmethod
    async def fetch_telemetry(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fetch real-time or verified telemetry for coordinates."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Verify external endpoint availability."""
        pass
