"""
HRCE Agent Service — Entry Point
=================================
LangChain / LangGraph orchestration service.
Provides AI-powered agents that augment the core HRCE backend.

Endpoints:
    GET  /health                → service health check
    GET  /ping                  → liveness probe
    POST /agents/decompose      → DecompositionAgent (event → responsibilities)
    POST /agents/summarize      → ContextSummaryAgent (documents → summary)
"""
import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, status
from pydantic import BaseModel

from agents.decomposition_agent import DecompositionAgent, DecompositionResult
from agents.context_agent import ContextSummaryAgent, ContextSummaryResult

# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="HRCE — Agent Service",
    description="LangChain/LangGraph Agentic Orchestration Layer",
    version="0.2.0",
)

# ─── Singleton agents (builds LangGraph graphs once at startup) ───────────────
_decomposition_agent = DecompositionAgent()
_context_agent = ContextSummaryAgent()


# ─── Request / Response Schemas ───────────────────────────────────────────────

class AgentRequest(BaseModel):
    event_id: str


# ─── System Routes ────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "service": "hrce-agent-service", "version": "0.2.0"}


@app.get("/ping", tags=["System"])
async def ping():
    return {"ping": "pong"}


# ─── Agent Routes ─────────────────────────────────────────────────────────────

@app.post(
    "/agents/decompose",
    response_model=DecompositionResult,
    tags=["Agents"],
    summary="Decompose an event into responsibility proposals",
    description=(
        "Runs the ResponsibilityDecompositionAgent on the given event. "
        "Fetches the event from the backend, then uses an LLM to propose "
        "a structured list of responsibilities the event should generate. "
        "Optionally forward the user's Bearer token so backend calls are "
        "authenticated."
    ),
)
async def decompose_event(
    body: AgentRequest,
    authorization: Optional[str] = Header(default=None),
) -> DecompositionResult:
    """
    POST /agents/decompose
    Body: { "event_id": "<uuid>" }
    Header: Authorization: Bearer <token>  (optional but recommended)
    """
    # Extract raw token from "Bearer <token>" header
    token: Optional[str] = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:]

    try:
        result = await _decomposition_agent.run(event_id=body.event_id, token=token)
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"DecompositionAgent failed: {exc}",
        ) from exc


@app.post(
    "/agents/summarize",
    response_model=ContextSummaryResult,
    tags=["Agents"],
    summary="Summarise documents attached to an event",
    description=(
        "Runs the ContextSummaryAgent on the given event. "
        "Fetches all attached documents from the backend, then uses an LLM to "
        "produce a concise narrative summary and a list of key actionable points. "
        "Returns a graceful response even when no documents are attached."
    ),
)
async def summarize_event(
    body: AgentRequest,
    authorization: Optional[str] = Header(default=None),
) -> ContextSummaryResult:
    """
    POST /agents/summarize
    Body: { "event_id": "<uuid>" }
    Header: Authorization: Bearer <token>  (optional but recommended)
    """
    token: Optional[str] = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:]

    try:
        result = await _context_agent.run(event_id=body.event_id, token=token)
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"ContextSummaryAgent failed: {exc}",
        ) from exc
