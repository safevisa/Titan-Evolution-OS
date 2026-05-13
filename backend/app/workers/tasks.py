"""Celery tasks — Phase 1 queue for agent runs (expand with real runners)."""

from app.workers.celery_app import celery_app


@celery_app.task(name="titan.ping")
def ping() -> str:
    return "pong"


@celery_app.task(name="titan.enqueue_agent_task")
def enqueue_agent_task(task_id: str) -> dict:
    """Placeholder: mark task running in DB and invoke agent (implemented in Phase 1+)."""
    return {"task_id": task_id, "status": "queued"}
