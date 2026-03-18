import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

# Ensure the backend directory is in the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.core.database import AsyncSessionFactory
from app.core.security import hash_password

from app.models.user import User
from app.models.event import Event
from app.models.responsibility import Responsibility
from app.models.notification import Notification

async def seed():
    print("Starting HRCE Database Seeding...")

    async with AsyncSessionFactory() as session:
        # 1. Create or GET Test User
        email = "demo@hrce.ai"
        plain_password = "password123"

        # Check if user already exists
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalars().first()

        if not user:
            print(f"Creating test user: {email}")
            user = User(
                email=email,
                hashed_password=hash_password(plain_password),
                full_name="HRCE Demo User",
                is_active=True,
                is_superuser=True
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            print(f"User {email} already exists. Using existing ID: {user.id}")

            # Option: Delete existing responsibilities/events for a clean slate
            # But let's just append to make it look active, or you can drop all.
            # We'll just leave them for now so the user has lots to look at!

        # 2. Create Events
        now = datetime.now(timezone.utc)
        print("Creating Events...")

        event1 = Event(
            title="Q3 Strategy Meeting",
            description="Quarterly planning with the board of directors.",
            start_time=now + timedelta(days=2, hours=10),
            end_time=now + timedelta(days=2, hours=12),
            is_all_day=False,
            location="Boardroom A",
            preparation_time_minutes=120,
            owner_id=user.id
        )

        event2 = Event(
            title="Medical Appointment",
            description="Annual checkup downtown.",
            start_time=now + timedelta(days=5, hours=9),
            end_time=now + timedelta(days=5, hours=10),
            is_all_day=False,
            location="City Clinic",
            preparation_time_minutes=30,
            owner_id=user.id
        )

        session.add_all([event1, event2])
        await session.commit()
        await session.refresh(event1)
        await session.refresh(event2)

        # 3. Create Responsibilities for Event 1 (Q3 Strategy)
        print("Creating Responsibilities...")

        r1 = Responsibility(
            title="Prepare Financial Slide Deck",
            description="Compile revenue and burn rate numbers from Q2.",
            status="ACTIVE",
            priority=1,
            due_date=now + timedelta(days=1),
            effort_score=8,
            complexity_level="HIGH",
            urgency="CRITICAL",
            impact="HIGH",
            preparation_status="IN_PROGRESS",
            event_id=event1.id,
            assigned_to_id=user.id
        )

        r2 = Responsibility(
            title="Book Catering",
            description="Order lunch for 12 people.",
            status="PENDING",
            priority=2,
            due_date=now + timedelta(days=1, hours=5),
            effort_score=2,
            complexity_level="LOW",
            urgency="MEDIUM",
            impact="LOW",
            preparation_status="NOT_STARTED",
            event_id=event1.id,
            assigned_to_id=user.id
        )

        session.add_all([r1, r2])
        await session.commit()
        await session.refresh(r1)

        # Sub-responsibility for Slide Deck
        r1_sub = Responsibility(
            title="Get finalized Q2 numbers from Accounting",
            status="BLOCKED",
            priority=1,
            effort_score=5,
            complexity_level="MEDIUM",
            urgency="HIGH",
            impact="MEDIUM",
            preparation_status="NOT_STARTED",
            event_id=event1.id,
            parent_id=r1.id,
            assigned_to_id=user.id
        )
        session.add(r1_sub)

        # Responsibilities for Event 2
        r3 = Responsibility(
            title="Gather medical records",
            status="COMPLETED",
            priority=1,
            effort_score=3,
            complexity_level="LOW",
            urgency="LOW",
            impact="MEDIUM",
            preparation_status="READY",
            event_id=event2.id,
            assigned_to_id=user.id
        )
        session.add(r3)
        
        await session.commit()
        await session.refresh(r1_sub)
        await session.refresh(r3)

        # 4. Create Notifications
        print("Creating Notifications...")

        n1 = Notification(
            type="REMINDER",
            message="Preparation for 'Q3 Strategy Meeting' must start soon.",
            is_read=False,
            user_id=user.id,
            responsibility_id=r1.id
        )
        n2 = Notification(
            type="ESCALATION",
            message="'Prepare Financial Slide Deck' is at risk because you are blocked on Accounting.",
            is_read=False,
            user_id=user.id,
            responsibility_id=r1_sub.id
        )
        n3 = Notification(
            type="MISSED",
            message="Don't forget to book catering by tomorrow.",
            is_read=True,
            user_id=user.id,
            responsibility_id=r2.id
        )

        session.add_all([n1, n2, n3])
        await session.commit()

        print("\n\nSeed completed successfully!")
        print("="*40)
        print("  Login details:")
        print(f"  Email:    {email}")
        print(f"  Password: {plain_password}")
        print("="*40)

if __name__ == "__main__":
    asyncio.run(seed())
