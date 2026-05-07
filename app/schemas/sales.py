from datetime import date as date_type
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SaleCreate(BaseModel):
    """Schema for POST /sales — logging a new sale entry."""

    business_id: int = Field(..., example=1)
    amount: float = Field(..., gt=0, example=3500.00, description="Amount in KES, must be > 0")
    date: date_type = Field(default_factory=date_type.today, example="2024-06-15")
    notes: Optional[str] = Field(None, max_length=500, example="Cash sales, afternoon rush")

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Sale amount must be greater than zero")
        return round(v, 2)


class SaleOut(BaseModel):
    """Public representation of a Sale record."""

    id: int
    business_id: int
    amount: float
    date: date_type
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class SaleSummary(BaseModel):
    """Aggregated sales summary returned by the dashboard endpoint."""

    total_sales: float
    total_entries: int
    period: str
