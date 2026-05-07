# ============================================================
# app/routes/business.py
# Business management routes.
# All routes require authentication (JWT).
# SMEs can only view/edit their own businesses.
# ============================================================

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.business import Business
from app.models.user import User
from app.schemas.business import BusinessCreate, BusinessOut, BusinessUpdate

router = APIRouter(prefix="/business", tags=["Businesses"])


def _get_business_or_404(business_id: int, db: Session, current_user: User) -> Business:
    """
    Helper: fetch a business by ID and verify the current user owns it.
    Raises 404 if not found, 403 if not the owner.
    Keeps route handlers clean and DRY.
    """
    biz = db.query(Business).filter(Business.id == business_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail="Business not found")
    if biz.user_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Access denied")
    return biz


# ------------------------------------------------------------
# POST /business
# ------------------------------------------------------------
@router.post(
    "/",
    response_model=BusinessOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new business for the current user",
)
def create_business(
    payload: BusinessCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Register a new SME business.
    The business is automatically linked to the authenticated user.
    """
    biz = Business(
        user_id=current_user.id,
        name=payload.name,
        category=payload.category,
        location=payload.location,
    )
    db.add(biz)
    db.commit()
    db.refresh(biz)
    return biz


# ------------------------------------------------------------
# GET /business
# ------------------------------------------------------------
@router.get(
    "/",
    response_model=List[BusinessOut],
    summary="List all businesses for the current user",
)
def list_businesses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return all businesses owned by the authenticated user.
    Admins see all businesses across the platform.
    """
    if current_user.role == "ADMIN":
        return db.query(Business).all()
    return db.query(Business).filter(Business.user_id == current_user.id).all()


# ------------------------------------------------------------
# GET /business/{id}
# ------------------------------------------------------------
@router.get(
    "/{business_id}",
    response_model=BusinessOut,
    summary="Get a single business by ID",
)
def get_business(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_business_or_404(business_id, db, current_user)


# ------------------------------------------------------------
# PATCH /business/{id}
# ------------------------------------------------------------
@router.patch(
    "/{business_id}",
    response_model=BusinessOut,
    summary="Update a business (partial update — only send fields to change)",
)
def update_business(
    business_id: int,
    payload: BusinessUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Partially update a business. Only the fields you send are changed.
    """
    biz = _get_business_or_404(business_id, db, current_user)

    # model_dump(exclude_unset=True) gives only the fields the client sent
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(biz, field, value)

    db.commit()
    db.refresh(biz)
    return biz


# ------------------------------------------------------------
# DELETE /business/{id}
# ------------------------------------------------------------
@router.delete(
    "/{business_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a business and all its data",
)
def delete_business(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Permanently delete a business.
    Cascades to all sales, stock, and reminders linked to it.
    """
    biz = _get_business_or_404(business_id, db, current_user)
    db.delete(biz)
    db.commit()
    # 204 No Content — no response body
