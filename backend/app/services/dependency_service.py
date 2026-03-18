from uuid import UUID
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.dependency import Dependency, DependencyType
from app.schemas.dependency import DependencyCreate

class DependencyService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_dependency(self, dependency_in: DependencyCreate) -> Dependency | None:
        # Check for cycles before creating
        if await self.check_cycle(dependency_in.blocker_id, dependency_in.blocked_id):
            raise ValueError("Cycle detected: Cannot create dependency that forms a loop.")
        
        # Check if already exists
        existing = await self.session.execute(
            select(Dependency).where(
                Dependency.blocker_id == dependency_in.blocker_id,
                Dependency.blocked_id == dependency_in.blocked_id
            )
        )
        if existing.scalars().first():
            return None # Already exists
            
        dependency = Dependency(**dependency_in.model_dump())
        self.session.add(dependency)
        await self.session.commit()
        await self.session.refresh(dependency)
        return dependency

    async def remove_dependency(self, blocker_id: UUID, blocked_id: UUID) -> bool:
        result = await self.session.execute(
            select(Dependency).where(
                Dependency.blocker_id == blocker_id,
                Dependency.blocked_id == blocked_id
            )
        )
        dependency = result.scalars().first()
        if not dependency:
            return False
            
        await self.session.delete(dependency)
        await self.session.commit()
        return True

    async def get_blockers(self, responsibility_id: UUID) -> list[Dependency]:
        """Get responsibilities that mark this one as blocked."""
        result = await self.session.execute(
            select(Dependency).where(Dependency.blocked_id == responsibility_id)
        )
        return list(result.scalars().all())

    async def get_blocked(self, responsibility_id: UUID) -> list[Dependency]:
        """Get responsibilities blocked by this one."""
        result = await self.session.execute(
            select(Dependency).where(Dependency.blocker_id == responsibility_id)
        )
        return list(result.scalars().all())

    async def check_cycle(self, blocker_id: UUID, blocked_id: UUID) -> bool:
        """
        Check if making 'blocker' block 'blocked' would create a cycle.
        BFS/DFS to see if 'blocked' is already an ancestor of 'blocker'.
        If blocked is reachable from blocker (downstream), then adding blocker -> blocked creates a cycle?
        Wait: 
        New dependency: Blocker -> Blocked.
        Cycle if: Blocked can reach Blocker (Blocked -> ... -> Blocker).
        """
        visited = set()
        queue = [blocker_id] 
        
        # We want to forbid: Blocker -> Blocked IF Blocked ~> Blocker
        # So we check if Blocker is reachable from Blocked in the EXISTING graph.
        
        # Checking: Is there a path from Blocked to Blocker?
        check_queue = [blocked_id]
        visited_check = {blocked_id}
        
        while check_queue:
            current_id = check_queue.pop(0)
            if current_id == blocker_id:
                return True
                
            # Get what 'current' blocks (current -> next)
            # We are traversing downstream: who does 'current' block?
            deps = await self.get_blocked(current_id) 
            for dep in deps:
                next_node = dep.blocked_id # current blocks next_node
                if next_node not in visited_check:
                    visited_check.add(next_node)
                    check_queue.append(next_node)
                    
        return False
