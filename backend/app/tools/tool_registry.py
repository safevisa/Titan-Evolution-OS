from typing import Any

from app.integrations.builtins_dispatch import run_builtin_capability


def get_tools_for_role(role: str) -> list[str]:
    names = ["apollo_search", "resend_email"]
    if role == "hunter":
        return names
    if role == "outreach":
        return ["resend_email"]
    return []


async def run_tool(name: str, **kwargs: Any) -> Any:
    """Deprecated: use execute_capability / builtins_dispatch. Kept for legacy imports."""
    if name in ("apollo_search", "resend_email"):
        return await run_builtin_capability(name, dict(kwargs))
    raise ValueError(f"unknown tool {name}")
