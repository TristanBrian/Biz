# ============================================================
# app/models/sales.py
# SQLAlchemy ORM model for the sales table.
# ============================================================

from datetime import date, datetime, timezone

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Sale(Base):
    """
    Records a single sales entry for a business.
    Designed for quick daily logging — just amount, date, optional notes.

    Relationships:
        business: The Business this sale belongs to.
    """

    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign key to the owning business
    business_id = Column(
        Integer,
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Revenue amount in KES (Kenyan Shillings)
    amount = Column(Float, nullable=False)

    # The calendar date this sale occurred — separate from created_at
    # so users can backfill entries for yesterday, last week, etc.
    date = Column(Date, nullable=False, default=date.today)

    # Optional: what was sold, payment method, anything useful
    notes = Column(Text, nullable=True)

    # Timestamp of when the record was created in the system
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
    business = relationship("Business", back_populates="sales")

    def __repr__(self) -> str:
        return f"<Sale id={self.id} business_id={self.business_id} amount={self.amount} date={self.date}>"
