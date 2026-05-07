# ============================================================
# app/schemas/user.py
# Pydantic v2 schemas for User request/response validation.
# These are NOT the ORM models — they control what the API
# accepts as input and what it returns as output.
# ============================================================

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


# ------------------------------------------------------------
# Request schemas (what the client sends)
# ------------------------------------------------------------

class UserCreate(BaseModel):
    """Schema for POST /auth/register — creating a new user."""

    name: str = Field(..., min_length=2, max_length=150, example="Jane Wanjiku")
    email: EmailStr = Field(..., example="jane@bizsafi.co.ke")
    password: str = Field(..., min_length=8, example="Secure@123")
    role: Literal["SME", "ADMIN"] = Field(default="SME")


class UserLogin(BaseModel):
    """Schema for POST /auth/login — email + password credentials."""

    email: EmailStr = Field(..., example="jane@bizsafi.co.ke")
    password: str = Field(..., example="Secure@123")


# ------------------------------------------------------------
# Response schemas (what the API returns)
# ------------------------------------------------------------

class UserOut(BaseModel):
    """
    Safe public representation of a User.
    password_hash is deliberately excluded.
    """

    id: int
    name: str
    email: EmailStr
    role: str
    created_at: datetime

    # model_config tells pydantic to read attributes from ORM objects
    # (replaces orm_mode = True from pydantic v1)
    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    """Response from /auth/login — JWT bearer token."""

    access_token: str
    token_type: str = "bearer"
    user: UserOut
