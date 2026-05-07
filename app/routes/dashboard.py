from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.business import Business
from app.models.reminder import Reminder
from app.models.sales import Sale
from app.models.stock import StockItem
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.dashboard import DashboardSummaryOut

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/summary",
    response_model=ApiResponse[DashboardSummaryOut],
    summary="Get dashboard KPI summary for the authenticated user",
)
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    upcoming_cutoff = today + timedelta(days=3)

    business_ids_query = db.query(Business.id)
    if current_user.role != "ADMIN":
        business_ids_query = business_ids_query.filter(Business.user_id == current_user.id)
    business_ids = [row[0] for row in business_ids_query.all()]

    if not business_ids:
        empty = DashboardSummaryOut(
            today_sales=0.0,
            sales_count=0,
            low_stock_count=0,
            upcoming_reminders=0,
        )
        return ApiResponse(success=True, message="Dashboard summary fetched successfully", data=empty)

    sales_result = (
        db.query(func.sum(Sale.amount).label("total"), func.count(Sale.id).label("count"))
        .filter(Sale.business_id.in_(business_ids), Sale.date == today)
        .one()
    )

    low_stock_count = (
        db.query(func.count(StockItem.id))
        .filter(
            StockItem.business_id.in_(business_ids),
            StockItem.quantity <= StockItem.low_stock_threshold,
        )
        .scalar()
        or 0
    )

    upcoming_reminders = (
        db.query(func.count(Reminder.id))
        .filter(
            Reminder.business_id.in_(business_ids),
            Reminder.status == "pending",
            Reminder.due_date >= today,
            Reminder.due_date <= upcoming_cutoff,
        )
        .scalar()
        or 0
    )

    payload = DashboardSummaryOut(
        today_sales=round(sales_result.total or 0, 2),
        sales_count=sales_result.count or 0,
        low_stock_count=low_stock_count,
        upcoming_reminders=upcoming_reminders,
    )

    return ApiResponse(
        success=True,
        message="Dashboard summary fetched successfully",
        data=payload,
    )
