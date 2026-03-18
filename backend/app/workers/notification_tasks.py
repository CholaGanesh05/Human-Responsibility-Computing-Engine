"""
HRCE — Notification Tasks (Celery)

Background tasks for:
  - send_reminder_task      : warns user ≤3 days before due date
  - send_escalation_task    : alerts when a task is overdue & still active
  - send_missed_alert_task  : fires when due_date passed without completion
  - scan_upcoming_responsibilities : Celery Beat periodic entry point

NOTE: These tasks use SYNCHRONOUS SQLAlchemy (psycopg2) because Celery
workers are not async-capable. They use a separate sync engine.
"""
from celery import shared_task
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.responsibility import Responsibility, ResponsibilityStatus, PreparationStatus
from app.models.notification import Notification, NotificationType

# ── Sync DB engine for Celery workers (psycopg2, NOT asyncpg) ───────────────
_sync_db_url = settings.database_url.replace(
    "postgresql+asyncpg://", "postgresql+psycopg2://"
)
_sync_engine = create_engine(_sync_db_url, pool_pre_ping=True)


def _get_sync_session() -> Session:
    return Session(_sync_engine)


# ──────────────────────────────────────────────────────────────────────────────
# Helper: write notification row (sync)
# ──────────────────────────────────────────────────────────────────────────────

def _write_notification(
    session: Session,
    user_id,
    responsibility_id,
    notification_type: NotificationType,
    message: str,
) -> None:
    """Idempotent: skip if an unread notification of the same type already exists."""
    existing = session.execute(
        select(Notification).where(
            Notification.responsibility_id == responsibility_id,
            Notification.type == notification_type,
            Notification.is_read == False,  # noqa: E712
        )
    ).scalar_one_or_none()
    if existing:
        return  # Already notified, don't spam

    notification = Notification(
        user_id=user_id,
        responsibility_id=responsibility_id,
        type=notification_type,
        message=message,
    )
    session.add(notification)
    session.commit()

    # ── Live push via Redis pub/sub (fire-and-forget from sync context) ───────
    try:
        import asyncio
        from app.core.event_emitter import emit_notification
        asyncio.run(emit_notification(
            user_id=str(user_id),
            notification={
                "type": notification_type.value,
                "message": message,
                "responsibility_id": str(responsibility_id),
            }
        ))
    except Exception:
        pass  # Never crash Celery tasks on WS push failure



# ──────────────────────────────────────────────────────────────────────────────
# Task 1: Reminder (≤ 3 days to due date, not yet READY)
# ──────────────────────────────────────────────────────────────────────────────

@shared_task(name="notification_tasks.send_reminder", bind=True, max_retries=3)
def send_reminder_task(self, responsibility_id: str):
    """Sends a REMINDER notification if the responsibility is due in ≤ 3 days."""
    try:
        with _get_sync_session() as session:
            r = session.get(Responsibility, responsibility_id)
            if not r or not r.due_date:
                return {"status": "skipped", "reason": "no due_date"}

            now = datetime.now(timezone.utc)
            delta = r.due_date.replace(tzinfo=timezone.utc) - now
            days_left = delta.days

            if days_left > 3 or days_left < 0:
                return {"status": "skipped", "reason": "not in reminder window"}

            if r.preparation_status == PreparationStatus.READY:
                return {"status": "skipped", "reason": "already READY"}

            message = (
                f"⏰ Reminder: '{r.title}' is due in {days_left} day(s). "
                f"Preparation status: {r.preparation_status.value}."
            )
            user_id = r.assigned_to_id or r.event.owner_id if r.event else None
            if not user_id:
                return {"status": "skipped", "reason": "no user to notify"}

            _write_notification(session, user_id, r.id, NotificationType.REMINDER, message)
            return {"status": "sent", "type": "REMINDER", "responsibility_id": responsibility_id}

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


# ──────────────────────────────────────────────────────────────────────────────
# Task 2: Escalation (overdue & still ACTIVE)
# ──────────────────────────────────────────────────────────────────────────────

