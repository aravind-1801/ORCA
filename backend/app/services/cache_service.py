import json
import time
from typing import Optional, Any
from backend.app.config import settings
from backend.app.utils.logging import logger

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class CacheService:
    """
    Asynchronous caching layer.
    Attempts Redis first; falls back seamlessly to an in-memory dictionary with TTL.
    """

    def __init__(self):
        self._memory_cache = {}
        self._redis_client = None
        if REDIS_AVAILABLE:
            try:
                self._redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=1.0,
                )
            except Exception as e:
                logger.warning(f"Redis init warning: {e}. Using in-memory cache.")

    async def get(self, key: str) -> Optional[Any]:
        # Try Redis
        if self._redis_client:
            try:
                val = await self._redis_client.get(key)
                if val is not None:
                    return json.loads(val)
            except Exception:
                pass

        # In-memory fallback
        if key in self._memory_cache:
            expires_at, val = self._memory_cache[key]
            if time.time() < expires_at:
                return val
            else:
                del self._memory_cache[key]
        return None

    async def set(self, key: str, value: Any, ttl_sec: int = 300) -> bool:
        # Set Redis
        if self._redis_client:
            try:
                await self._redis_client.set(key, json.dumps(value), ex=ttl_sec)
            except Exception:
                pass

        # Set In-memory
        expires_at = time.time() + ttl_sec
        self._memory_cache[key] = (expires_at, value)
        return True


cache_service = CacheService()
