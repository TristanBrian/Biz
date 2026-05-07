# ============================================================
# app/main.py
# BizSafi API — FastAPI application entry point.
#
# Responsibilities:
#   - Register all route modules
#   - Configure CORS for the PWA frontend
#   - Start the APScheduler cron job for SMS reminders
#   - Mount the /ai/query endpoint
# ============================================================

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import Base, engine, ensure_runtime_schema
from app.core.deps import get_current_user
from app.models import business, reminder, sales, stock, user  # noqa: F401 — registers models
from app.routes import auth, business as biz_router, dashboard, reminders, sales as sales_router, stock as stock_router
from app.services.ai_service import query_ai
from app.services.notification_service import run_reminder_cron

# Configure root logger — shows timestamps and log level in uvicorn output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# APScheduler — background task runner
# AsyncIOScheduler works inside the asyncio event loop,
# which is the same loop FastAPI/uvicorn uses.
# ------------------------------------------------------------
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    Code before `yield` runs on startup; code after runs on shutdown.
    """
    # --- Startup ---
    logger.info("BizSafi API starting up...")

    # Create all DB tables from ORM models (idempotent — safe to run every start)
    # In production, use Alembic migrations instead of create_all.
    Base.metadata.create_all(bind=engine)
    ensure_runtime_schema()
    logger.info("Database tables verified / created")

    # Schedule the daily reminder SMS cron job
    # Runs every day at 08:00 Nairobi time (East Africa Time = UTC+3)
    scheduler.add_job(
        run_reminder_cron,
        trigger="cron",
        hour=8,
        minute=0,
        timezone="Africa/Nairobi",
        id="daily_reminders",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("APScheduler started — reminder cron runs daily at 08:00 EAT")

    yield  # Application runs here

    # --- Shutdown ---
    scheduler.shutdown(wait=False)
    logger.info("BizSafi API shut down cleanly")


# ------------------------------------------------------------
# FastAPI application instance
# ------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "BizSafi — SME Operations + Compliance Assistant API. "
        "Tracks sales, stock, and compliance reminders for small businesses in Kenya."
    ),
    version="1.0.0",
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc UI
    lifespan=lifespan,
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    """Return standardized API error envelope for HTTP errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail},
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error"},
    )

# ------------------------------------------------------------
# CORS — allow the PWA frontend to call the API
# In production, replace ["*"] with your frontend domain.
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: replace with ["https://app.bizsafi.co.ke"] in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# Route modules
# ------------------------------------------------------------
app.include_router(auth.router)
app.include_router(biz_router.router)
app.include_router(sales_router.router)
app.include_router(stock_router.router)
app.include_router(reminders.router)
app.include_router(dashboard.router)

frontend_dir = Path(__file__).resolve().parents[1] / "frontend"
if frontend_dir.exists():
    app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")


# ------------------------------------------------------------
# AI query endpoint
# POST /ai/query — ask Claude for business advice
# ------------------------------------------------------------
class AIQueryRequest(BaseModel):
    """Request body for the AI advisory endpoint."""
    prompt: str
    business_context: str = ""  # Optional — e.g. "salon in Nairobi"


@app.post(
    "/ai/query",
    tags=["AI Advisory"],
    summary="Ask the AI for business advice",
)
async def ai_query(
    payload: AIQueryRequest,
    current_user=Depends(get_current_user),  # Must be logged in
):
    """
    Send a business question to Claude and get practical advice.

    Example prompt: "How can a salon in Nairobi track daily profits simply?"

    The response includes:
    - `advice`: Claude's actionable answer
    - `prompt_used`: The full prompt sent (for debugging)
    - `model`: Claude model version used
    """
    result = await query_ai(
        user_prompt=payload.prompt,
        business_context=payload.business_context,
    )
    return result


# ------------------------------------------------------------
# Health check — used by load balancers / uptime monitors
# ------------------------------------------------------------
@app.get("/", tags=["Health"])
def health_check():
    """Returns API status. No auth required."""
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }


@app.get("/app", include_in_schema=False)
def frontend_app():
    """Serve the starter frontend UI."""
    if not frontend_dir.exists():
        return {"detail": "Frontend folder not found"}
    return FileResponse(frontend_dir / "index.html")
