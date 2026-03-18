"""
HRCE — Stage 12: Docker Integration Smoke Tests
================================================
These tests verify that all containers start up healthy and the key HTTP
endpoints are reachable.

They are SKIPPED in normal pytest runs.  To execute them you must first
bring the stack up with Docker Compose and then set the env variable:

    docker compose up -d
    $env:DOCKER_INTEGRATION = "1"             # PowerShell
    python -m pytest tests/test_docker.py -v

They are intentionally NOT included in `make test` so they never break
local unit-test runs that don't have Docker up.
"""
import os

import httpx
import pytest

# ─── Guard ────────────────────────────────────────────────────────────────────
INTEGRATION = os.environ.get("DOCKER_INTEGRATION", "").strip() == "1"
skip_reason = "Set DOCKER_INTEGRATION=1 and run 'docker compose up -d' to enable"

pytestmark = pytest.mark.skipif(not INTEGRATION, reason=skip_reason)

# ─── Constants ────────────────────────────────────────────────────────────────
BACKEND   = "http://localhost:8000"
AGENT_SVC = "http://localhost:8001"
FRONTEND  = "http://localhost:3000"
TIMEOUT   = 10.0  # seconds per request


# ─── Backend Smoke Tests ──────────────────────────────────────────────────────

def test_backend_health():
    """GET /api/v1/health → status ok."""
    resp = httpx.get(f"{BACKEND}/api/v1/health", timeout=TIMEOUT)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    body = resp.json()
    assert body.get("status") == "ok", f"Unexpected body: {body}"


def test_backend_db_health():
    """GET /api/v1/health/db → PostgreSQL connected."""
    resp = httpx.get(f"{BACKEND}/api/v1/health/db", timeout=TIMEOUT)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    body = resp.json()
    assert body.get("connected") is True, f"DB not connected: {body}"


def test_backend_redis_health():
    """GET /api/v1/health/redis → Redis connected."""
    resp = httpx.get(f"{BACKEND}/api/v1/health/redis", timeout=TIMEOUT)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    body = resp.json()
    assert body.get("connected") is True, f"Redis not connected: {body}"


def test_backend_all_health():
    """GET /api/v1/health/all → aggregate status ok (no degraded services)."""
    resp = httpx.get(f"{BACKEND}/api/v1/health/all", timeout=TIMEOUT)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    body = resp.json()
    assert body.get("status") == "ok", (
        f"One or more services degraded: {body}"
    )


def test_backend_docs_reachable():
    """GET /docs → Swagger UI is served (HTML, not an error)."""
    resp = httpx.get(f"{BACKEND}/docs", timeout=TIMEOUT)
    assert resp.status_code == 200, f"Swagger UI not reachable: {resp.status_code}"
    assert "swagger" in resp.text.lower(), "Response doesn't look like Swagger UI"


# ─── Agent Service Smoke Test ─────────────────────────────────────────────────

def test_agent_service_health():
    """GET agent-service /health → status ok."""
    resp = httpx.get(f"{AGENT_SVC}/health", timeout=TIMEOUT)
    assert resp.status_code == 200, f"Agent service not healthy: {resp.status_code}"
    body = resp.json()
    assert body.get("status") == "ok", f"Unexpected body: {body}"


# ─── Frontend Smoke Test ──────────────────────────────────────────────────────

def test_frontend_root_reachable():
    """GET / on the Next.js frontend → returns HTML (not a 5xx error)."""
    resp = httpx.get(f"{FRONTEND}/", timeout=TIMEOUT, follow_redirects=True)
    assert resp.status_code < 500, (
        f"Frontend returned server error: {resp.status_code}"
    )
    content_type = resp.headers.get("content-type", "")
    assert "text/html" in content_type, (
        f"Expected HTML response, got Content-Type: {content_type}"
    )
