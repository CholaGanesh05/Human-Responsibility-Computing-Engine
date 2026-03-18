"""
HRCE — Notifications API Endpoints (Stage 11: Auth-protected)
Notifications are now scoped to the authenticated user (no user_id path param).
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("")
async def list_notifications(
    unread_only: bool = Query(False, description="Return only unread notifications"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns all notifications for the authenticated user, ordered newest first.
    Use ?unread_only=true to filter to unread alerts only.
    """
    service = NotificationService(session)
    notifications = await service.get_user_notifications(current_user.id, unread_only=unread_only)
    return {
        "user_id": current_user.id,
        "count": len(notifications),
        "notifications": [
            {
                "id": n.id,
                "type": n.type,
                "message": n.message,
                "is_read": n.is_read,
                "responsibility_id": n.responsibility_id,
                "created_at": n.created_at,
            }
            for n in notifications
        ],
    }


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Marks a notification as read. Returns the updated notification object."""
    service = NotificationService(session)
    notification = await service.mark_as_read(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {
        "id": notification.id,
        "is_read": notification.is_read,
        "type": notification.type,
        "message": notification.message,
    }


@router.post("/trigger-scan")
async def trigger_notification_scan(
    current_user: User = Depends(get_current_user),
):
    """
    Manually triggers the periodic responsibility scan.
    Useful during development and testing without waiting for Celery Beat.
    """
    from app.workers.notification_tasks import scan_upcoming_responsibilities
    task = scan_upcoming_responsibilities.delay()
    return {
        "status": "triggered",
        "task_id": task.id,
        "message": "Scan dispatched to Celery worker. Check task result for dispatch counts.",
    }
