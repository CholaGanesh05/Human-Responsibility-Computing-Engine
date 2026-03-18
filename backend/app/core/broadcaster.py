"""
HRCE — Stage 8: Redis Pub/Sub Broadcaster
Publishes and subscribes to per-user channels for real-time fan-out.
Channel pattern: hrce:user:{user_id}
"""
import json
import asyncio
from typing import AsyncGenerator

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.logging import logger

CHANNEL_PREFIX = "hrce:user:"


class Broadcaster:
    """
    Thin wrapper around Redis pub/sub.
    One Broadcaster is shared across the app (singleton via module-level instance).
    """

    def __init__(self):
        self._redis: aioredis.Redis | None = None

    def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    def _channel(self, user_id: str) -> str:
        return f"{CHANNEL_PREFIX}{user_id}"

    async def publish(self, user_id: str, payload: dict) -> None:
        """
        Publish a JSON payload to the user's Redis channel.
        Called by services/tasks when something changes.
        """
        try:
            r = self._get_redis()
            await r.publish(self._channel(user_id), json.dumps(payload))
        except Exception as exc:
            logger.warning(f"Broadcaster.publish failed for user {user_id}: {exc}")

    async def subscribe(self, user_id: str) -> AsyncGenerator[dict, None]:
        """
        Async generator that yields parsed payloads from the user's Redis channel.
        Each WebSocket connection runs one of these in a background task.
        """
        r = self._get_redis()
        pubsub = r.pubsub()
        await pubsub.subscribe(self._channel(user_id))
        logger.debug(f"Subscribed to channel: {self._channel(user_id)}")
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        yield json.loads(message["data"])
                    except json.JSONDecodeError:
                        logger.warning(f"Non-JSON message on channel {self._channel(user_id)}")
        finally:
            await pubsub.unsubscribe(self._channel(user_id))
            await pubsub.aclose()
            logger.debug(f"Unsubscribed from channel: {self._channel(user_id)}")


# ── Singleton instance ────────────────────────────────────────────────────────
broadcaster = Broadcaster()
