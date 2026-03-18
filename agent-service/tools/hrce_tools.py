"""
HRCE Agent Service — Shared HRCE Tools
=======================================
LangChain @tool-decorated functions that call the backend REST API via httpx.
These give LangGraph agents access to live HRCE data without a direct DB connection.

Configuration:
    BACKEND_URL  — base URL of the backend API (default: http://localhost:8000)
    AGENT_TOKEN  — Bearer token forwarded to the backend (set at request time)
"""
import os
from typing import Optional

import httpx
from langchain_core.tools import tool

# ─── Base URL ─────────────────────────────────────────────────────────────────
_BACKEND_URL: str = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")
_TIMEOUT: float = 10.0


def _headers(token: Optional[str] = None) -> dict[str, str]:
    """Build request headers, optionally including a Bearer token."""
    h: dict[str, str] = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


# ─── Tools ────────────────────────────────────────────────────────────────────

@tool
async def fetch_event(event_id: str, token: Optional[str] = None) -> dict:
    """
    Fetch a single HRCE event by its UUID.

    Args:
        event_id: UUID string of the event.
        token:    Optional Bearer token for auth (forwarded to backend).

    Returns:
        Event dict with keys: id, title, description, start_time, end_time,
        owner_id, status, created_at.
    """
    async with httpx.AsyncClient(base_url=_BACKEND_URL, timeout=_TIMEOUT) as client:
        resp = await client.get(
            f"/api/v1/events/{event_id}",
            headers=_headers(token),
        )
        resp.raise_for_status()
        return resp.json()


@tool
async def fetch_responsibilities(event_id: str, token: Optional[str] = None) -> list[dict]:
    """
    Fetch all responsibilities belonging to a given event.

    Args:
        event_id: UUID string of the parent event.
        token:    Optional Bearer token for auth.

    Returns:
        List of responsibility dicts with keys: id, title, description,
        priority, status, estimated_effort_hours, due_date.
    """
    async with httpx.AsyncClient(base_url=_BACKEND_URL, timeout=_TIMEOUT) as client:
        resp = await client.get(
            "/api/v1/responsibilities/",
            params={"event_id": event_id, "limit": 50},
            headers=_headers(token),
        )
        resp.raise_for_status()
        data = resp.json()
        # Handle both list and paginated {"items": [...]} responses
        if isinstance(data, list):
            return data
        return data.get("items", data)


@tool
async def fetch_documents(event_id: str, token: Optional[str] = None) -> list[dict]:
    """
    Fetch all documents attached to a given event.

    Args:
        event_id: UUID string of the parent event.
        token:    Optional Bearer token for auth.

    Returns:
        List of document dicts with keys: id, filename, content, content_type,
        created_at.
    """
    async with httpx.AsyncClient(base_url=_BACKEND_URL, timeout=_TIMEOUT) as client:
        resp = await client.get(
            "/api/v1/documents/",
            params={"event_id": event_id, "limit": 20},
            headers=_headers(token),
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data
        return data.get("items", data)
