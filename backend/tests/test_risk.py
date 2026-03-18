"""
tests/test_risk.py — Unit tests for Stage 6: Risk & Preparation Intelligence

Tests cover:
  1. Heuristic risk score calculation (no DB, no LLM)
  2. AI analysis happy path (mocked DB + mocked agent)
  3. AI analysis when responsibility is not found
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from uuid import uuid4

from app.models.responsibility import (
    Responsibility,
    UrgencyLevel,
    ImpactLevel,
    PreparationStatus,
    ResponsibilityStatus,
    ComplexityLevel,
)
from app.services.risk_service import RiskService


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def make_responsibility(**kwargs) -> Responsibility:
    """Create a minimal Responsibility ORM object for testing."""
    defaults = dict(
        id=uuid4(),
        title="Test Task",
        description="A test responsibility",
        status=ResponsibilityStatus.PENDING,
        priority=0,
        due_date=None,
        effort_score=3,
        complexity_level=ComplexityLevel.LOW,
        urgency=UrgencyLevel.LOW,
        impact=ImpactLevel.LOW,
        preparation_status=PreparationStatus.NOT_STARTED,
        event_id=uuid4(),
        parent_id=None,
        assigned_to_id=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    obj = MagicMock(spec=Responsibility)
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


# ──────────────────────────────────────────────────────────────────────────────
# Test 1: Heuristic score — no DB, no LLM
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_calculate_risk_score_high_high_no_due_date():
    """
    urgency=HIGH (3), impact=HIGH (3) → base = 9/16 * 80 = 45.
    No due date → no time bonus → score should be 45.
    """
    mock_session = AsyncMock()

    with patch("app.services.risk_service.RiskResponseAgent"):
        service = RiskService(mock_session)

    responsibility = make_responsibility(
        urgency=UrgencyLevel.HIGH,
        impact=ImpactLevel.HIGH,
        due_date=None,
    )

    score = service.calculate_risk_score(responsibility)
    assert score == 45, f"Expected 45, got {score}"


@pytest.mark.asyncio
async def test_calculate_risk_score_critical_critical_overdue():
    """
    urgency=CRITICAL (4), impact=CRITICAL (4) → base = 16/16 * 80 = 80.
    Due date is in the past (overdue) → +20 → score should be capped at 100.
    """
    mock_session = AsyncMock()

    with patch("app.services.risk_service.RiskResponseAgent"):
        service = RiskService(mock_session)

    from datetime import timedelta
    overdue = datetime.now(timezone.utc) - timedelta(days=1)

    responsibility = make_responsibility(
        urgency=UrgencyLevel.CRITICAL,
        impact=ImpactLevel.CRITICAL,
        due_date=overdue,
    )

    score = service.calculate_risk_score(responsibility)
    assert score == 100, f"Expected 100 (capped), got {score}"


# ──────────────────────────────────────────────────────────────────────────────
# Test 2: AI analysis happy path
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analyze_responsibility_ai_success():
    """
    AI agent returns HIGH urgency & impact.
    Service should update responsibility fields and return the correct risk score.
    """
    mock_session = AsyncMock()
    responsibility_id = uuid4()

    responsibility = make_responsibility(
        id=responsibility_id,
        title="Prepare Q4 Report",
        description="Must complete before board meeting.",
        urgency=UrgencyLevel.LOW,
        impact=ImpactLevel.LOW,
    )

    agent_result = {
        "urgency": "HIGH",
        "impact": "HIGH",
        "preparation_steps": ["Gather data", "Draft slides", "Review with manager"],
        "reasoning": "Board meeting is critical and time is short.",
    }

    with patch("app.services.risk_service.RiskResponseAgent") as MockAgent, \
         patch("app.services.risk_service.ResponsibilityService") as MockRespService:

        # Mock agent
        mock_agent_instance = MockAgent.return_value
        mock_agent_instance.analyze = AsyncMock(return_value=agent_result)

        # Mock responsibility service
        mock_resp_service_instance = MockRespService.return_value
        mock_resp_service_instance.get_responsibility = AsyncMock(return_value=responsibility)

        # Mock session methods
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        service = RiskService(mock_session)
        result = await service.analyze_responsibility_ai(responsibility_id)

    assert "risk_score" in result
    assert "analysis" in result
    assert result["analysis"]["urgency"] == "HIGH"
    assert result["analysis"]["impact"] == "HIGH"
    assert len(result["analysis"]["preparation_steps"]) == 3

    # Verify DB write was called
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()


# ──────────────────────────────────────────────────────────────────────────────
# Test 3: Responsibility not found
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analyze_responsibility_not_found():
    """
    If the responsibility doesn't exist, a ValueError should be raised.
    """
    mock_session = AsyncMock()

    with patch("app.services.risk_service.RiskResponseAgent"), \
         patch("app.services.risk_service.ResponsibilityService") as MockRespService:

        mock_resp_service_instance = MockRespService.return_value
        mock_resp_service_instance.get_responsibility = AsyncMock(return_value=None)

        service = RiskService(mock_session)

        with pytest.raises(ValueError, match="Responsibility not found"):
            await service.analyze_responsibility_ai(uuid4())
