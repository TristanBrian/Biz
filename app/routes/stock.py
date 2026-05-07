# ============================================================
# app/routes/stock.py
# Stock (inventory) management routes.
# Includes a low-stock alert endpoint for dashboard warnings.
# ============================================================

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.business import Business
from app.models.stock import StockItem
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.stock import StockItemCreate, StockItemOut, StockItemUpdate

router = APIRouter(prefix="/stock", tags=["Stock"])


def _verify_ownership(business_id: int, db: Session, user: User) -> Business:
    biz = db.query(Business).filter(Business.id == business_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail="Business not found")
    if biz.user_id != user.id and user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Access denied")
    return biz


# ------------------------------------------------------------
# POST /stock
# ------------------------------------------------------------
@router.post(
    "/",
    response_model=StockItemOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new stock item to a business",
)
def create_stock_item(
    payload: StockItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _verify_ownership(payload.business_id, db, current_user)

    item = StockItem(
        business_id=payload.business_id,
        item_name=payload.item_name,
        quantity=payload.quantity,
        cost_price=payload.cost_price,
        selling_price=payload.selling_price,
        low_stock_threshold=payload.low_stock_threshold,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


# ------------------------------------------------------------
# GET /stock
# ------------------------------------------------------------
@router.get(
    "/",
    response_model=List[StockItemOut],
    summary="List all stock items for a business",
)
def list_stock(
    business_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _verify_ownership(business_id, db, current_user)
    return db.query(StockItem).filter(StockItem.business_id == business_id).all()


# ------------------------------------------------------------
# GET /stock/alerts
# ------------------------------------------------------------
@router.get(
    "/alerts",
    response_model=List[StockItemOut],
    summary="Get stock items that are at or below their low-stock threshold",
)
def low_stock_alerts(
    business_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns only items where quantity <= low_stock_threshold.
    Powers the "Stock running low" dashboard warning.
    """
    _verify_ownership(business_id, db, current_user)

    items = db.query(StockItem).filter(
        StockItem.business_id == business_id,
        StockItem.quantity <= StockItem.low_stock_threshold,
    ).all()

    return items


@router.get(
    "/low",
    response_model=ApiResponse[List[StockItemOut]],
    summary="Get low-stock items using standardized response format",
)
def low_stock_items(
    business_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _verify_ownership(business_id, db, current_user)

    items = db.query(StockItem).filter(
        StockItem.business_id == business_id,
        StockItem.quantity <= StockItem.low_stock_threshold,
    ).all()
    return ApiResponse(
        success=True,
        message="Low stock items fetched successfully",
        data=items,
    )


# ------------------------------------------------------------
# PATCH /stock/{id}
# ------------------------------------------------------------
@router.patch(
    "/{item_id}",
    response_model=StockItemOut,
    summary="Update a stock item (e.g. restock quantity, change price)",
)
def update_stock_item(
    item_id: int,
    payload: StockItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(StockItem).filter(StockItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Stock item not found")

    _verify_ownership(item.business_id, db, current_user)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item


# ------------------------------------------------------------
# DELETE /stock/{id}
# ------------------------------------------------------------
@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a stock item",
)
def delete_stock_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(StockItem).filter(StockItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Stock item not found")

    _verify_ownership(item.business_id, db, current_user)

    db.delete(item)
    db.commit()
