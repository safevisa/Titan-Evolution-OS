"""execute_capability dispatch for computer_use_* (M03/M07c)."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.computer_use.orchestrator import cancel_run, get_run, submit_run

_COMPUTER_USE_IDS = frozenset(
    {
        "computer_use_submit",
        "computer_use_status",
        "computer_use_cancel",
    }
)


async def try_computer_use_capability(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    capability_id: str,
    clean_params: dict[str, Any],
) -> tuple[bool, dict[str, Any] | None]:
    if capability_id not in _COMPUTER_USE_IDS:
        return False, None

    try:
        if capability_id == "computer_use_submit":
            instruction = str(clean_params.get("instruction") or "").strip()
            if not instruction:
                return True, {
                    "ok": False,
                    "capability_id": capability_id,
                    "error": "missing_instruction",
                }
            task_id_raw = clean_params.get("task_id")
            task_id = UUID(str(task_id_raw)) if task_id_raw else None
            max_steps = int(clean_params.get("max_steps") or 30)
            run_id = await submit_run(
                session,
                tenant_id,
                instruction,
                task_id=task_id,
                max_steps=max_steps,
            )
            return True, {
                "ok": True,
                "capability_id": capability_id,
                "data": {"run_id": str(run_id)},
            }

        if capability_id == "computer_use_status":
            run_id_raw = clean_params.get("run_id")
            if not run_id_raw:
                return True, {
                    "ok": False,
                    "capability_id": capability_id,
                    "error": "missing_run_id",
                }
            data = await get_run(session, tenant_id, UUID(str(run_id_raw)))
            return True, {
                "ok": bool(data.get("ok")),
                "capability_id": capability_id,
                "data": data,
                "error": data.get("error"),
            }

        if capability_id == "computer_use_cancel":
            run_id_raw = clean_params.get("run_id")
            if not run_id_raw:
                return True, {
                    "ok": False,
                    "capability_id": capability_id,
                    "error": "missing_run_id",
                }
            data = await cancel_run(session, tenant_id, UUID(str(run_id_raw)))
            return True, {
                "ok": bool(data.get("ok")),
                "capability_id": capability_id,
                "data": data,
                "error": data.get("error"),
            }
    except ValueError as exc:
        return True, {
            "ok": False,
            "capability_id": capability_id,
            "error": str(exc),
        }
    except Exception as exc:
        return True, {
            "ok": False,
            "capability_id": capability_id,
            "error": "computer_use_error",
            "message": str(exc)[:500],
        }

    return False, None
