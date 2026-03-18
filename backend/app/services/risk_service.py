"""
HRCE — RiskService
Handles risk score calculation and AI-based risk analysis of responsibilities.
Delegates LLM prompting to RiskResponseAgent.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.responsibility import Responsibility, UrgencyLevel, ImpactLevel, PreparationStatus
from app.services.responsibility_service import ResponsibilityService
from app.agents.risk_agent import RiskResponseAgent
from datetime import datetime
import uuid


class RiskService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.resp_service = ResponsibilityService(session)
        self.agent = RiskResponseAgent()

    # ──────────────────────────────────────────────────────────────
    # Heuristic Score (no LLM)
    # ──────────────────────────────────────────────────────────────

    def calculate_risk_score(self, responsibility: Responsibility) -> int:
        """
        Calculates a heuristic risk score (0-100) based on Urgency, Impact,
        and time remaining until the due date.
        """
        urgency_map = {
            UrgencyLevel.LOW: 1, UrgencyLevel.MEDIUM: 2,
            UrgencyLevel.HIGH: 3, UrgencyLevel.CRITICAL: 4
        }
        impact_map = {
            ImpactLevel.LOW: 1, ImpactLevel.MEDIUM: 2,
            ImpactLevel.HIGH: 3, ImpactLevel.CRITICAL: 4
        }

        u_score = urgency_map.get(responsibility.urgency, 1)
        i_score = impact_map.get(responsibility.impact, 1)

        # Base score: urgency × impact, max = 16 → scaled to 80
        normalized_score = (u_score * i_score / 16) * 80

        # Time pressure bonus: up to +20 points
        if responsibility.due_date:
            delta = responsibility.due_date - datetime.now(responsibility.due_date.tzinfo)
            days_left = delta.days
            if days_left < 1:
                normalized_score += 20
            elif days_left < 3:
                normalized_score += 10
            elif days_left < 7:
                normalized_score += 5

        return min(int(normalized_score), 100)

    # ──────────────────────────────────────────────────────────────
    # AI Analysis (via RiskResponseAgent)
    # ──────────────────────────────────────────────────────────────

    async def analyze_responsibility_ai(self, responsibility_id: uuid.UUID) -> dict:
        """
        Uses RiskResponseAgent to assess urgency/impact and suggest prep steps.
        Updates the Responsibility record in the database.

        Returns:
            {
                "risk_score": int,
                "analysis": {
                    "urgency": str,
                    "impact": str,
                    "preparation_steps": list[str],
                    "reasoning": str
                }
            }

        Raises:
            ValueError: if the responsibility is not found.
        """
        responsibility = await self.resp_service.get_responsibility(responsibility_id)
        if not responsibility:
            raise ValueError("Responsibility not found")

        # Delegate LLM call to the agent
        result = await self.agent.analyze(
            title=responsibility.title,
            description=responsibility.description,
        )

        # If agent returned a hard error, surface it without touching the DB
        if "_error" in result and not result.get("urgency"):
            return {"error": result["_error"]}

        # Map string values back to enums
        urgency_enum = UrgencyLevel(result.get("urgency", "LOW").upper())
        impact_enum = ImpactLevel(result.get("impact", "LOW").upper())

        # Persist urgency + impact
        responsibility.urgency = urgency_enum
        responsibility.impact = impact_enum

        # Append AI-suggested prep steps to the description (idempotent)
        prep_steps = result.get("preparation_steps", [])
        if prep_steps:
            prep_text = "\n\n[AI Suggested Prep]:\n" + "\n".join(f"- {s}" for s in prep_steps)
            if responsibility.description:
                if "[AI Suggested Prep]" not in responsibility.description:
                    responsibility.description += prep_text
            else:
                responsibility.description = prep_text

        self.session.add(responsibility)
        await self.session.commit()
        await self.session.refresh(responsibility)

        return {
            "risk_score": self.calculate_risk_score(responsibility),
            "analysis": result,
        }
