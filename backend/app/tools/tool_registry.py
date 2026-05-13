from typing import Any

from app.tools.apollo_tool import apollo_search_people
from app.tools.resend_tool import resend_send_email


def get_tools_for_role(role: str) -> list[str]:
    names = ["apollo_search", "resend_email"]
    if role == "hunter":
        return names
    if role == "outreach":
        return ["resend_email"]
    return []


async def run_tool(name: str, **kwargs: Any) -> Any:
    if name == "apollo_search":
        return await apollo_search_people(**kwargs)
    if name == "resend_email":
        return await resend_send_email(**kwargs)
    raise ValueError(f"unknown tool {name}")
