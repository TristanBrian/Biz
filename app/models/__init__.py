# app/models/__init__.py
# Import all ORM models here so SQLAlchemy's metadata registry
# knows about them when Base.metadata.create_all() is called.

from app.models.user import User          # noqa: F401
from app.models.business import Business  # noqa: F401
from app.models.sales import Sale         # noqa: F401
from app.models.stock import StockItem    # noqa: F401
from app.models.reminder import Reminder  # noqa: F401
