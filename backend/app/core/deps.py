"""
HRCE Backend — FastAPI Dependencies (Stage 11)

Provides:
  - get_current_user: Decodes Bearer JWT and loads the User from DB.
    Raises HTTP 401 on any failure so all protected routes stay clean.
"""
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

# OAuth2 scheme — FastAPI auto-extracts "Authorization: Bearer <token>"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency — resolves the currently-authenticated User.

    Flow:
      1. Extract Bearer token from Authorization header.
      2. Decode and validate the JWT.
      3. Load User from DB by the 'sub' claim (user id).
      4. Raise 401 on any failure (bad token, expired, user not found).
    """
    payload = decode_access_token(token)
    if payload is None:
        raise _CREDENTIALS_EXCEPTION

    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise _CREDENTIALS_EXCEPTION

    try:
        user_id = uuid.UUID(user_id_str)
    except (ValueError, AttributeError):
        raise _CREDENTIALS_EXCEPTION

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise _CREDENTIALS_EXCEPTION

    return user
