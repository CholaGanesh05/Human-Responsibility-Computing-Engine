from datetime import datetime
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, ConfigDict

class DependencyType(str, Enum):
    HARD = "HARD"
    SOFT = "SOFT"

class DependencyBase(BaseModel):
    blocker_id: UUID
    blocked_id: UUID
    dependency_type: DependencyType = DependencyType.HARD

class DependencyCreate(DependencyBase):
    pass

class DependencyResponse(DependencyBase):
    id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
