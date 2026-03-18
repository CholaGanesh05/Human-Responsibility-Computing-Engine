"""
HRCE Backend — User Pydantic Schemas (Stage 11)
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


# ─── Request schemas ─────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ─── Response schemas ─────────────────────────────────────────────────────────

class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Token schemas ────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str          # user id as string
    exp: datetime | None = None
