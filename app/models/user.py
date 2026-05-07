# ============================================================
# app/models/user.py
# SQLAlchemy ORM model for the users table.
# ============================================================

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """
    Represents a BizSafi user — either an SME owner or an Admin.

    Relationships:
        businesses: All businesses owned by this user (one-to-many).
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # Full name displayed in the dashboard
    name = Column(String(150), nullable=False)

    # Email is the login identifier — must be unique across the system
    email = Column(String(255), unique=True, index=True, nullable=False)

    # Never store plain-text passwords — only bcrypt hashes
    password_hash = Column(String(255), nullable=False)

    # "SME" = small business owner, "ADMIN" = platform administrator
    role = Column(String(10), nullable=False, default="SME")

    # Automatically set to now() when the record is inserted
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

    # ORM relationship — access via user.businesses
    # cascade="all, delete-orphan" means deleting a user also deletes their businesses
    businesses = relationship(
        "Business",
        back_populates="owner",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role!r}>"
