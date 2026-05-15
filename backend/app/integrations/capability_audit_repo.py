"""Append-only audit + idempotency ledger for execute_capability."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import CapabilityAuditLog, CapabilityIdempotency

IdemOutcome = Literal["execute", "replay", "conflict"]


async def append_audit_log(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    capability_id: str,
    ok: bool,
    actor: str | None,
    correlation_id: str | None,
    request_summary: dict[str, Any],
    error: str | None,
    result_summary: dict[str, Any] | None,
) -> None:
    session.add(
        CapabilityAuditLog(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            capability_id=capability_id[:160],
            actor=actor,
            correlation_id=correlation_id,
            request_summary=request_summary,
            ok=ok,
            error=(error[:8000] if error else None),
            result_summary=result_summary,
        )
    )


async def idempotency_try_begin(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    idempotency_key: str,
    capability_id: str,
    stale_after_seconds: int = 900,
) -> tuple[IdemOutcome, dict[str, Any] | None]:
    """
    Returns (outcome, replay_payload_or_none).

    outcome:
      execute — this invocation owns the key (row inserted as running).
      replay — prior succeeded; replay_payload is stored result_summary (wrapped).
      conflict — concurrent in-flight (non-stale running) for same key.
    """
    key = idempotency_key[:160]
    cap = capability_id[:160]
    stale_before = datetime.now(timezone.utc) - timedelta(seconds=stale_after_seconds)

    row = await session.scalar(
        select(CapabilityIdempotency).where(
            CapabilityIdempotency.tenant_id == tenant_id,
            CapabilityIdempotency.idempotency_key == key,
        )
    )
    if row is not None:
        if row.state == "succeeded" and row.result_summary is not None:
            wrapped = {
                "ok": bool(row.result_ok),
                "capability_id": cap,
                "data": row.result_summary.get("data") if isinstance(row.result_summary, dict) else row.result_summary,
                "error": row.result_summary.get("error") if isinstance(row.result_summary, dict) else None,
                "idempotent_replay": True,
            }
            return "replay", wrapped
        if row.state == "running":
            created = row.created_at or datetime.now(timezone.utc)
            if created >= stale_before:
                return "conflict", None
            await session.delete(row)
            await session.flush()
        elif row.state == "failed":
            await session.delete(row)
            await session.flush()

    stmt = (
        insert(CapabilityIdempotency)
        .values(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            idempotency_key=key,
            capability_id=cap,
            state="running",
            result_ok=None,
            result_summary=None,
        )
        .on_conflict_do_nothing(constraint="uq_capability_idem_tenant_key")
    )
    res = await session.execute(stmt)
    if res.rowcount == 1:
        await session.flush()
        return "execute", None

    again = await session.scalar(
        select(CapabilityIdempotency).where(
            CapabilityIdempotency.tenant_id == tenant_id,
            CapabilityIdempotency.idempotency_key == key,
        )
    )
    if again is not None and again.state == "succeeded" and again.result_summary is not None:
        wrapped = {
            "ok": bool(again.result_ok),
            "capability_id": cap,
            "data": again.result_summary.get("data") if isinstance(again.result_summary, dict) else again.result_summary,
            "error": again.result_summary.get("error") if isinstance(again.result_summary, dict) else None,
            "idempotent_replay": True,
        }
        return "replay", wrapped
    return "conflict", None


async def idempotency_mark_succeeded(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    idempotency_key: str,
    result_ok: bool,
    result_for_storage: dict[str, Any],
) -> None:
    await session.execute(
        update(CapabilityIdempotency)
        .where(
            CapabilityIdempotency.tenant_id == tenant_id,
            CapabilityIdempotency.idempotency_key == idempotency_key[:160],
            CapabilityIdempotency.state == "running",
        )
        .values(
            state="succeeded",
            result_ok=result_ok,
            result_summary=result_for_storage,
            finished_at=datetime.now(timezone.utc),
        )
    )


async def idempotency_mark_failed(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    idempotency_key: str,
) -> None:
    """Drop row so the same key may be retried after failure."""
    await session.execute(
        delete(CapabilityIdempotency).where(
            CapabilityIdempotency.tenant_id == tenant_id,
            CapabilityIdempotency.idempotency_key == idempotency_key[:160],
        )
    )
