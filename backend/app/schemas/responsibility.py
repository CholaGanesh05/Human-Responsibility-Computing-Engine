from datetime import datetime
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, ConfigDict

class ResponsibilityStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"

class ComplexityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class ResponsibilityBase(BaseModel):
    title: str
    description: str | None = None
    status: ResponsibilityStatus = ResponsibilityStatus.PENDING
    priority: int = 0
    due_date: datetime | None = None
    effort_score: int = 1
    complexity_level: ComplexityLevel = ComplexityLevel.LOW

class ResponsibilityCreate(ResponsibilityBase):
    event_id: UUID
    parent_id: UUID | None = None
    assigned_to_id: UUID | None = None

class ResponsibilityUpdate(ResponsibilityBase):
    title: str | None = None
    status: ResponsibilityStatus | None = None
    effort_score: int | None = None
    complexity_level: ComplexityLevel | None = None

class ResponsibilityResponse(ResponsibilityBase):
    id: UUID
    event_id: UUID
    parent_id: UUID | None
    assigned_to_id: UUID | None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
