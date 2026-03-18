
import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base

class ResponsibilityStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"

class ComplexityLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class UrgencyLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ImpactLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class PreparationStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    READY = "READY"

class Responsibility(Base):
    __tablename__ = "responsibilities"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ResponsibilityStatus] = mapped_column(Enum(ResponsibilityStatus), default=ResponsibilityStatus.PENDING)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Stage 3: Effort and Complexity
    effort_score: Mapped[int] = mapped_column(Integer, default=1) # 1-10 scale
    complexity_level: Mapped[ComplexityLevel] = mapped_column(Enum(ComplexityLevel), default=ComplexityLevel.LOW)
    
    # Stage 6: Risk & Preparation
    urgency: Mapped[UrgencyLevel] = mapped_column(Enum(UrgencyLevel), default=UrgencyLevel.LOW)
    impact: Mapped[ImpactLevel] = mapped_column(Enum(ImpactLevel), default=ImpactLevel.LOW)
    preparation_status: Mapped[PreparationStatus] = mapped_column(Enum(PreparationStatus), default=PreparationStatus.NOT_STARTED)
    
    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("events.id"))
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("responsibilities.id"), nullable=True)
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    event = relationship("Event", back_populates="responsibilities")
    parent = relationship("Responsibility", remote_side=[id], back_populates="sub_responsibilities")
    sub_responsibilities = relationship("Responsibility", back_populates="parent", cascade="all, delete-orphan")
    assignee = relationship("User", back_populates="responsibilities")
