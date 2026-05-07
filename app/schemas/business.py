# ============================================================
# app/schemas/business.py
# Pydantic v2 schemas for Business CRUD operations.
# ============================================================

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BusinessCreate(BaseModel):
    """Schema for POST /business — registering a new business."""

    name: str = Field(..., min_length=2, max_length=200, example="Mama Jane's Salon")
    category: str = Field(..., min_length=2, max_length=100, example="salon")
    location: Optional[str] = Field(None, max_length=200, example="Westlands, Nairobi")


class BusinessUpdate(BaseModel):
    """Schema for PATCH /business/{id} — partial updates."""

    name: Optional[str] = Field(None, min_length=2, max_length=200)
    category: Optional[str] = Field(None, min_length=2, max_length=100)
    location: Optional[str] = Field(None, max_length=200)


class BusinessOut(BaseModel):
    """Public representation of a Business returned by the API."""

    id: int
    user_id: int
    name: str
    category: str
    location: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
