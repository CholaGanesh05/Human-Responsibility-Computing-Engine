
import uuid
import enum
from datetime import datetime
from sqlalchemy import String, ForeignKey, Enum, UniqueConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base

class DependencyType(str, enum.Enum):
    HARD = "HARD" # Strict blocker
    SOFT = "SOFT" # Suggestion/Ordering

class Dependency(Base):
    __tablename__ = "dependencies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    
    blocker_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("responsibilities.id"))
    blocked_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("responsibilities.id"))
    
    dependency_type: Mapped[DependencyType] = mapped_column(Enum(DependencyType), default=DependencyType.HARD)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Constraints
    __table_args__ = (
        UniqueConstraint('blocker_id', 'blocked_id', name='uq_dependency_blocker_blocked'),
    )

    # Relationships
    # We need to define relationships in Responsibility model to access these, 
    # or just use backrefs here if we want. 
    # Let's add them here for clarity, but they might need to be configured in Responsibility too.
    blocker = relationship("Responsibility", foreign_keys=[blocker_id], backref="blocking_dependencies")
    blocked = relationship("Responsibility", foreign_keys=[blocked_id], backref="blocked_by_dependencies")
