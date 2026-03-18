"""
HRCE — Stage 8: WebSocket Connection Manager
Tracks active WebSocket connections per user.
Forwards messages received from Redis pub/sub to connected sockets.
"""
import asyncio
import json
from collections import defaultdict

from fastapi import WebSocket
from app.core.logging import logger


class ConnectionManager:
    """
    Manages all active WebSocket connections.

    Each user_id maps to a set of WebSocket objects (multiple tabs/devices).
    A background asyncio task per connection listens to Redis and forwards messages.
    """

    def __init__(self):
        # user_id -> set of active WebSockets
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        # websocket -> background listener task
        self._tasks: dict[WebSocket, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """Accept the WebSocket and start listening for Redis messages."""
        await websocket.accept()
        self._connections[user_id].add(websocket)
        # Spawn a background task that forwards Redis messages to this socket
        task = asyncio.create_task(self._listen_and_forward(websocket, user_id))
        self._tasks[websocket] = task
        logger.info(f"WS connected: user={user_id}, total={len(self._connections[user_id])}")

    async def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        """Remove a WebSocket and cancel its Redis listener."""
        self._connections[user_id].discard(websocket)
        if not self._connections[user_id]:
            del self._connections[user_id]

        task = self._tasks.pop(websocket, None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        logger.info(f"WS disconnected: user={user_id}")

    async def send_to_user(self, user_id: str, payload: dict) -> None:
        """
        Push a JSON payload directly to all sockets for a user.
        Used for server-initiated pushes (e.g., from event emitter).
        """
        dead_sockets = set()
        for ws in self._connections.get(user_id, set()):
            try:
                await ws.send_json(payload)
            except Exception:
                dead_sockets.add(ws)

        for ws in dead_sockets:
            await self.disconnect(ws, user_id)

    async def _listen_and_forward(self, websocket: WebSocket, user_id: str) -> None:
        """Background task: subscribe to Redis channel and forward messages to socket."""
        from app.core.broadcaster import broadcaster
        try:
            async for payload in broadcaster.subscribe(user_id):
                try:
                    await websocket.send_json(payload)
                except Exception:
                    break  # Socket closed — exit loop
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.warning(f"WS listener error for user {user_id}: {exc}")


# ── Singleton instance ────────────────────────────────────────────────────────
ws_manager = ConnectionManager()
