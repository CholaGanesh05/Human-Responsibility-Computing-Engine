"""
HRCE — NotificationService
Async service for creating and querying notifications (used by the API layer).
"""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.notification import Notification, NotificationType


class NotificationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_notification(
        self,
        user_id: uuid.UUID,
        responsibility_id: uuid.UUID,
        notification_type: NotificationType,
        message: str,
    ) -> Notification:
        """
        Persists a new notification record and returns it.
        """
        notification = Notification(
            user_id=user_id,
            responsibility_id=responsibility_id,
            type=notification_type,
            message=message,
        )
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification

    async def get_user_notifications(
        self,
        user_id: uuid.UUID,
        unread_only: bool = False,
    ) -> list[Notification]:
        """
        Returns notifications for a user, optionally filtered to unread only.
        Ordered newest first.
        """
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        if unread_only:
            stmt = stmt.where(Notification.is_read == False)  # noqa: E712

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_as_read(self, notification_id: uuid.UUID) -> Notification | None:
        """
        Marks a notification as read. Returns the updated object, or None if not found.
        """
        result = await self.session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one_or_none()
        if not notification:
            return None

        notification.is_read = True
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification
