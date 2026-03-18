"""
HRCE Backend — API v1 Router
Aggregates all v1 endpoint routers.
"""
from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.endpoints.auth import router as auth_router                          # Stage 11
from app.api.endpoints.documents import router as documents_router
from app.api.endpoints.rag import router as rag_router
from app.api.endpoints.risk import router as risk_router
from app.api.endpoints.notifications import router as notifications_router
from app.api.endpoints.events import router as events_router                      # Stage 10
from app.api.endpoints.responsibilities import router as responsibilities_router  # Stage 10

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router, tags=["Health"])
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])             # Stage 11
api_router.include_router(documents_router, prefix="/documents", tags=["Documents"])
api_router.include_router(rag_router, prefix="/rag", tags=["RAG"])
api_router.include_router(risk_router, prefix="/risk", tags=["Risk"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(events_router, prefix="/events", tags=["Events"])                          # Stage 10
api_router.include_router(responsibilities_router, prefix="/responsibilities", tags=["Responsibilities"])  # Stage 10
