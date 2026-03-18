"""
HRCE — RiskResponseAgent
Agent responsible for LLM-based risk analysis of a responsibility.
Separates prompting logic from the service/DB layer.
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq
from app.core.config import settings


_SYSTEM_PROMPT = """\
You are a Risk Assessment Expert for task and responsibility management.

Given a responsibility title and description, you must:
1. Determine the appropriate Urgency level (how time-sensitive this is).
2. Determine the appropriate Impact level (how significant the consequences are if missed).
3. Suggest 3-5 concrete, actionable preparation steps.
4. Provide a brief reasoning for your assessment.

Allowed levels: LOW, MEDIUM, HIGH, CRITICAL.

Output ONLY valid JSON in this exact format — no markdown, no extra text:
{
    "urgency": "LEVEL",
    "impact": "LEVEL",
    "preparation_steps": ["step1", "step2", "step3"],
    "reasoning": "brief explanation"
}
"""

_USER_TEMPLATE = """\
Title: {title}
Description: {description}
"""


class RiskResponseAgent:
    """
    LLM-powered agent that analyzes a responsibility's risk profile.

    Usage:
        agent = RiskResponseAgent()
        result = await agent.analyze(title="Prepare Report", description="Q4 financial report due Friday")
        # result = { "urgency": "HIGH", "impact": "HIGH", "preparation_steps": [...], "reasoning": "..." }
    """

    def __init__(self):
        self.llm = ChatGroq(
            groq_api_key=settings.groq_api_key,
            model_name=settings.groq_model,
            temperature=0.2,  # Low temperature for consistent, structured output
        )
        self._chain = (
            ChatPromptTemplate.from_messages([
                ("system", _SYSTEM_PROMPT),
                ("user", _USER_TEMPLATE),
            ])
            | self.llm
            | JsonOutputParser()
        )

    async def analyze(self, title: str, description: str | None) -> dict:
        """
        Analyzes the given responsibility and returns a risk assessment dict.

        Args:
            title:       The responsibility title.
            description: Optional description text.

        Returns:
            dict with keys: urgency, impact, preparation_steps, reasoning.
            Falls back to safe defaults if the LLM call fails.
        """
        safe_description = description or "No description provided."
        try:
            result = await self._chain.ainvoke({
                "title": title,
                "description": safe_description,
            })
            return result
        except Exception as exc:
            # Return a structured fallback so callers don't crash
            return {
                "urgency": "LOW",
                "impact": "LOW",
                "preparation_steps": [],
                "reasoning": f"AI analysis failed: {exc}",
                "_error": str(exc),
            }
