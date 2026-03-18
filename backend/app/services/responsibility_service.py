from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.responsibility import Responsibility, ResponsibilityStatus
from app.models.event import Event
from app.schemas.responsibility import ResponsibilityCreate, ResponsibilityUpdate

class ResponsibilityService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_responsibility(self, responsibility_in: ResponsibilityCreate) -> Responsibility:
        responsibility = Responsibility(**responsibility_in.model_dump())
        self.session.add(responsibility)
        await self.session.commit()
        await self.session.refresh(responsibility)
        return responsibility

    async def get_responsibility(self, responsibility_id: UUID) -> Responsibility | None:
        result = await self.session.execute(select(Responsibility).where(Responsibility.id == responsibility_id))
        return result.scalars().first()

    async def get_event_responsibilities(self, event_id: UUID) -> list[Responsibility]:
        result = await self.session.execute(
            select(Responsibility).where(Responsibility.event_id == event_id)
        )
        return list(result.scalars().all())

    async def get_sub_responsibilities(self, parent_id: UUID) -> list[Responsibility]:
        result = await self.session.execute(
            select(Responsibility).where(Responsibility.parent_id == parent_id)
        )
        return list(result.scalars().all())

    async def get_user_responsibilities(
        self, user_id: UUID, skip: int = 0, limit: int = 200
    ) -> list[Responsibility]:
        """Get all responsibilities assigned to a user or belonging to user's events."""
        from sqlalchemy import or_
        result = await self.session.execute(
            select(Responsibility)
            .join(Event, Responsibility.event_id == Event.id, isouter=True)
            .where(
                or_(
                    Responsibility.assigned_to_id == user_id,
                    Event.owner_id == user_id,
                )
            )
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_responsibility(self, responsibility_id: UUID, responsibility_in: ResponsibilityUpdate) -> Responsibility | None:
        responsibility = await self.get_responsibility(responsibility_id)
        if not responsibility:
            return None
        
        update_data = responsibility_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(responsibility, key, value)
        
        self.session.add(responsibility)
        await self.session.commit()
        await self.session.refresh(responsibility)
        return responsibility

    async def delete_responsibility(self, responsibility_id: UUID) -> bool:
        responsibility = await self.get_responsibility(responsibility_id)
        if not responsibility:
            return False

        await self.session.delete(responsibility)
        await self.session.commit()
        return True

    async def calculate_aggregate_effort(self, responsibility_id: UUID) -> int:
        """
        Calculates total effort score including all sub-responsibilities recursively.
        """
        root = await self.get_responsibility(responsibility_id)
        if not root:
             return 0
             
        total_effort = root.effort_score
        
        # Get children
        children = await self.get_sub_responsibilities(responsibility_id)
        for child in children:
            total_effort += await self.calculate_aggregate_effort(child.id)
            
        return total_effort

