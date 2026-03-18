"""
HRCE Backend — API v1 Health Router
Provides system health check endpoints for all infrastructure components.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis_client import get_redis

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health():
    """Overall service health check."""
    return {
        "status": "ok",
        "service": "hrce-backend",
        "version": "0.1.0",
    }


@router.get("/db")
async def health_db(db: AsyncSession = Depends(get_db)):
    """
    PostgreSQL connectivity check.
    Runs a lightweight SELECT 1 query to verify the DB is reachable.
    """
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        return {"status": "ok", "database": "postgresql", "connected": True}
    except Exception as e:
        return {"status": "error", "database": "postgresql", "connected": False, "detail": str(e)}


@router.get("/redis")
async def health_redis():
    """
    Redis connectivity check.
    Sends a PING command and expects PONG.
    """
    try:
        redis = get_redis()
        pong = await redis.ping()
        return {"status": "ok", "cache": "redis", "connected": bool(pong)}
    except Exception as e:
        return {"status": "error", "cache": "redis", "connected": False, "detail": str(e)}


@router.get("/all")
async def health_all(db: AsyncSession = Depends(get_db)):
    """Aggregate health check — all infrastructure components."""
    results = {}

    # PostgreSQL
    try:
        await db.execute(text("SELECT 1"))
        results["postgresql"] = {"status": "ok", "connected": True}
    except Exception as e:
        results["postgresql"] = {"status": "error", "connected": False, "detail": str(e)}

    # Redis
    try:
        redis = get_redis()
        pong = await redis.ping()
        results["redis"] = {"status": "ok", "connected": bool(pong)}
    except Exception as e:
        results["redis"] = {"status": "error", "connected": False, "detail": str(e)}

    overall = "ok" if all(v["status"] == "ok" for v in results.values()) else "degraded"
    return {"status": overall, "services": results}
