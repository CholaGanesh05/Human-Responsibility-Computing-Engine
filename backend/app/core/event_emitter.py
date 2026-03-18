"""
HRCE — Stage 8: Event Emitter
Convenience helpers for publishing live events to connected WebSocket clients.
Called by services and Celery tasks after state changes.
"""
from datetime import datetime, timezone
from app.core.broadcaster import broadcaster


async def emit_notification(user_id: str, notification: dict) -> None:
    """
    Push a notification event to the user's live WebSocket channel.

    Args:
        user_id:       UUID string of the recipient user.
        notification:  Dict with notification fields (type, message, id, etc.)
    """
    payload = {
        "event": "notification",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": notification,
    }
    await broadcaster.publish(user_id, payload)


async def emit_responsibility_update(user_id: str, responsibility: dict) -> None:
    """
    Push a responsibility state update to the user's live WebSocket channel.
    Triggered when a responsibility's status, urgency, or impact changes.

    Args:
        user_id:        UUID string of the owner/assignee.
        responsibility: Dict with responsibility fields (id, title, status, etc.)
    """
    payload = {
        "event": "responsibility_update",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": responsibility,
    }
    await broadcaster.publish(user_id, payload)


async def emit_risk_update(user_id: str, risk_data: dict) -> None:
    """
    Push a risk score or AI analysis update to the user's live WebSocket channel.

    Args:
        user_id:   UUID string of the owner/assignee.
        risk_data: Dict with risk_score, urgency, impact, preparation_steps.
    """
    payload = {
        "event": "risk_update",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": risk_data,
    }
    await broadcaster.publish(user_id, payload)