@shared_task(name="notification_tasks.send_escalation", bind=True, max_retries=3)
def send_escalation_task(self, responsibility_id: str):
    """Fires an ESCALATION alert when a task is overdue but still active."""
    try:
        with _get_sync_session() as session:
            r = session.get(Responsibility, responsibility_id)
            if not r or not r.due_date:
                return {"status": "skipped", "reason": "no due_date"}

            now = datetime.now(timezone.utc)
            due = r.due_date.replace(tzinfo=timezone.utc)

            if due > now:
                return {"status": "skipped", "reason": "not yet overdue"}

            if r.status not in (ResponsibilityStatus.ACTIVE, ResponsibilityStatus.PENDING):
                return {"status": "skipped", "reason": "already resolved"}

            days_overdue = (now - due).days
            message = (
                f"🚨 Escalation: '{r.title}' is {days_overdue} day(s) overdue! "
                f"Current status: {r.status.value}. Immediate action required."
            )
            user_id = r.assigned_to_id or (r.event.owner_id if r.event else None)
            if not user_id:
                return {"status": "skipped", "reason": "no user to notify"}

            _write_notification(session, user_id, r.id, NotificationType.ESCALATION, message)
            return {"status": "sent", "type": "ESCALATION", "responsibility_id": responsibility_id}

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


# ──────────────────────────────────────────────────────────────────────────────
# Task 3: Missed Alert (past due & not completed)
# ──────────────────────────────────────────────────────────────────────────────

@shared_task(name="notification_tasks.send_missed_alert", bind=True, max_retries=3)
def send_missed_alert_task(self, responsibility_id: str):
    """Marks a responsibility as MISSED and stores alert notification."""
    try:
        with _get_sync_session() as session:
            r = session.get(Responsibility, responsibility_id)
            if not r or not r.due_date:
                return {"status": "skipped", "reason": "no due_date"}

            now = datetime.now(timezone.utc)
            due = r.due_date.replace(tzinfo=timezone.utc)

            if due > now:
                return {"status": "skipped", "reason": "not yet past due"}

            if r.status == ResponsibilityStatus.COMPLETED:
                return {"status": "skipped", "reason": "already completed"}

            message = (
                f"❌ Missed: '{r.title}' was due on {due.strftime('%Y-%m-%d')} "
                f"and was never completed. Please review."
            )
            user_id = r.assigned_to_id or (r.event.owner_id if r.event else None)
            if not user_id:
                return {"status": "skipped", "reason": "no user to notify"}

            _write_notification(session, user_id, r.id, NotificationType.MISSED, message)
            return {"status": "sent", "type": "MISSED", "responsibility_id": responsibility_id}

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


# ──────────────────────────────────────────────────────────────────────────────
# Periodic Scan (Celery Beat entry point)
# ──────────────────────────────────────────────────────────────────────────────

@shared_task(name="notification_tasks.scan_upcoming_responsibilities")
def scan_upcoming_responsibilities():
    """
    Runs every hour (scheduled via Celery Beat).
    Queries responsibilities that need attention and dispatches sub-tasks.
    """
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(days=3)

    with _get_sync_session() as session:
        # Upcoming (in 0-3 days)
        upcoming = session.execute(
            select(Responsibility).where(
                Responsibility.due_date >= now,
                Responsibility.due_date <= window_end,
                Responsibility.status != ResponsibilityStatus.COMPLETED,
            )
        ).scalars().all()

        # Overdue (past due_date, not completed)
        overdue = session.execute(
            select(Responsibility).where(
                Responsibility.due_date < now,
                Responsibility.status != ResponsibilityStatus.COMPLETED,
            )
        ).scalars().all()

    dispatched = {"reminder": 0, "escalation": 0, "missed": 0}

    for r in upcoming:
        send_reminder_task.delay(str(r.id))
        dispatched["reminder"] += 1

    for r in overdue:
        send_escalation_task.delay(str(r.id))
        send_missed_alert_task.delay(str(r.id))
        dispatched["escalation"] += 1
        dispatched["missed"] += 1

    return {"status": "scan_complete", "dispatched": dispatched}
