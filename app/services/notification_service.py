# ============================================================
# app/services/notification_service.py
# SMS notification service using Africa's Talking gateway.
# A cron job runs daily and sends SMS for upcoming reminders.
#
# Cron logic: if due_date - today <= 3 days → send SMS
# Lifecycle:  pending → sent  (user marks it → done)
# ============================================================

import logging
from datetime import date, timedelta

import africastalking

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.business import Business
from app.models.reminder import Reminder
from app.models.user import User

logger = logging.getLogger(__name__)

# Initialise Africa's Talking SDK once at module load
africastalking.initialize(
    username=settings.AT_USERNAME,
    api_key=settings.AT_API_KEY,
)
sms_service = africastalking.SMS


def _build_sms_message(reminder: Reminder, business_name: str) -> str:
    """
    Format the SMS text to send to the SME owner.
    Kept under 160 characters where possible for single SMS billing.
    """
    days = reminder.days_until_due
    urgency = "TODAY" if days == 0 else f"in {days} day(s)"
    return (
        f"[BizSafi] {business_name}: {reminder.message} — Due {urgency} "
        f"({reminder.due_date}). Reply STOP to unsubscribe."
    )


def send_reminder_sms(phone_number: str, message: str) -> bool:
    """
    Send a single SMS via Africa's Talking.

    Args:
        phone_number: Recipient in international format, e.g. "+254712345678"
        message:      SMS body text.

    Returns:
        True if the API accepted the message, False on failure.
    """
    try:
        response = sms_service.send(
            message=message,
            recipients=[phone_number],
        )
        logger.info("SMS sent to %s: %s", phone_number, response)
        return True
    except Exception as exc:
        logger.error("Failed to send SMS to %s: %s", phone_number, exc)
        return False


def run_reminder_cron() -> None:
    """
    Main cron job — called daily by APScheduler.

    Algorithm:
    1. Query all 'pending' reminders where due_date - today <= 3 days.
    2. For each, load the owning business and user.
    3. Send an SMS to the user's registered phone (if available).
    4. Update reminder status from 'pending' → 'sent'.

    This function opens and closes its own DB session because it runs
    outside of a FastAPI request context (no Depends() injection here).
    """
    db = SessionLocal()
    try:
        today = date.today()
        alert_window = today + timedelta(days=3)

        # Fetch all pending reminders due within the next 3 days
        due_reminders = (
            db.query(Reminder)
            .filter(
                Reminder.status == "pending",
                Reminder.due_date <= alert_window,
                Reminder.due_date >= today,  # Don't resend overdue ones
            )
            .all()
        )

        logger.info("Reminder cron: found %d reminders to process", len(due_reminders))

        for reminder in due_reminders:
            # Load business and owner
            business = db.query(Business).filter(Business.id == reminder.business_id).first()
            if not business:
                continue

            user = db.query(User).filter(User.id == business.user_id).first()
            if not user:
                continue

            # NOTE: User model doesn't have a phone field yet.
            # When you add it, replace this placeholder:
            phone = getattr(user, "phone", None)

            if not phone:
                logger.warning(
                    "User %s has no phone number — skipping reminder %s",
                    user.id, reminder.id,
                )
                # Still mark as sent so we don't loop forever
                reminder.status = "sent"
                db.commit()
                continue

            message = _build_sms_message(reminder, business.name)
            success = send_reminder_sms(phone, message)

            if success:
                reminder.status = "sent"
                db.commit()
                logger.info(
                    "Reminder %s marked as 'sent' for business '%s'",
                    reminder.id, business.name,
                )

    except Exception as exc:
        logger.error("Reminder cron job crashed: %s", exc)
        db.rollback()
    finally:
        db.close()
