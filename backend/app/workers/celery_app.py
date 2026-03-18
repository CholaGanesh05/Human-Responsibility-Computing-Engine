"""
HRCE Backend — Celery Application
Background task worker using Redis as broker and result backend.
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "hrce",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.workers.notification_tasks",  # Stage 7: Reminders, escalations, missed alerts
        "app.workers.agent_tasks",          # Stage 10: Auto agent execution triggers
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# ── Celery Beat Periodic Schedule ────────────────────────────────────────────
celery_app.conf.beat_schedule = {
    # Scans all responsibilities every hour and dispatches reminder/escalation/missed tasks
    "scan-upcoming-responsibilities-every-hour": {
        "task": "notification_tasks.scan_upcoming_responsibilities",
        "schedule": crontab(minute=0),  # top of every hour
    },
    # Stage 10: Re-run AI risk scoring on overdue/near-due responsibilities every hour
    "analyze-delayed-responsibilities-every-hour": {
        "task": "agent_tasks.analyze_delayed_responsibilities",
        "schedule": crontab(minute=30),  # at :30 of every hour (offset from notification scan)
    },
}
