# ============================================================
# app/core/database.py
# Database engine, session factory, and declarative Base.
# All SQLAlchemy models inherit from Base defined here.
# ============================================================

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

# ------------------------------------------------------------
# Engine
# The engine is the entry point to the database. It manages
# the connection pool automatically — no manual pool management needed.
# pool_pre_ping=True tests connections before using them,
# preventing "connection closed" errors after idle periods.
# ------------------------------------------------------------
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=(settings.APP_ENV == "development"),  # Log SQL only in dev
)

# ------------------------------------------------------------
# Session factory
# Each request gets its own session (see get_db below).
# autocommit=False: we commit manually after successful operations.
# autoflush=False: prevents premature writes mid-transaction.
# ------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# ------------------------------------------------------------
# Declarative Base
# All ORM models (User, Business, etc.) inherit from this Base.
# Base.metadata.create_all(engine) creates tables in the database.
# ------------------------------------------------------------
Base = declarative_base()


# ------------------------------------------------------------
# Dependency — FastAPI route injection
# Usage in any route:
#   def my_route(db: Session = Depends(get_db)):
# The finally block guarantees the session is always closed,
# even if the route raises an exception.
# ------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_runtime_schema() -> None:
    """
    Apply safe, additive schema changes for existing local databases.
    Keeps development environments running without a formal migration toolchain.
    """
    alter_statements = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        "ALTER TABLE sales ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        "ALTER TABLE stock ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        "ALTER TABLE stock ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        "ALTER TABLE reminders ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
    ]
    with engine.begin() as conn:
        for statement in alter_statements:
            conn.execute(text(statement))
