from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class EventBase(BaseModel):
    title: str
    description: str | None = None
    start_time: datetime
    end_time: datetime
    is_all_day: bool = False
    location: str | None = None
    recurrence_rule: str | None = None
    preparation_time_minutes: int = 0

class EventCreate(EventBase):
    pass

class EventUpdate(EventBase):
    title: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    recurrence_rule: str | None = None
    preparation_time_minutes: int | None = None

class EventResponse(EventBase):
    id: UUID
    owner_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
