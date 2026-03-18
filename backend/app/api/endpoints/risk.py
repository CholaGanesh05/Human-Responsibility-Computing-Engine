"""
HRCE — Risk API Endpoints (Stage 11: Auth-protected)
"""
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.risk_service import RiskService

router = APIRouter()


@router.post("/analyze/{responsibility_id}")
async def analyze_responsibility_risk(
    responsibility_id: UUID = Path(..., title="The ID of the responsibility to analyze"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Triggers AI analysis to determine Urgency and Impact, and suggests preparation steps.
    Updates the Responsibility record.
    """
    service = RiskService(session)
    try:
        result = await service.analyze_responsibility_ai(responsibility_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/score/{responsibility_id}")
async def get_risk_score(
    responsibility_id: UUID = Path(..., title="The ID of the responsibility"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns the calculated risk score (0-100) based on current fields."""
    from app.services.responsibility_service import ResponsibilityService

    resp_service = ResponsibilityService(session)
    responsibility = await resp_service.get_responsibility(responsibility_id)
    if not responsibility:
        raise HTTPException(status_code=404, detail="Responsibility not found")

    service = RiskService(session)
    score = service.calculate_risk_score(responsibility)
    return {
        "responsibility_id": responsibility_id,
        "risk_score": score,
        "urgency": responsibility.urgency,
        "impact": responsibility.impact,
        "due_date": responsibility.due_date,
    }
