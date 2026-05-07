# ============================================================
# app/models/stock.py
# SQLAlchemy ORM model for the stock table.
# ============================================================

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class StockItem(Base):
    """
    Represents a single stock-keeping unit (SKU) in a business.
    Tracks quantity, pricing, and a low-stock alert threshold.

    Relationships:
        business: The Business this stock item belongs to.
    """

    __tablename__ = "stock"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign key to the owning business
    business_id = Column(
        Integer,
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Name of the item (e.g. "Shampoo 500ml", "Mandazi dozen")
    item_name = Column(String(200), nullable=False)

    # Current quantity in stock (units / pieces / kg — SME decides the unit)
    quantity = Column(Float, nullable=False, default=0)

    # What the business paid per unit (buying price) in KES
    cost_price = Column(Float, nullable=False, default=0)

    # What the business charges per unit (selling price) in KES
    selling_price = Column(Float, nullable=False, default=0)

    # When quantity drops to or below this number, trigger a low-stock alert
    low_stock_threshold = Column(Float, nullable=False, default=5)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # --- ORM relationship ---
    business = relationship("Business", back_populates="stock")

    @property
    def is_low_stock(self) -> bool:
        """Returns True if current quantity is at or below the alert threshold."""
        return self.quantity <= self.low_stock_threshold

    @property
    def profit_margin(self) -> float:
        """Returns gross profit per unit in KES (selling - cost)."""
        return self.selling_price - self.cost_price

    def __repr__(self) -> str:
        return (
            f"<StockItem id={self.id} item={self.item_name!r} "
            f"qty={self.quantity} low_stock={self.is_low_stock}>"
        )
