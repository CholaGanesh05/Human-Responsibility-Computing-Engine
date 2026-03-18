"""
HRCE Backend — FastAPI Application Entry Point
Includes lifespan context manager for DB + Redis startup/shutdown.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.router import api_router
from app.api.ws.ws_router import ws_router
from app.core.config import settings
from app.core.database import connect_db, disconnect_db
from app.core.logging import logger, setup_logging
from app.core.rate_limit import limiter
from app.core.redis_client import connect_redis, disconnect_redis

# ─── Logging ──────────────────────────────────────────────────
setup_logging("DEBUG" if settings.debug else "INFO")


# ─── Lifespan ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle for all infrastructure connections."""
    logger.info("🚀 HRCE Backend starting up...")
    await connect_db()
    await connect_redis()
    logger.info("✅ All connections established. Ready to serve.")
    yield
    logger.info("🛑 HRCE Backend shutting down...")
    await disconnect_db()
    await disconnect_redis()
    logger.info("✅ All connections closed.")


# ─── App ──────────────────────────────────────────────────────
app = FastAPI(
    title="HRCE — Human Responsibility Computing Engine",
    description="Agentic AI-Powered Responsibility Management Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── Rate Limiting ────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ─── CORS ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────
app.include_router(api_router)
app.include_router(ws_router)  # WebSocket live push (/ws/{user_id})


# ─── Root ─────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "HRCE — Human Responsibility Computing Engine",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health/all",
    }


@app.get("/ping", tags=["Root"])
async def ping():
    return {"ping": "pong"}
