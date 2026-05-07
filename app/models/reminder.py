# ============================================================
# app/models/reminder.py
# SQLAlchemy ORM model for the reminders table.
# Covers both compliance reminders (permits, licences) and
# operational ones (rent, salaries, stock reorder).
# ============================================================

from datetime import date, datetime, timezone

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base

# Allowed reminder categories — enforced at the DB level
REMINDER_TYPES = ("permit", "rent", "stock", "salary", "tax", "other")

# Lifecycle of a reminder
REMINDER_STATUSES = ("pending", "sent", "done")


class Reminder(Base):
    """
    A scheduled reminder for a business event or compliance deadline.

    Lifecycle:
        pending → (cron sends SMS) → sent → (user marks complete) → done

    Relationships:
        business: The Business this reminder belongs to.
    """

    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign key to the owning business
    business_id = Column(
        Integer,
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # What kind of reminder this is (permit renewal, rent payment, etc.)
    type = Column(
        Enum(*REMINDER_TYPES, name="reminder_type"),
        nullable=False,
        default="other",
    )

    # Human-readable message that will be sent via SMS
    # e.g. "Business permit renewal due — visit City Hall, fee KES 10,000"
    message = Column(Text, nullable=False)

    # The deadline date — cron job fires when due_date - today <= 3 days
    due_date = Column(Date, nullable=False)

    # Current lifecycle state
    status = Column(
        Enum(*REMINDER_STATUSES, name="reminder_status"),
        nullable=False,
        default="pending",
    )

    # When the reminder record was created
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
    business = relationship("Business", back_populates="reminders")

    @property
    def days_until_due(self) -> int:
        """Returns how many days remain until the due date."""
        return (self.due_date - date.today()).days

    def __repr__(self) -> str:
        return (
            f"<Reminder id={self.id} type={self.type!r} "
            f"due={self.due_date} status={self.status!r}>"
        )
