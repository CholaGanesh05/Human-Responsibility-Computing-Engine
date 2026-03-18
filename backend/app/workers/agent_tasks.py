"""
HRCE — Agent Execution Tasks (Celery) — Stage 10

Four auto-triggered background tasks:

  1. decompose_event_task(event_id)
       Fired on every new event creation.
       Uses RiskResponseAgent to generate 3-5 responsibilities for the event.

  2. analyze_delayed_responsibilities_task()
       Celery Beat periodic job (every hour).
       Re-runs AI risk scoring on overdue/active items and updates urgency/impact.

  3. process_document_task(document_id)
       Fired on every document upload.
       Expands the embedding beyond the 1000-char truncation and saves back to DB.

  4. cascade_dependency_update_task(blocker_responsibility_id)
       Fired when a dependency is added.
       Walks downstream and marks all BLOCKED responsibilities' status.

NOTE: Uses synchronous psycopg2 (same pattern as notification_tasks.py) because Celery
workers run in a synchronous context. asyncio.run() is used only for WS pub/sub calls.
"""
from celery import shared_task
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, joinedload
import asyncio
import uuid

from app.core.config import settings
from app.models.responsibility import (
    Responsibility,
    ResponsibilityStatus,
    UrgencyLevel,
    ImpactLevel,
    PreparationStatus,
)
from app.models.dependency import Dependency
from app.models.document import Document

# ── Sync DB engine — lazy to avoid connecting at import time ─────────────────
_sync_engine = None


def _get_sync_session() -> Session:
    global _sync_engine
    if _sync_engine is None:
        _sync_db_url = settings.database_url.replace(
            "postgresql+asyncpg://", "postgresql+psycopg2://"
        )
        _sync_engine = create_engine(_sync_db_url, pool_pre_ping=True)
    return Session(_sync_engine)


# ── WS emit helpers (fire-and-forget from sync context) ─────────────────────
def _emit_responsibility_ws(user_id: str, responsibility: dict) -> None:
    try:
        import asyncio
        from app.core.event_emitter import emit_responsibility_update
        asyncio.run(emit_responsibility_update(user_id=user_id, responsibility=responsibility))
    except Exception:
        pass  # Never crash Celery on WS failure


def _emit_risk_ws(user_id: str, risk: dict) -> None:
    try:
        import asyncio
        from app.core.event_emitter import emit_risk_update
        asyncio.run(emit_risk_update(user_id=user_id, risk=risk))
    except Exception:
        pass


# ── Agent helper (easily patchable in tests) ─────────────────────────────────
def _run_agent(agent, title: str, description: str) -> dict:
    """Synchronously runs the async RiskResponseAgent.analyze call."""
    return asyncio.run(agent.analyze(title=title, description=description))


# ─────────────────────────────────────────────────────────────────────────────
# Task 1: Decompose Event into Responsibilities
# ─────────────────────────────────────────────────────────────────────────────

@shared_task(name="agent_tasks.decompose_event", bind=True, max_retries=2)
def decompose_event_task(self, event_id: str):
    """
    Auto-generates AI responsibilities for a newly created event.
    Idempotent: skips if the event already has responsibilities.
    """
    try:
        with _get_sync_session() as session:
            # Import Event model inline to avoid circular issues
            from app.models.event import Event

            event = session.get(Event, event_id)
            if not event:
                return {"status": "skipped", "reason": "event not found"}

            # Idempotency check
            existing = session.execute(
                select(Responsibility).where(
                    Responsibility.event_id == event.id,
                    Responsibility.parent_id == None,  # noqa: E711
                )
            ).scalars().all()
            if existing:
                return {"status": "skipped", "reason": "responsibilities already exist"}

            # ── AI decomposition ──────────────────────────────────────────────
            from app.agents.risk_agent import RiskResponseAgent

            agent = RiskResponseAgent()
            decompose_prompt = (
                f"This is for event planning decomposition. "
                f"Event: '{event.title}'. "
                f"Description: {event.description or 'No description'}. "
                f"Generate responsibilities needed to prepare for this event."
            )
            result = _run_agent(agent, event.title, decompose_prompt)

            # ── Build responsibility list from agent output ───────────────────
            prep_steps_raw = result.get("preparation_steps", [])
            prep_steps: list[str] = prep_steps_raw if isinstance(prep_steps_raw, list) else []
            urgency_val = result.get("urgency", "MEDIUM")
            impact_val = result.get("impact", "MEDIUM")

            # Ensure valid enum values
            urgency = UrgencyLevel(urgency_val) if urgency_val in UrgencyLevel._value2member_map_ else UrgencyLevel.MEDIUM
            impact = ImpactLevel(impact_val) if impact_val in ImpactLevel._value2member_map_ else ImpactLevel.MEDIUM

            if not prep_steps:
                prep_steps = [
                    f"Plan and prepare for {event.title}",
                    f"Review requirements for {event.title}",
                    f"Execute {event.title} deliverables",
                ]

            created = []
            for i, step_title in enumerate(prep_steps[0:5]):  # type: ignore
                r = Responsibility(
                    id=uuid.uuid4(),
                    title=str(step_title)[0:200],  # type: ignore
                    description=result.get("reasoning", "AI-generated preparation step"),
                    status=ResponsibilityStatus.PENDING,
                    priority=i + 1,
                    effort_score=max(1, min(10, 3 + i)),  # 3-7 scale
                    urgency=urgency,
                    impact=impact,
                    preparation_status=PreparationStatus.NOT_STARTED,
                    event_id=event.id,
                    assigned_to_id=event.owner_id,
                )
                session.add(r)
                created.append(r)

            session.commit()

            # ── WS push per created responsibility ────────────────────────────
            for r in created:
                _emit_responsibility_ws(
                    user_id=str(event.owner_id),
                    responsibility={
                        "id": str(r.id),
                        "title": r.title,
                        "status": r.status.value,
                        "urgency": r.urgency.value,
                        "event_id": str(r.event_id),
                    },
                )

            return {
                "status": "done",
                "event_id": event_id,
                "responsibilities_created": len(created),
            }

    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)


