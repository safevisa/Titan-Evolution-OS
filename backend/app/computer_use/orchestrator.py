"""Computer Use run lifecycle — DB + optional Runner dispatch (M07c)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.computer_use.runner_client import runner_configured
from app.core.config import settings
from app.models.domain import ComputerUseRun, Tenant


def computer_use_enabled(tenant_config: dict[str, Any] | None) -> bool:
    if not isinstance(tenant_config, dict):
        return False
    cu = tenant_config.get("computer_use")
    if isinstance(cu, dict) and cu.get("enabled") is True:
        return True
    return False


async def _active_run_count(session: AsyncSession, tenant_id: UUID) -> int:
    res = await session.execute(
        select(func.count())
        .select_from(ComputerUseRun)
        .where(
            ComputerUseRun.tenant_id == tenant_id,
            ComputerUseRun.status.in_(("queued", "running")),
        )
    )
    return int(res.scalar_one() or 0)


async def submit_run(
    session: AsyncSession,
    tenant_id: UUID,
    instruction: str,
    *,
    task_id: UUID | None = None,
    max_steps: int = 30,
) -> UUID:
    tenant = await session.get(Tenant, tenant_id)
    cfg = tenant.config if tenant and isinstance(tenant.config, dict) else {}
    if not computer_use_enabled(cfg):
        raise ValueError("computer_use_disabled")

    active = await _active_run_count(session, tenant_id)
    if active >= settings.computer_use_max_concurrent:
        raise ValueError("computer_use_concurrency_limit")

    row = ComputerUseRun(
        tenant_id=tenant_id,
        task_id=task_id,
        instruction=instruction.strip(),
        status="queued",
    )
    session.add(row)
    await session.flush()

    if runner_configured():
        from app.computer_use.tasks import dispatch_computer_use_run

        dispatch_computer_use_run.delay(str(row.id))
    else:
        row.status = "failed"
        row.error = "runner_not_configured"
        row.finished_at = datetime.now(tz=timezone.utc)

    await session.flush()
    return row.id


async def get_run(session: AsyncSession, tenant_id: UUID, run_id: UUID) -> dict[str, Any]:
    row = await session.get(ComputerUseRun, run_id)
    if row is None or row.tenant_id != tenant_id:
        return {"ok": False, "error": "not_found"}
    return {
        "ok": True,
        "run_id": str(row.id),
        "status": row.status,
        "instruction": row.instruction[:500],
        "step_count": row.step_count,
        "sandbox_id": row.sandbox_id,
        "artifact_json": row.artifact_json or {},
        "error": row.error,
        "task_id": str(row.task_id) if row.task_id else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "finished_at": row.finished_at.isoformat() if row.finished_at else None,
    }


async def cancel_run(session: AsyncSession, tenant_id: UUID, run_id: UUID) -> dict[str, Any]:
    row = await session.get(ComputerUseRun, run_id)
    if row is None or row.tenant_id != tenant_id:
        return {"ok": False, "error": "not_found"}
    if row.status in ("success", "failed", "cancelled"):
        return {"ok": True, "run_id": str(row.id), "status": row.status}

    if row.sandbox_id and runner_configured():
        try:
            from app.computer_use.runner_client import cancel_run as runner_cancel

            await runner_cancel(row.sandbox_id)
        except Exception as exc:
            row.error = str(exc)[:500]

    row.status = "cancelled"
    row.finished_at = datetime.now(tz=timezone.utc)
    await session.flush()
    return {"ok": True, "run_id": str(row.id), "status": row.status}
