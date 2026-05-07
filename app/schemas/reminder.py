# ============================================================
# app/schemas/reminder.py
# Pydantic v2 schemas for Compliance & Operational Reminders.
# ============================================================

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

# Mirror the Enum values from the ORM model
ReminderType = Literal["permit", "rent", "stock", "salary", "tax", "other"]
ReminderStatus = Literal["pending", "sent", "done"]


class ReminderCreate(BaseModel):
    """Schema for POST /reminders — creating a new reminder."""

    business_id: int = Field(..., example=1)
    type: ReminderType = Field(..., example="permit")
    message: str = Field(
        ...,
        min_length=5,
        max_length=500,
        example="Business permit renewal due — visit City Hall, fee KES 10,000",
    )
    due_date: date = Field(..., example="2024-07-31")


class ReminderUpdate(BaseModel):
    """Schema for PATCH /reminders/{id} — update message, date, or status."""

    message: Optional[str] = Field(None, min_length=5, max_length=500)
    due_date: Optional[date] = None
    status: Optional[ReminderStatus] = None


class ReminderOut(BaseModel):
    """Public representation of a Reminder, including days_until_due."""

    id: int
    business_id: int
    type: str
    message: str
    due_date: date
    status: str
    days_until_due: int      # Computed property from ORM model
    created_at: datetime

    model_config = {"from_attributes": True}