# ─────────────────────────────────────────────────────────────────────────────
# Task 2: Analyze Delayed Responsibilities (Periodic — Celery Beat)
# ─────────────────────────────────────────────────────────────────────────────

@shared_task(name="agent_tasks.analyze_delayed_responsibilities")
def analyze_delayed_responsibilities_task():
    """
    Celery Beat job (hourly). Re-runs AI risk scoring on overdue/near-due items.
    Updates urgency and impact fields, emits risk_update WS events.
    """
    from app.agents.risk_agent import RiskResponseAgent

    now = datetime.now(timezone.utc)
    window = now + timedelta(hours=24)

    with _get_sync_session() as session:
        # Overdue or due within 24h
        targets = session.execute(
            select(Responsibility)
            .options(joinedload(Responsibility.event))
            .where(
                Responsibility.due_date <= window,
                Responsibility.status.in_([
                    ResponsibilityStatus.PENDING,
                    ResponsibilityStatus.ACTIVE,
                ]),
            )
        ).scalars().unique().all()

    agent = RiskResponseAgent()
    updated: int = 0

    with _get_sync_session() as session:
        for r in targets:
            try:
                result = _run_agent(agent, r.title, r.description)
                urgency_val = result.get("urgency", r.urgency.value)
                impact_val = result.get("impact", r.impact.value)

                urgency = UrgencyLevel(urgency_val) if urgency_val in UrgencyLevel._value2member_map_ else r.urgency
                impact = ImpactLevel(impact_val) if impact_val in ImpactLevel._value2member_map_ else r.impact

                live_r = session.get(Responsibility, r.id)
                if live_r:
                    live_r.urgency = urgency
                    live_r.impact = impact
                    session.add(live_r)
                    session.commit()
                    updated = updated + 1  # type: ignore

                    # WS push
                    owner_id = str(r.event.owner_id) if r.event else None
                    if owner_id:
                        _emit_risk_ws(
                            user_id=owner_id,
                            risk={
                                "responsibility_id": str(r.id),
                                "urgency": urgency.value,
                                "impact": impact.value,
                            },
                        )
            except Exception:
                continue  # Don't fail the whole scan for one bad item

    return {"status": "done", "responsibilities_analyzed": updated}


# ─────────────────────────────────────────────────────────────────────────────
# Task 3: Process Document (expand embedding, link to events)
# ─────────────────────────────────────────────────────────────────────────────

@shared_task(name="agent_tasks.process_document", bind=True, max_retries=2)
def process_document_task(self, document_id: str):
    """
    Expands the document embedding beyond the 1000-char truncation and
    stores back to DB for richer semantic search.
    """
    try:
        with _get_sync_session() as session:
            doc = session.get(Document, document_id)
            if not doc:
                return {"status": "skipped", "reason": "document not found"}

            if not doc.content or doc.content == "Binary file or empty content":
                return {"status": "skipped", "reason": "no text content"}

            # Re-embed using full content (up to 8000 chars for richer vectors)
            from app.services.embedding_service import EmbeddingService
            full_text = doc.content[:8000]
            embedding = EmbeddingService.generate_embedding(full_text)

            if embedding:
                doc.embedding = embedding
                session.add(doc)
                session.commit()

            return {"status": "done", "document_id": document_id, "chars_embedded": len(full_text)}

    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)


# ─────────────────────────────────────────────────────────────────────────────
# Task 4: Cascade Dependency Updates
# ─────────────────────────────────────────────────────────────────────────────

@shared_task(name="agent_tasks.cascade_dependency_update", bind=True, max_retries=2)
def cascade_dependency_update_task(self, blocker_responsibility_id: str):
    """
    When a new dependency is added (blocker → blocked), walk all downstream
    responsibilities and mark them as BLOCKED. Emits WS events.
    """
    try:
        blocker_id = uuid.UUID(blocker_responsibility_id)

        with _get_sync_session() as session:
            # BFS to find all downstream blocked nodes
            visited = set()
            queue = [blocker_id]

            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)

                # Find everything blocked by `current`
                deps = session.execute(
                    select(Dependency).where(Dependency.blocker_id == current)
                ).scalars().all()

                for dep in deps:
                    blocked_resp = session.get(
                        Responsibility,
                        dep.blocked_id,
                        options=[joinedload(Responsibility.event)],
                    )
                    if blocked_resp and blocked_resp.status != ResponsibilityStatus.COMPLETED:
                        blocked_resp.status = ResponsibilityStatus.BLOCKED
                        session.add(blocked_resp)

                        # WS push
                        owner_id = None
                        if blocked_resp.event:
                            owner_id = str(blocked_resp.event.owner_id)
                        elif blocked_resp.assigned_to_id:
                            owner_id = str(blocked_resp.assigned_to_id)

                        if owner_id:
                            _emit_responsibility_ws(
                                user_id=owner_id,
                                responsibility={
                                    "id": str(blocked_resp.id),
                                    "title": blocked_resp.title,
                                    "status": "BLOCKED",
                                },
                            )

                    queue.append(dep.blocked_id)

            session.commit()

        return {
            "status": "done",
            "blocker_id": blocker_responsibility_id,
            "blocked_updated": len(visited) - 1,  # exclude root
        }

    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)
