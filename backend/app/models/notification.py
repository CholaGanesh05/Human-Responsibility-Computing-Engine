"""
HRCE — Notification Model
Tracks reminders, escalations, and missed alerts for responsibilities.
"""
import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base


class NotificationType(str, enum.Enum):
    REMINDER   = "REMINDER"    # due date approaching (≤ 3 days)
    ESCALATION = "ESCALATION"  # overdue & still active
    MISSED     = "MISSED"      # past due & never completed


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    responsibility_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("responsibilities.id"), index=True)

    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType))
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user           = relationship("User")
    responsibility = relationship("Responsibility")
