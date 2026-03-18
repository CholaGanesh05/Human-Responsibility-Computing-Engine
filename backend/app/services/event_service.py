from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event import Event
from app.schemas.event import EventCreate, EventUpdate

class EventService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_event(self, event_in: EventCreate, owner_id: UUID) -> Event:
        event = Event(**event_in.model_dump(), owner_id=owner_id)
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def get_event(self, event_id: UUID) -> Event | None:
        result = await self.session.execute(select(Event).where(Event.id == event_id))
        return result.scalars().first()

    async def get_user_events(self, user_id: UUID, skip: int = 0, limit: int = 100) -> list[Event]:
        result = await self.session.execute(
            select(Event).where(Event.owner_id == user_id).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def update_event(self, event_id: UUID, event_in: EventUpdate) -> Event | None:
        event = await self.get_event(event_id)
        if not event:
            return None
        
        update_data = event_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(event, key, value)
        
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def delete_event(self, event_id: UUID) -> bool:
        event = await self.get_event(event_id)
        if not event:
            return False
        
        await self.session.delete(event)
        await self.session.commit()
        return True
