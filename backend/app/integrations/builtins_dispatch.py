"""Built-in capabilities (server env keys) — called only via execute_capability."""
from __future__ import annotations

from typing import Any

from app.tools.apollo_tool import apollo_search_people
from app.tools.resend_tool import resend_send_email


async def run_builtin_capability(capability_id: str, params: dict[str, Any]) -> Any:
    """Dispatch env-backed catalog capabilities. Raises ValueError on unknown id."""
    if capability_id == "apollo_search":
        return await apollo_search_people(**params)
    if capability_id == "resend_email":
        return await resend_send_email(**params)
    raise ValueError(f"unknown_builtin_capability:{capability_id}")
