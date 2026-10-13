import redis.asyncio as redis
from .config import settings
import logging



_redis_client: redis.Redis | None = None
logger = logging.getLogger(__name__)


async def init_redis_client() -> redis.Redis | None:
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            )

    try:
        await client.ping()
        logger.info("Redis connected %s", client)
        _redis_client = client
    except Exception as e:
        logger.warning(f"Failed to connect to Redis server: {e}")
        await client.aclose()
        _redis_client = None
        return None

    return _redis_client

async def get_redis_client() -> redis.Redis | None:
    if _redis_client is None:
        return await init_redis_client()
    return _redis_client

async def close_redis_client() -> None:
    global _redis_client

    if _redis_client is None:
        return

    await _redis_client.aclose()
    _redis_client = None

async def redis_health() -> None:
    client = await get_redis_client()
    if client is None:
        return "disconnected"
    try:
        await client.ping()
        return "connected"
    except Exception:
        return "disconnected"