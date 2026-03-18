"""
HRCE — Stage 8: WebSocket Route
WS /ws/{user_id}  — live push channel per user

Clients connect once per session. All server-side events (notifications,
responsibility updates, risk changes) are forwarded via Redis pub/sub.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.ws_manager import ws_manager
from app.core.logging import logger

ws_router = APIRouter()


@ws_router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time push events.

    Connect: ws://localhost:8000/ws/{user_id}

    Incoming client messages are ignored (read-only channel from server side).
    Server pushes JSON payloads of shape:
        {
            "event": "notification" | "responsibility_update" | "risk_update",
            "timestamp": "<ISO-8601>",
            "data": { ... }
        }
    """
    await ws_manager.connect(websocket, user_id)
    logger.info(f"WebSocket session opened for user: {user_id}")
    try:
        while True:
            # Keep alive: wait for client messages (ping/pong or close)
            data = await websocket.receive_text()
            # Echo keep-alive pings back so clients can detect stale connections
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        logger.info(f"WebSocket session closed for user: {user_id}")
    except Exception as exc:
        logger.warning(f"WebSocket error for user {user_id}: {exc}")
    finally:
        await ws_manager.disconnect(websocket, user_id)
