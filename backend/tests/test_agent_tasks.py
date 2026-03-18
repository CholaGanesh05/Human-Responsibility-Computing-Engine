"""
HRCE — Stage 10 Agent Task Tests

All tests call task.__wrapped__(self, *args) to bypass Celery broker.
AI agent calls are intercepted by patching _run_agent (module-level helper).
Import agent_tasks at top-level so patching inside tests works correctly.
"""
import uuid
from unittest.mock import MagicMock, patch

# Import once at module level — required for patch() to work correctly
from app.workers import agent_tasks
from app.models.responsibility import ResponsibilityStatus


# ─── Shared helpers ───────────────────────────────────────────────────────────

def _make_event():
    e = MagicMock()
    e.id = uuid.uuid4()
    e.owner_id = uuid.uuid4()
    e.title = "Board Review"
    e.description = "Q4 meeting"
    return e


def _make_session(get_return=None, scalars_side_effect=None):
    s = MagicMock()
    s.__enter__ = lambda s_: s_
    s.__exit__ = MagicMock(return_value=False)
    if get_return is not None:
        s.get.return_value = get_return
    if scalars_side_effect is not None:
        s.execute.return_value.scalars.return_value.all.side_effect = scalars_side_effect
    else:
        s.execute.return_value.scalars.return_value.all.return_value = []
    return s


# ─── Test 1: decompose_event creates 3 responsibilities from LLM output ───────

def test_decompose_event_creates_responsibilities():
    event = _make_event()
    session = _make_session(get_return=event)  # empty existing responsibilities

    agent_result = {
        "urgency": "HIGH",
        "impact": "HIGH",
        "preparation_steps": ["Step A", "Step B", "Step C"],
        "reasoning": "Thorough prep needed",
    }

    added = []
    session.add.side_effect = lambda r: added.append(r)

    with patch.object(agent_tasks, "_get_sync_session", return_value=session), \
         patch.object(agent_tasks, "_emit_responsibility_ws"), \
         patch.object(agent_tasks, "_run_agent", return_value=agent_result), \
         patch("app.agents.risk_agent.RiskResponseAgent"):
        result = agent_tasks.decompose_event_task.__wrapped__(str(event.id))

    assert result["status"] == "done", f"Expected done, got: {result}"
    assert result["responsibilities_created"] == 3
    assert len(added) == 3
    assert session.commit.called


# ─── Test 2: decompose_event is idempotent ────────────────────────────────────

def test_decompose_event_skips_when_exists():
    event = _make_event()
    session = _make_session(
        get_return=event,
        scalars_side_effect=[[MagicMock()]],  # one existing responsibility
    )

    with patch.object(agent_tasks, "_get_sync_session", return_value=session), \
         patch.object(agent_tasks, "_emit_responsibility_ws"):
        result = agent_tasks.decompose_event_task.__wrapped__(str(event.id))

    assert result["status"] == "skipped"
    assert "already exist" in result["reason"]


# ─── Test 3: process_document expands embedding ───────────────────────────────

def test_process_document_updates_embedding():
    doc = MagicMock()
    doc.id = str(uuid.uuid4())
    doc.content = "X" * 5000
    doc.embedding = None

    session = _make_session(get_return=doc)
    new_embedding = [0.1, 0.2, 0.3]

    with patch.object(agent_tasks, "_get_sync_session", return_value=session), \
         patch("app.services.embedding_service.EmbeddingService") as MockEmbed:
        MockEmbed.generate_embedding.return_value = new_embedding
        result = agent_tasks.process_document_task.__wrapped__(doc.id)

    assert result["status"] == "done"
    assert result["chars_embedded"] == min(8000, 5000)
    assert doc.embedding == new_embedding
    assert session.commit.called


# ─── Test 4: cascade dependency marks downstream responsibilities BLOCKED ──────

def test_cascade_dependency_blocks_downstream():
    blocker_id = uuid.uuid4()
    blocked_id = uuid.uuid4()
    event = _make_event()

    dep = MagicMock()
    dep.blocker_id = blocker_id
    dep.blocked_id = blocked_id

    blocked_resp = MagicMock()
    blocked_resp.id = blocked_id
    blocked_resp.event = event
    blocked_resp.assigned_to_id = event.owner_id
    blocked_resp.status = MagicMock(value="PENDING")

    session = MagicMock()
    session.__enter__ = lambda s: s
    session.__exit__ = MagicMock(return_value=False)
    # 1st execute → deps of blocker [dep]; 2nd execute → leaf (no further deps)
    session.execute.return_value.scalars.return_value.all.side_effect = [[dep], []]
    session.get.return_value = blocked_resp

    with patch.object(agent_tasks, "_get_sync_session", return_value=session), \
         patch.object(agent_tasks, "_emit_responsibility_ws"):
        result = agent_tasks.cascade_dependency_update_task.__wrapped__(str(blocker_id))

    assert result["status"] == "done"
    assert blocked_resp.status == ResponsibilityStatus.BLOCKED
    assert session.commit.called
