"""
tests/test_notifications.py — Unit tests for Stage 7: Notification Orchestration

Tests cover:
  1. Creating a REMINDER notification
  2. Listing user notifications (with unread_only filter)
  3. Marking a notification as read
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from app.models.notification import Notification, NotificationType
from app.services.notification_service import NotificationService


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def make_notification(**kwargs) -> MagicMock:
    defaults = {
        "id": uuid4(),
        "user_id": uuid4(),
        "responsibility_id": uuid4(),
        "type": NotificationType.REMINDER,
        "message": "⏰ Reminder: Task is due in 2 day(s).",
        "is_read": False,
        "created_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    obj = MagicMock(spec=Notification)
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


# ──────────────────────────────────────────────────────────────────────────────
# Test 1: Create notification
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_notification_success():
    """
    NotificationService.create_notification() should persist and return a Notification.
    """
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    user_id = uuid4()
    resp_id = uuid4()
    expected_notification = make_notification(
        user_id=user_id,
        responsibility_id=resp_id,
        type=NotificationType.REMINDER,
    )
    mock_session.refresh = AsyncMock(side_effect=lambda n: None)

    service = NotificationService(mock_session)

    # Patch the Notification constructor to return our mock
    with patch("app.services.notification_service.Notification", return_value=expected_notification):
        result = await service.create_notification(
            user_id=user_id,
            responsibility_id=resp_id,
            notification_type=NotificationType.REMINDER,
            message="⏰ Reminder: Task is due in 2 day(s).",
        )

    mock_session.add.assert_called_once_with(expected_notification)
    mock_session.commit.assert_awaited_once()
    assert result.type == NotificationType.REMINDER
    assert result.is_read is False


# ──────────────────────────────────────────────────────────────────────────────
# Test 2: Get user notifications (unread_only filter)
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_user_notifications_unread_only():
    """
    get_user_notifications(unread_only=True) should only return unread notifications.
    """
    user_id = uuid4()
    mock_session = AsyncMock()

    unread_notif = make_notification(user_id=user_id, is_read=False)
    read_notif = make_notification(user_id=user_id, is_read=True)

    # Mock the execute → scalars → all chain
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [unread_notif]  # only unread returned
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)

    service = NotificationService(mock_session)
    results = await service.get_user_notifications(user_id, unread_only=True)
    assert isinstance(results, list)

    assert len(results) == 1
    assert results[0].is_read is False
    mock_session.execute.assert_awaited_once()


# ──────────────────────────────────────────────────────────────────────────────
# Test 3: Mark notification as read
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_mark_notification_as_read():
    """
    mark_as_read() should set is_read=True and commit.
    """
    mock_session = AsyncMock()
    notification_id = uuid4()
    notification = make_notification(id=notification_id, is_read=False)

    mock_scalar = MagicMock()
    mock_scalar.scalar_one_or_none.return_value = notification
    mock_session.execute = AsyncMock(return_value=mock_scalar)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    service = NotificationService(mock_session)
    result = await service.mark_as_read(notification_id)

    assert result.is_read is True
    mock_session.add.assert_called_once_with(notification)
    mock_session.commit.assert_awaited_once()


# ──────────────────────────────────────────────────────────────────────────────
# Test 4: Mark notification not found → returns None
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_mark_notification_as_read_not_found():
    """
    mark_as_read() should return None when the notification doesn't exist.
    """
    mock_session = AsyncMock()
    mock_scalar = MagicMock()
    mock_scalar.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_scalar)

    service = NotificationService(mock_session)
    result = await service.mark_as_read(uuid4())

    assert result is None
