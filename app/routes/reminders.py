# ============================================================
# app/routes/reminders.py
# Compliance & operational reminder routes.
# SMEs set due dates; the cron job fires SMS notifications.
# ============================================================

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.business import Business
from app.models.reminder import Reminder
from app.models.user import User
from app.schemas.reminder import ReminderCreate, ReminderOut, ReminderUpdate

router = APIRouter(prefix="/reminders", tags=["Reminders"])


def _verify_ownership(business_id: int, db: Session, user: User) -> Business:
    biz = db.query(Business).filter(Business.id == business_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail="Business not found")
    if biz.user_id != user.id and user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Access denied")
    return biz


# ------------------------------------------------------------
# POST /reminders
# ------------------------------------------------------------
@router.post(
    "/",
    response_model=ReminderOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new compliance or operational reminder",
)
def create_reminder(
    payload: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a reminder. The cron job checks daily and sends an SMS
    when due_date is 3 days or fewer away.
    """
    _verify_ownership(payload.business_id, db, current_user)

    reminder = Reminder(
        business_id=payload.business_id,
        type=payload.type,
        message=payload.message,
        due_date=payload.due_date,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


# ------------------------------------------------------------
# GET /reminders
# ------------------------------------------------------------
@router.get(
    "/",
    response_model=List[ReminderOut],
    summary="List reminders for a business, optionally filtered by status",
)
def list_reminders(
    business_id: int = Query(...),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return all reminders for the given business, sorted by due date (soonest first).
    Filter by status with ?status=pending | sent | done
    """
    _verify_ownership(business_id, db, current_user)

    query = db.query(Reminder).filter(Reminder.business_id == business_id)

    if status_filter:
        query = query.filter(Reminder.status == status_filter)

    return query.order_by(Reminder.due_date.asc()).all()


# ------------------------------------------------------------
# PATCH /reminders/{id}
# ------------------------------------------------------------
@router.patch(
    "/{reminder_id}",
    response_model=ReminderOut,
    summary="Update a reminder (message, due date, or mark as done)",
)
def update_reminder(
    reminder_id: int,
    payload: ReminderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Partial update. To mark a reminder as completed:
        PATCH /reminders/5  {"status": "done"}
    """
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    _verify_ownership(reminder.business_id, db, current_user)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(reminder, field, value)

    db.commit()
    db.refresh(reminder)
    return reminder


# ------------------------------------------------------------
# DELETE /reminders/{id}
# ------------------------------------------------------------
@router.delete(
    "/{reminder_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a reminder",
)
def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    _verify_ownership(reminder.business_id, db, current_user)

    db.delete(reminder)
    db.commit()
