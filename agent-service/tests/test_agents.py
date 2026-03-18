"""
HRCE Agent Service — Unit Tests
================================
These tests verify the node logic and agent structure.

Running locally (uses backend venv — no langgraph):
    pytest tests/test_agents.py -v
    → All tests SKIPPED (AGENT_SERVICE_TESTS not set)

Running inside the agent-service Docker container (has all deps):
    AGENT_SERVICE_TESTS=1 pytest tests/ -v

Or locally after installing deps:
    pip install -r requirements.txt
    AGENT_SERVICE_TESTS=1 pytest tests/ -v
"""
import os
import sys

import pytest
from unittest.mock import AsyncMock, patch

# ─── Guard — skip unless agent-service deps are available ─────────────────────
ENABLED = os.environ.get("AGENT_SERVICE_TESTS", "").strip() == "1"
skip_reason = (
    "Set AGENT_SERVICE_TESTS=1 and ensure agent-service deps are installed "
    "(run: pip install -r requirements.txt)"
)
pytestmark = pytest.mark.skipif(not ENABLED, reason=skip_reason)

# Ensure the agent-service root is on sys.path so `agents` and `tools` are importable
if ENABLED:
    _root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if _root not in sys.path:
        sys.path.insert(0, _root)


# ─── DecompositionAgent Tests ─────────────────────────────────────────────────

class TestDecompositionAgent:

    @pytest.mark.asyncio
    async def test_fetch_event_success(self):
        """fetch_event_node correctly stores event data in state."""
        from agents.decomposition_agent import fetch_event_node

        mock_event = {
            "id": "evt-001",
            "title": "Q4 Financial Audit",
            "description": "Complete the end-of-year financial audit.",
        }
        with patch("tools.hrce_tools.fetch_event.ainvoke", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_event
            state = {
                "event_id": "evt-001",
                "token": "test-token",
                "event": {},
                "result": None,
                "error": None,
            }
            result = await fetch_event_node(state)
            assert result["event"]["title"] == "Q4 Financial Audit"
            assert result["error"] is None

    @pytest.mark.asyncio
    async def test_fetch_event_failure_sets_error(self):
        """When backend call fails, error is recorded in state."""
        from agents.decomposition_agent import fetch_event_node

        with patch("tools.hrce_tools.fetch_event.ainvoke", side_effect=Exception("Connection refused")):
            state = {
                "event_id": "bad-id",
                "token": None,
                "event": {},
                "result": None,
                "error": None,
            }
            result = await fetch_event_node(state)
            assert result["error"] is not None
            assert "Failed to fetch event" in result["error"]
            assert result["event"] == {}

    @pytest.mark.asyncio
    async def test_decompose_node_skips_on_error(self):
        """decompose_node passes through unchanged when upstream error is set."""
        from agents.decomposition_agent import decompose_node

        state = {
            "event_id": "ev-001",
            "token": None,
            "event": {},
            "result": None,
            "error": "upstream fetch error",
        }
        result = await decompose_node(state)
        # No result produced when there is a pre-existing error
        assert result["result"] is None
        assert result["error"] == "upstream fetch error"


# ─── ContextSummaryAgent Tests ────────────────────────────────────────────────

class TestContextSummaryAgent:

    @pytest.mark.asyncio
    async def test_empty_documents_returns_graceful_result(self):
        """When no documents exist, summarize_node returns a polite no-docs message."""
        from agents.context_agent import summarize_node

        state = {
            "event_id": "ev-002",
            "token": None,
            "documents": [],
            "result": None,
            "error": None,
        }
        result = await summarize_node(state)
        assert result["result"] is not None
        assert result["result"].document_count == 0
        assert "No documents" in result["result"].summary

    @pytest.mark.asyncio
    async def test_fetch_docs_failure_sets_error(self):
        """When backend call fails, error is recorded in state."""
        from agents.context_agent import fetch_docs_node

        with patch("tools.hrce_tools.fetch_documents.ainvoke", side_effect=Exception("timeout")):
            state = {
                "event_id": "ev-003",
                "token": None,
                "documents": [],
                "result": None,
                "error": None,
            }
            result = await fetch_docs_node(state)
            assert result["error"] is not None
            assert "Failed to fetch documents" in result["error"]

    @pytest.mark.asyncio
    async def test_fetch_docs_happy_path(self):
        """Documents fetched from backend are stored in state."""
        from agents.context_agent import fetch_docs_node

        mock_docs = [
            {"id": "doc-1", "filename": "report.pdf", "content": "Annual report content..."},
            {"id": "doc-2", "filename": "budget.xlsx", "content": "Budget figures..."},
        ]
        with patch("tools.hrce_tools.fetch_documents.ainvoke", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_docs
            state = {
                "event_id": "ev-004",
                "token": "bearer-xyz",
                "documents": [],
                "result": None,
                "error": None,
            }
            result = await fetch_docs_node(state)
            assert len(result["documents"]) == 2
            assert result["error"] is None
