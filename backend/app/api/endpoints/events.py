"""
HRCE — Events API Endpoints (Auth-protected + Rate Limited)
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.models.user import User
from app.schemas.event import EventCreate, EventResponse, EventUpdate
from app.services.event_service import EventService
from app.services.responsibility_service import ResponsibilityService

router = APIRouter()


@router.post("", response_model=EventResponse, status_code=201)
@limiter.limit("100/minute")
async def create_event(
    request: Request,
    event_in: EventCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new event owned by the authenticated user.
    Automatically enqueues AI responsibility decomposition via Celery (Stage 10).
    """
    service = EventService(session)
    event = await service.create_event(event_in, owner_id=current_user.id)

    # ─── Stage 10: Auto-trigger responsibility decomposition ──────────────────
    try:
        from app.workers.agent_tasks import decompose_event_task
        decompose_event_task.delay(str(event.id))
    except Exception:
        pass  # Never fail the event creation if Celery is unavailable

    return event


@router.get("", response_model=list[EventResponse])
@limiter.limit("100/minute")
async def list_events(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns all events owned by the authenticated user."""
    service = EventService(session)
    return await service.get_user_events(current_user.id, skip=skip, limit=limit)


@router.get("/{event_id}", response_model=EventResponse)
@limiter.limit("100/minute")
async def get_event(
    request: Request,
    event_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = EventService(session)
    event = await service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.put("/{event_id}", response_model=EventResponse)
@limiter.limit("100/minute")
async def update_event(
    request: Request,
    event_id: UUID,
    event_in: EventUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = EventService(session)
    event = await service.update_event(event_id, event_in)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.delete("/{event_id}", status_code=204)
@limiter.limit("60/minute")
async def delete_event(
    request: Request,
    event_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = EventService(session)
    deleted = await service.delete_event(event_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Event not found")


@router.get("/{event_id}/responsibilities")
@limiter.limit("100/minute")
async def get_event_responsibilities(
    request: Request,
    event_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns all responsibilities (flat list) linked to an event."""
    r_service = ResponsibilityService(session)
    responsibilities = await r_service.get_event_responsibilities(event_id)
    return [
        {
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "status": r.status,
            "priority": r.priority,
            "due_date": r.due_date,
            "effort_score": r.effort_score,
            "complexity_level": r.complexity_level,
            "urgency": r.urgency,
            "impact": r.impact,
            "preparation_status": r.preparation_status,
            "event_id": r.event_id,
            "parent_id": r.parent_id,
            "assigned_to_id": r.assigned_to_id,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
        }
        for r in responsibilities
    ]
