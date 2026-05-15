"""execute_capability dispatch for computer_use_* (M03 implements)."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

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
    _ = session, tenant_id, clean_params
    return True, {
        "ok": False,
        "capability_id": capability_id,
        "error": "not_implemented",
        "message": "computer_use ships in M03; see docs/development/M03-Computer-Use.md",
    }
