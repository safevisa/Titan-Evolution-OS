"""Celery tasks for Computer Use dispatch and reaper (M07c)."""
from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from uuid import UUID

from app.workers.celery_app import celery_app

_RUN_TIMEOUT_SEC = 1800
_POLL_SEC = 5.0


@celery_app.task(name="titan.computer_use.dispatch")
def dispatch_computer_use_run(run_id: str) -> dict:
    return asyncio.get_event_loop().run_until_complete(_dispatch_async(run_id))


async def _dispatch_async(run_id: str) -> dict:
    from app.computer_use.runner_client import create_run, get_run, runner_configured
    from app.core.database import AsyncSessionLocal
    from app.models.domain import ComputerUseRun

    if not runner_configured():
        return {"error": "runner_not_configured"}

    async with AsyncSessionLocal() as db:
        row = await db.get(ComputerUseRun, UUID(run_id))
        if row is None:
            return {"error": "not_found"}
        if row.status not in ("queued",):
            return {"status": row.status}

        row.status = "running"
        await db.commit()

        try:
            created = await create_run(instruction=row.instruction, max_steps=30)
            runner_id = str(created.get("run_id") or created.get("id") or "")
            row.sandbox_id = runner_id
            await db.commit()
        except Exception as exc:
            row.status = "failed"
            row.error = str(exc)[:800]
            row.finished_at = datetime.now(tz=timezone.utc)
            await db.commit()
            return {"status": "failed", "error": row.error}

        deadline = time.monotonic() + _RUN_TIMEOUT_SEC
        while time.monotonic() < deadline:
            await asyncio.sleep(_POLL_SEC)
            try:
                remote = await get_run(row.sandbox_id or "")
            except Exception as exc:
                row.error = str(exc)[:500]
                continue
            status = str(remote.get("status") or "").lower()
            row.step_count = int(remote.get("step_count") or row.step_count or 0)
            if remote.get("artifact"):
                row.artifact_json = remote.get("artifact") or row.artifact_json
            if status in ("success", "succeeded", "completed"):
                row.status = "success"
                row.finished_at = datetime.now(tz=timezone.utc)
                await db.commit()
                return {"status": "success", "run_id": run_id}
            if status in ("failed", "error"):
                row.status = "failed"
                row.error = str(remote.get("error") or "runner_failed")[:800]
                row.finished_at = datetime.now(tz=timezone.utc)
                await db.commit()
                return {"status": "failed", "error": row.error}
            if status in ("cancelled", "canceled"):
                row.status = "cancelled"
                row.finished_at = datetime.now(tz=timezone.utc)
                await db.commit()
                return {"status": "cancelled"}

        row.status = "failed"
        row.error = "timeout"
        row.finished_at = datetime.now(tz=timezone.utc)
        await db.commit()
        return {"status": "failed", "error": "timeout"}


@celery_app.task(name="titan.computer_use.reaper")
def reaper_stale_runs() -> dict:
    return asyncio.get_event_loop().run_until_complete(_reaper_async())


async def _reaper_async() -> dict:
    from sqlalchemy import select

    from app.core.database import AsyncSessionLocal
    from app.models.domain import ComputerUseRun

    cutoff = datetime.now(tz=timezone.utc)
    marked = 0
    async with AsyncSessionLocal() as db:
        res = await db.execute(
            select(ComputerUseRun).where(ComputerUseRun.status.in_(("queued", "running")))
        )
        for row in res.scalars().all():
            created = row.created_at
            if created and (cutoff - created).total_seconds() > _RUN_TIMEOUT_SEC:
                row.status = "failed"
                row.error = "reaper_timeout"
                row.finished_at = cutoff
                marked += 1
        await db.commit()
    return {"marked_failed": marked}
