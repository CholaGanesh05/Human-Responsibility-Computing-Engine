"""
HRCE Backend — Auth Endpoints (Stage 11)

Routes:
  POST /api/v1/auth/register  — create account, return JWT
  POST /api/v1/auth/login     — verify credentials, return JWT
  GET  /api/v1/auth/me        — return current user profile
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserLogin, UserRead

router = APIRouter()


# ─── Register ────────────────────────────────────────────────────────────────

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register(
    request: Request,
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Create a new user account and return a JWT access token.
    Raises 409 if the email already exists.
    """
    # Check for duplicate email
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=token)


# ─── Login ───────────────────────────────────────────────────────────────────

@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Authenticate with email + password.
    Returns a JWT on success; raises 401 on invalid credentials.
    """
    result = await db.execute(select(User).where(User.email == credentials.email))
    user: User | None = result.scalar_one_or_none()

    if user is None or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )

    token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=token)


# ─── Me ──────────────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserRead)
@limiter.limit("60/minute")
async def me(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> UserRead:
    """Return the profile of the currently-authenticated user."""
    return current_user
