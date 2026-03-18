"""
HRCE Agent Service — Context Summary Agent
==========================================
LangGraph state-graph agent that fetches documents attached to an HRCE event
and summarises them into a concise brief with key actionable points.

LangGraph flow:
    [START] → fetch_docs_node → summarize_node → [END]

Usage:
    agent = ContextSummaryAgent()
    result = await agent.run(event_id="<uuid>", token="<bearer>")
    # result.summary   → str
    # result.key_points → list[str]
"""
import os
from typing import Any, Optional, TypedDict

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field

from tools.hrce_tools import fetch_documents

# ─── Configuration ────────────────────────────────────────────────────────────
_GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")
_MODEL: str = os.environ.get("GROQ_MODEL", "llama3-8b-8192")

# ─── Output Schema ────────────────────────────────────────────────────────────

class ContextSummaryResult(BaseModel):
    event_id: str
    document_count: int
    summary: str = Field(description="Concise narrative summary of all documents")
    key_points: list[str] = Field(description="3–7 actionable key points extracted from the documents")


# ─── LangGraph State ──────────────────────────────────────────────────────────

class ContextState(TypedDict):
    event_id: str
    token: Optional[str]
    documents: list[dict[str, Any]]
    result: Optional[ContextSummaryResult]
    error: Optional[str]


# ─── Prompts ──────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are an intelligent document analyst for the HRCE responsibility management platform.

You will be given the content of multiple documents related to an event.
Your job is to:
1. Write a concise 2–4 sentence narrative summary that captures the main theme.
2. Extract 3–7 concrete, actionable key points that stakeholders must act on.

Output ONLY valid JSON — no markdown, no extra text:
{
  "summary": "Concise narrative summary here.",
  "key_points": [
    "Actionable point 1",
    "Actionable point 2"
  ]
}
"""

_USER_TEMPLATE = """\
Documents ({doc_count} total):

{doc_content}
"""

# ─── Graph Nodes ──────────────────────────────────────────────────────────────

async def fetch_docs_node(state: ContextState) -> ContextState:
    """Fetch all documents for the event from the backend API."""
    try:
        docs = await fetch_documents.ainvoke({
            "event_id": state["event_id"],
            "token": state.get("token"),
        })
        return {**state, "documents": docs}
    except Exception as exc:
        return {**state, "documents": [], "error": f"Failed to fetch documents: {exc}"}


async def summarize_node(state: ContextState) -> ContextState:
    """Summarise the fetched documents using the LLM."""
    documents = state["documents"]

    if not documents:
        # No documents — return a graceful empty result
        result = ContextSummaryResult(
            event_id=state["event_id"],
            document_count=0,
            summary="No documents are currently attached to this event.",
            key_points=["Attach relevant documents to generate an AI-powered context summary."],
        )
        return {**state, "result": result}

    # Build document content string
    doc_parts: list[str] = []
    for i, doc in enumerate(documents, 1):
        filename = doc.get("filename", f"Document {i}")
        content = doc.get("content", "").strip()
        if content:
            doc_parts.append(f"--- {filename} ---\n{content}")

    doc_content = "\n\n".join(doc_parts) if doc_parts else "Documents have no extractable text content."

    llm = ChatGroq(
        groq_api_key=_GROQ_API_KEY,
        model_name=_MODEL,
        temperature=0.2,
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
        raw = await chain.ainvoke({
            "doc_count": len(documents),
            "doc_content": doc_content,
        })
        result = ContextSummaryResult(
            event_id=state["event_id"],
            document_count=len(documents),
            summary=raw.get("summary", "Summary unavailable."),
            key_points=raw.get("key_points", []),
        )
        return {**state, "result": result}
    except Exception as exc:
        # Graceful fallback
        result = ContextSummaryResult(
            event_id=state["event_id"],
            document_count=len(documents),
            summary=f"AI summarisation failed. {len(documents)} document(s) are attached — please review them manually.",
            key_points=[],
        )
        return {**state, "result": result, "error": str(exc)}


# ─── Graph ────────────────────────────────────────────────────────────────────

def _build_graph() -> Any:
    graph = StateGraph(ContextState)
    graph.add_node("fetch_docs", fetch_docs_node)
    graph.add_node("summarize", summarize_node)
    graph.add_edge(START, "fetch_docs")
    graph.add_edge("fetch_docs", "summarize")
    graph.add_edge("summarize", END)
    return graph.compile()


# ─── Public Agent Class ───────────────────────────────────────────────────────

class ContextSummaryAgent:
    """
    LangGraph agent that fetches documents for an HRCE event and summarises them.

    Usage:
        agent = ContextSummaryAgent()
        result = await agent.run(event_id="<uuid>", token="<bearer>")
    """

    def __init__(self) -> None:
        self._graph = _build_graph()

    async def run(
        self,
        event_id: str,
        token: Optional[str] = None,
    ) -> ContextSummaryResult:
        initial_state: ContextState = {
            "event_id": event_id,
            "token": token,
            "documents": [],
            "result": None,
            "error": None,
        }
        final_state = await self._graph.ainvoke(initial_state)
        if final_state["result"] is None:
            raise RuntimeError(
                f"ContextSummaryAgent failed: {final_state.get('error', 'unknown error')}"
            )
        return final_state["result"]
