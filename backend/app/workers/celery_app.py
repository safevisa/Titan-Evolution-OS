from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "titan",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "evolution-scan-hourly": {
            "task": "titan.evolution.scan_all",
            "schedule": 3600,  # every hour
        },
    },
)

import app.workers.tasks  # noqa: E402, F401 — register tasks
import app.workers.evolution_worker  # noqa: E402, F401 — register evolution tasks
