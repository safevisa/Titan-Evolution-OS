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
        "context-sync-tick": {
            "task": "titan.context_sync.tick",
            "schedule": 1200,
        },
        "context-sync-rollup": {
            "task": "titan.context_sync.rollup",
            "schedule": 21600,
        },
        "computer-use-reaper": {
            "task": "titan.computer_use.reaper",
            "schedule": 900,
        },
    },
)

import app.workers.tasks  # noqa: E402, F401 — register tasks
import app.workers.evolution_worker  # noqa: E402, F401 — register evolution tasks
import app.context_sync.tasks  # noqa: E402, F401 — register context sync tasks
import app.computer_use.tasks  # noqa: E402, F401 — register computer use tasks
