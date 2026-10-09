import hashlib
import json
import logging
from typing import Any

from .config import settings
from .redis_config import get_redis_client


logger = logging.getLogger(__name__)

def make_cache_key(prefix: str, *parts: Any, **kwargs: Any) -> str:
    payload = {
        "parts": [str(p) for p in parts],
        "kwargs": {k: str(v) for k, v in sorted(kwargs.items()) if v is not None},
    }

    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()[:16]

    return f"{prefix}:{digest}"


class CacheService:

    def __init__(self) -> None:
        self.enabled = settings.CACHE_ENABLED

    async def get(self, key: str) -> Any | None:
        if not self.enabled:
            return None

        client = await get_redis_client()
        if client is None:
            return None

        try:
            raw = await client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as e:
            logger.warning("Cache GET failed for %s: %s", key, e)
            return None

    async def set(self, key: str, value: Any, ttl: int) -> None:
        if not self.enabled:
            return None

        client = await get_redis_client()
        if client is None:
            return None

        try:
            await client.set(key, json.dumps(value, default=str), ex=ttl)
        except Exception as e:
            logger.warning("Cache SET failed for %s: %s", key, e)
            return None

    async def delete_pattern(self, pattern: str) -> None:
        if not self.enabled:
            return None
        client = await get_redis_client()
        if client is None:
            return None
        try:
            async for key in client.scan_iter(match=pattern, count=100):
                await client.delete(key)
        except Exception as e:
            logger.warning("Cache DELETE failed for %s: %s", pattern, e)


cache_service = CacheService()