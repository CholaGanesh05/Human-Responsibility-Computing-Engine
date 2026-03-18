import asyncio
import uuid
import sys
from datetime import datetime, timedelta, timezone

# Add backend directory to sys.path
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.database import AsyncSessionFactory
from app.models.user import User
from app.models.event import Event
from app.models.responsibility import Responsibility, ResponsibilityStatus

async def seed_data():
    async with AsyncSessionFactory() as session:
        # 1. Create Users
        user1 = User(
            id=uuid.uuid4(),
            email="alice@example.com",
            hashed_password="hashed_secret",
            full_name="Alice Administrator",
            is_active=True,
            is_superuser=True
        )
        user2 = User(
            id=uuid.uuid4(),
            email="bob@example.com",
            hashed_password="hashed_secret",
            full_name="Bob Builder",
            is_active=True,
            is_superuser=False
        )
        
        session.add_all([user1, user2])
        await session.commit()
        
        print(f"Created users: {user1.email}, {user2.email}")

        # 2. Create Event
        event = Event(
            id=uuid.uuid4(),
            title="Annual Tech Conference",
            description="A gathering of tech enthusiasts.",
            start_time=datetime.now(timezone.utc) + timedelta(days=30),
            end_time=datetime.now(timezone.utc) + timedelta(days=32),
            location="San Francisco",
            owner_id=user1.id
        )
        session.add(event)
        await session.commit()
        
        print(f"Created event: {event.title}")

        # 3. Create Responsibilities (Hierarchical)
        resp_root = Responsibility(
            id=uuid.uuid4(),
            title="Organize Logistics",
            description="Manage venue and catering.",
            status=ResponsibilityStatus.ACTIVE,
            event_id=event.id,
            assigned_to_id=user1.id
        )
        session.add(resp_root)
        await session.commit() # Commit to get ID for parent reference

        resp_venue = Responsibility(
            id=uuid.uuid4(),
            title="Book Venue",
            description="Sign contract with Moscone Center.",
            status=ResponsibilityStatus.PENDING,
            event_id=event.id,
            parent_id=resp_root.id,
            assigned_to_id=user1.id
        )
        
        resp_catering = Responsibility(
            id=uuid.uuid4(),
            title="Arrange Catering",
            description="Select menu and confirm headcount.",
            status=ResponsibilityStatus.PENDING,
            event_id=event.id,
            parent_id=resp_root.id,
            assigned_to_id=user2.id
        )

        session.add_all([resp_venue, resp_catering])
        await session.commit()

        print("Created responsibilities hierarchy.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_data())
