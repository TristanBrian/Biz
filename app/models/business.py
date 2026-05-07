# ============================================================
# app/models/business.py
# SQLAlchemy ORM model for the businesses table.
# ============================================================

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Business(Base):
    """
    Represents a single SME business registered on BizSafi.
    One user can own multiple businesses.

    Relationships:
        owner:     The User who registered this business.
        sales:     All sales entries for this business.
        stock:     All stock items for this business.
        reminders: All compliance/operational reminders.
    """

    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign key links this business to its owner
    # ondelete="CASCADE" ensures DB-level deletion when the user is deleted
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Display name of the business (e.g. "Mama Jane's Salon")
    name = Column(String(200), nullable=False)

    # Business category for filtering and AI context (e.g. "salon", "cafe", "retail")
    category = Column(String(100), nullable=False, default="general")

    # Physical or town location (e.g. "Westlands, Nairobi")
    location = Column(String(200), nullable=True)

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

    # --- ORM relationships ---
    owner = relationship("User", back_populates="businesses")

    sales = relationship(
        "Sale",
        back_populates="business",
        cascade="all, delete-orphan",
    )

    stock = relationship(
        "StockItem",
        back_populates="business",
        cascade="all, delete-orphan",
    )

    reminders = relationship(
        "Reminder",
        back_populates="business",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Business id={self.id} name={self.name!r} category={self.category!r}>"
