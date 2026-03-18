"""
HRCE — Responsibilities API Endpoints (Stage 11: Auth-protected)
CRUD for responsibilities + dependency creation with cascade trigger.
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.responsibility_service import ResponsibilityService
from app.services.dependency_service import DependencyService
from app.schemas.responsibility import ResponsibilityCreate, ResponsibilityUpdate, ResponsibilityResponse
from app.schemas.dependency import DependencyCreate
from app.core.event_emitter import emit_responsibility_update

router = APIRouter()


@router.post("", response_model=ResponsibilityResponse, status_code=201)
async def create_responsibility(
    resp_in: ResponsibilityCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually create a responsibility (agent decomposition uses this internally too)."""
    service = ResponsibilityService(session)
    return await service.create_responsibility(resp_in)


@router.get("", response_model=list[ResponsibilityResponse])
async def list_responsibilities(
    skip: int = 0,
    limit: int = 200,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns all responsibilities owned by or assigned to the authenticated user."""
    service = ResponsibilityService(session)
    return await service.get_user_responsibilities(current_user.id, skip=skip, limit=limit)


@router.get("/{responsibility_id}", response_model=ResponsibilityResponse)
async def get_responsibility(
    responsibility_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ResponsibilityService(session)
    r = await service.get_responsibility(responsibility_id)
    if not r:
        raise HTTPException(status_code=404, detail="Responsibility not found")
    return r


@router.put("/{responsibility_id}", response_model=ResponsibilityResponse)
async def update_responsibility(
    responsibility_id: UUID,
    resp_in: ResponsibilityUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update status, urgency, effort, etc. Emits a live WS push on change.
    """
    service = ResponsibilityService(session)
    r = await service.update_responsibility(responsibility_id, resp_in)
    if not r:
        raise HTTPException(status_code=404, detail="Responsibility not found")

    # Live push
    try:
        assigned_user = str(r.assigned_to_id) if r.assigned_to_id else None
        if assigned_user:
            await emit_responsibility_update(
                user_id=assigned_user,
                responsibility={
                    "id": str(r.id),
                    "title": r.title,
                    "status": r.status.value,
                    "urgency": r.urgency.value,
                },
            )
    except Exception:
        pass

    return r


@router.delete("/{responsibility_id}", status_code=204)
async def delete_responsibility(
    responsibility_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ResponsibilityService(session)
    r = await service.get_responsibility(responsibility_id)
    if not r:
        raise HTTPException(status_code=404, detail="Responsibility not found")
    await session.delete(r)


@router.post("/{responsibility_id}/dependencies", status_code=201)
async def create_dependency(
    responsibility_id: UUID,
    blocked_id: UUID = Body(..., embed=True, description="ID of the responsibility that gets BLOCKED"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Adds a dependency: `responsibility_id` (blocker) → `blocked_id`.
    Automatically triggers cascade status update for all downstream blocked items.
    """
    dep_in = DependencyCreate(
        blocker_id=responsibility_id,
        blocked_id=blocked_id,
    )
    dep_service = DependencyService(session)
    try:
        dep = await dep_service.create_dependency(dep_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if dep is None:
        raise HTTPException(status_code=409, detail="Dependency already exists")

    # ─── Stage 10: cascade BLOCKED status downstream ──────────────────────────
    try:
        from app.workers.agent_tasks import cascade_dependency_update_task
        cascade_dependency_update_task.delay(str(responsibility_id))
    except Exception:
        pass

    return {"blocker_id": responsibility_id, "blocked_id": blocked_id, "status": "created"}
