"""
HRCE Agent Service — Responsibility Decomposition Agent
=======================================================
LangGraph state-graph agent that takes an HRCE event and decomposes it
into a structured list of proposed responsibilities using an LLM.

LangGraph flow:
    [START] → fetch_event_node → decompose_node → [END]

Usage:
    agent = DecompositionAgent()
    result = await agent.run(event_id="<uuid>", token="<bearer>")
    # result.responsibilities → list[ResponsibilityProposal]
"""
import json
import os
from typing import Any, Optional, TypedDict

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field

from tools.hrce_tools import fetch_event

# ─── Configuration ────────────────────────────────────────────────────────────
_GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")
_MODEL: str = os.environ.get("GROQ_MODEL", "llama3-8b-8192")

# ─── Output Schema ────────────────────────────────────────────────────────────

class ResponsibilityProposal(BaseModel):
    title: str = Field(description="Short, action-oriented title for the responsibility")
    description: str = Field(description="Clear description of what needs to be done")
    priority: str = Field(description="Priority level: LOW, MEDIUM, HIGH, or CRITICAL")
    estimated_effort_hours: float = Field(description="Rough effort estimate in hours")


class DecompositionResult(BaseModel):
    event_id: str
    event_title: str
    responsibilities: list[ResponsibilityProposal]
    reasoning: str


# ─── LangGraph State ──────────────────────────────────────────────────────────

class DecompositionState(TypedDict):
    event_id: str
    token: Optional[str]
    event: dict[str, Any]
    result: Optional[DecompositionResult]
    error: Optional[str]


# ─── Prompts ──────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are an expert project manager and responsibility analyst for the HRCE platform.

Given an event title and description, decompose it into a list of concrete,
actionable responsibilities that team members must complete to fulfil the event.

Rules:
- Each responsibility should be a specific, well-scoped task
- Prioritize using: LOW, MEDIUM, HIGH, or CRITICAL
- Estimate realistic effort in hours (0.5 – 40)
- Aim for 3–8 responsibilities depending on event complexity
- Output ONLY valid JSON — no markdown, no extra text

Output format:
{
  "responsibilities": [
    {
      "title": "Short action-oriented title",
      "description": "Clear description of what needs doing",
      "priority": "HIGH",
      "estimated_effort_hours": 4.0
    }
  ],
  "reasoning": "Brief explanation of your decomposition approach"
}
"""

_USER_TEMPLATE = """\
Event Title: {title}
Event Description: {description}
"""

# ─── Graph Nodes ──────────────────────────────────────────────────────────────

async def fetch_event_node(state: DecompositionState) -> DecompositionState:
    """Fetch the event from the backend API."""
    try:
        event_data = await fetch_event.ainvoke({
            "event_id": state["event_id"],
            "token": state.get("token"),
        })
        return {**state, "event": event_data}
    except Exception as exc:
        return {**state, "event": {}, "error": f"Failed to fetch event: {exc}"}


async def decompose_node(state: DecompositionState) -> DecompositionState:
    """Call the LLM to decompose the event into responsibilities."""
    if state.get("error"):
        return state

    event = state["event"]
    title = event.get("title", "Unknown Event")
    description = event.get("description") or "No description provided."

    llm = ChatGroq(
        groq_api_key=_GROQ_API_KEY,
        model_name=_MODEL,
        temperature=0.3,
    )
    chain = (
        ChatPromptTemplate.from_messages([
            ("system", _SYSTEM_PROMPT),
            ("user", _USER_TEMPLATE),
        ])
        | llm
        | JsonOutputParser()
    )

    try:
        raw = await chain.ainvoke({"title": title, "description": description})
        proposals = [
            ResponsibilityProposal(**r)
            for r in raw.get("responsibilities", [])
        ]
        result = DecompositionResult(
            event_id=state["event_id"],
            event_title=title,
            responsibilities=proposals,
            reasoning=raw.get("reasoning", ""),
        )
        return {**state, "result": result}
    except Exception as exc:
        # Graceful fallback — return a single placeholder responsibility
        fallback = DecompositionResult(
            event_id=state["event_id"],
            event_title=title,
            responsibilities=[
                ResponsibilityProposal(
                    title="Review and plan event requirements",
                    description="AI decomposition failed — manually review the event and create responsibilities.",
                    priority="MEDIUM",
                    estimated_effort_hours=2.0,
                )
            ],
            reasoning=f"AI decomposition failed: {exc}",
        )
        return {**state, "result": fallback, "error": str(exc)}


# ─── Graph ────────────────────────────────────────────────────────────────────

def _build_graph() -> Any:
    graph = StateGraph(DecompositionState)
    graph.add_node("fetch_event", fetch_event_node)
    graph.add_node("decompose", decompose_node)
    graph.add_edge(START, "fetch_event")
    graph.add_edge("fetch_event", "decompose")
    graph.add_edge("decompose", END)
    return graph.compile()


# ─── Public Agent Class ───────────────────────────────────────────────────────

class DecompositionAgent:
    """
    LangGraph agent that decomposes an HRCE event into responsibility proposals.

    Usage:
        agent = DecompositionAgent()
        result = await agent.run(event_id="<uuid>", token="<bearer>")
    """

    def __init__(self) -> None:
        self._graph = _build_graph()

    async def run(
        self,
        event_id: str,
        token: Optional[str] = None,
    ) -> DecompositionResult:
        initial_state: DecompositionState = {
            "event_id": event_id,
            "token": token,
            "event": {},
            "result": None,
            "error": None,
        }
        final_state = await self._graph.ainvoke(initial_state)
        if final_state["result"] is None:
            raise RuntimeError(
                f"DecompositionAgent failed: {final_state.get('error', 'unknown error')}"
            )
        return final_state["result"]
