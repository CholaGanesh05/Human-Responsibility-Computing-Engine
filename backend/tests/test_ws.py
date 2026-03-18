"""
tests/test_ws.py — Unit tests for Stage 8: Real-Time Communication

Tests cover:
  1. Broadcaster.publish() calls Redis publish with correct channel + JSON
  2. ConnectionManager.connect() registers socket; disconnect() removes it
  3. event_emitter.emit_notification() calls broadcaster.publish with correct shape
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.core.broadcaster import Broadcaster, CHANNEL_PREFIX
from app.core.ws_manager import ConnectionManager
from app.core.event_emitter import emit_notification, emit_responsibility_update


# ──────────────────────────────────────────────────────────────────────────────
# Test 1: Broadcaster.publish()
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_broadcaster_publish_sends_to_correct_channel():
    """
    Broadcaster.publish() should call redis.publish with
    channel=hrce:user:{user_id} and a valid JSON payload.
    """
    broadcaster = Broadcaster()
    user_id = str(uuid4())
    payload = {"event": "notification", "data": {"message": "Hello"}}

    mock_redis = AsyncMock()
    broadcaster._redis = mock_redis

    await broadcaster.publish(user_id, payload)

    expected_channel = f"{CHANNEL_PREFIX}{user_id}"
    expected_data = json.dumps(payload)
    mock_redis.publish.assert_awaited_once_with(expected_channel, expected_data)


# ──────────────────────────────────────────────────────────────────────────────
# Test 2: ConnectionManager — connect / disconnect
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_connection_manager_connect_and_disconnect():
    """
    connect() should register the WebSocket under user_id.
    disconnect() should remove it and cancel the listener task.
    """
    manager = ConnectionManager()
    user_id = str(uuid4())

    mock_ws = AsyncMock()
    mock_ws.accept = AsyncMock()
    mock_ws.send_json = AsyncMock()

    # Patch the background listener so it doesn't actually run
    with patch.object(manager, "_listen_and_forward", new=AsyncMock()):
        await manager.connect(mock_ws, user_id)

        assert user_id in manager._connections
        assert mock_ws in manager._connections[user_id]

        await manager.disconnect(mock_ws, user_id)

        assert user_id not in manager._connections


# ──────────────────────────────────────────────────────────────────────────────
# Test 3: emit_notification()
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_emit_notification_publishes_correct_event():
    """
    emit_notification() should publish a payload with event='notification'
    and the notification data nested under 'data'.
    """
    user_id = str(uuid4())
    notification_data = {
        "id": str(uuid4()),
        "type": "REMINDER",
        "message": "⏰ Task due in 2 days",
    }

    with patch("app.core.event_emitter.broadcaster") as mock_broadcaster:
        mock_broadcaster.publish = AsyncMock()

        await emit_notification(user_id, notification_data)

        mock_broadcaster.publish.assert_awaited_once()
        call_args = mock_broadcaster.publish.call_args
        published_user_id = call_args[0][0]
        published_payload = call_args[0][1]

        assert published_user_id == user_id
        assert published_payload["event"] == "notification"
        assert published_payload["data"] == notification_data
        assert "timestamp" in published_payload


# ──────────────────────────────────────────────────────────────────────────────
# Test 4: emit_responsibility_update()
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_emit_responsibility_update_correct_event_type():
    """
    emit_responsibility_update() should publish event='responsibility_update'.
    """
    user_id = str(uuid4())
    resp_data = {"id": str(uuid4()), "title": "Prepare Report", "status": "ACTIVE"}

    with patch("app.core.event_emitter.broadcaster") as mock_broadcaster:
        mock_broadcaster.publish = AsyncMock()

        await emit_responsibility_update(user_id, resp_data)

        call_args = mock_broadcaster.publish.call_args
        published_payload = call_args[0][1]

        assert published_payload["event"] == "responsibility_update"
        assert published_payload["data"]["title"] == "Prepare Report"
