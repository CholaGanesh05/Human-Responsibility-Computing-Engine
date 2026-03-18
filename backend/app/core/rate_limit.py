"""
HRCE Backend — API Rate Limiter
Redis-backed rate limiting using slowapi.
Protects all endpoints from abuse, with tighter limits on expensive AI calls.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# ─── Global Limiter ───────────────────────────────────────────────────────────
# Uses Redis as the storage backend (already in the stack).
# Falls back to in-memory if Redis URL is not set (local dev safety net).
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.redis_url,
    default_limits=["200/minute"],
    headers_enabled=True,  # Adds X-RateLimit-* headers to responses
)
