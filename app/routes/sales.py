# ============================================================
# app/routes/sales.py
# Sales tracking routes.
# SMEs log daily revenue; the API also provides summaries.
# ============================================================

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.business import Business
from app.models.sales import Sale
from app.models.user import User
from app.schemas.sales import SaleCreate, SaleOut, SaleSummary

router = APIRouter(prefix="/sales", tags=["Sales"])


def _verify_business_ownership(business_id: int, db: Session, user: User) -> Business:
    """Ensure the business exists and the user owns it."""
    biz = db.query(Business).filter(Business.id == business_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail="Business not found")
    if biz.user_id != user.id and user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Access denied")
    return biz


# ------------------------------------------------------------
# POST /sales
# ------------------------------------------------------------
@router.post(
    "/",
    response_model=SaleOut,
    status_code=status.HTTP_201_CREATED,
    summary="Log a new sales entry",
)
def create_sale(
    payload: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Record a sale for a business.
    SMEs log this at the end of each day (or in real time).
    """
    _verify_business_ownership(payload.business_id, db, current_user)

    sale = Sale(
        business_id=payload.business_id,
        amount=payload.amount,
        date=payload.date,
        notes=payload.notes,
    )
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


# ------------------------------------------------------------
# GET /sales
# ------------------------------------------------------------
@router.get(
    "/",
    response_model=List[SaleOut],
    summary="List sales entries for a business (with optional date filter)",
)
def list_sales(
    business_id: int = Query(..., description="ID of the business to query"),
    start_date: Optional[date] = Query(None, description="Filter from this date (inclusive)"),
    end_date: Optional[date] = Query(None, description="Filter up to this date (inclusive)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return all sales for a business, newest first.
    Optionally filter by a date range (start_date to end_date).
    """
    _verify_business_ownership(business_id, db, current_user)

    query = db.query(Sale).filter(Sale.business_id == business_id)

    if start_date:
        query = query.filter(Sale.date >= start_date)
    if end_date:
        query = query.filter(Sale.date <= end_date)

    return query.order_by(Sale.date.desc()).all()


# ------------------------------------------------------------
# GET /sales/summary
# ------------------------------------------------------------
@router.get(
    "/summary",
    response_model=SaleSummary,
    summary="Get aggregated sales total for a business",
)
def sales_summary(
    business_id: int = Query(...),
    period: str = Query("today", description="'today' | 'month' — reporting period"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns total revenue and entry count for the given period.
    Powers the "You made KES X today" dashboard insight.
    """
    _verify_business_ownership(business_id, db, current_user)

    query = db.query(
        func.sum(Sale.amount).label("total"),
        func.count(Sale.id).label("count"),
    ).filter(Sale.business_id == business_id)

    today = date.today()

    if period == "today":
        query = query.filter(Sale.date == today)
        label = str(today)
    elif period == "month":
        query = query.filter(
            func.extract("year", Sale.date) == today.year,
            func.extract("month", Sale.date) == today.month,
        )
        label = today.strftime("%Y-%m")
    else:
        raise HTTPException(status_code=400, detail="period must be 'today' or 'month'")

    result = query.one()

    return SaleSummary(
        total_sales=round(result.total or 0, 2),
        total_entries=result.count or 0,
        period=label,
    )


# ------------------------------------------------------------
# DELETE /sales/{id}
# ------------------------------------------------------------
@router.delete(
    "/{sale_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a sales entry",
)
def delete_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")

    _verify_business_ownership(sale.business_id, db, current_user)

    db.delete(sale)
    db.commit()
