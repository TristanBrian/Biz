# ============================================================
# app/schemas/stock.py
# Pydantic v2 schemas for Stock item CRUD and alerts.
# ============================================================

from typing import Optional

from pydantic import BaseModel, Field


class StockItemCreate(BaseModel):
    """Schema for POST /stock — adding a new stock item."""

    business_id: int = Field(..., example=1)
    item_name: str = Field(..., min_length=1, max_length=200, example="Shampoo 500ml")
    quantity: float = Field(..., ge=0, example=50)
    cost_price: float = Field(..., ge=0, example=180.00)
    selling_price: float = Field(..., ge=0, example=250.00)
    low_stock_threshold: float = Field(default=5, ge=0, example=10)


class StockItemUpdate(BaseModel):
    """Schema for PATCH /stock/{id} — partial updates (e.g. restocking)."""

    item_name: Optional[str] = Field(None, min_length=1, max_length=200)
    quantity: Optional[float] = Field(None, ge=0)
    cost_price: Optional[float] = Field(None, ge=0)
    selling_price: Optional[float] = Field(None, ge=0)
    low_stock_threshold: Optional[float] = Field(None, ge=0)


class StockItemOut(BaseModel):
    """Public representation of a StockItem, including computed fields."""

    id: int
    business_id: int
    item_name: str
    quantity: float
    cost_price: float
    selling_price: float
    low_stock_threshold: float
    is_low_stock: bool       # Computed property from ORM model
    profit_margin: float     # Computed property from ORM model

    model_config = {"from_attributes": True}
