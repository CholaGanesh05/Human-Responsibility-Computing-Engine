"""
HRCE Backend — Redis Client
Async Redis connection using the redis-py library.
"""
import redis.asyncio as aioredis

from app.core.config import settings
from app.core.logging import logger

# ─── Singleton client ─────────────────────────────────────────
_redis_client: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    """Return the shared Redis client instance."""
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized. Call connect_redis() first.")
    return _redis_client


async def connect_redis() -> None:
    """Initialize Redis connection pool on startup."""
    global _redis_client
    _redis_client = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        max_connections=20,
    )
    try:
        await _redis_client.ping()
        logger.info("✅ Redis connected successfully")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        raise


async def disconnect_redis() -> None:
    """Close Redis connection pool on shutdown."""
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Redis connection closed")
