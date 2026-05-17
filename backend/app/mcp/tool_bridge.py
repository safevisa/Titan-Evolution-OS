"""Map MCP tools into OpenAI tool-calling format for agent_tool_runner."""
from __future__ import annotations

import json
from typing import Any

from app.mcp.host import get_mcp_host

MCP_TOOL_PREFIX = "mcp__"


async def ensure_mcp_started() -> None:
    from app.core.config import settings
    from app.mcp.host import get_mcp_host, servers_to_autostart

    if not settings.mcp_autostart:
        return
    host = get_mcp_host()
    if not host.is_started:
        await host.start(servers_to_autostart())


async def openai_tools_for_role(role: str) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """
    Returns (openai_tools, safe_name -> original_mcp_tool_name).
    Safe names use MCP_TOOL_PREFIX to avoid colliding with capability tool ids.
    """
    await ensure_mcp_started()
    host = get_mcp_host()
    if not host.is_started or host.ready_server_count() == 0:
        return [], {}
    raw = await host.list_tools_for_role(role)
    tools: list[dict[str, Any]] = []
    name_map: dict[str, str] = {}
    for entry in raw:
        fn = entry.get("function") or {}
        orig = str(fn.get("name") or "")
        if not orig:
            continue
        safe = f"{MCP_TOOL_PREFIX}{orig}"
        name_map[safe] = orig
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": safe,
                    "description": fn.get("description", "") or f"MCP tool {orig}",
                    "parameters": fn.get("parameters") or {"type": "object", "properties": {}},
                },
            }
        )
    return tools, name_map


def is_mcp_tool_name(name: str) -> bool:
    return name.startswith(MCP_TOOL_PREFIX)


def resolve_mcp_tool_name(safe_name: str, name_map: dict[str, str]) -> str | None:
    if safe_name in name_map:
        return name_map[safe_name]
    if safe_name.startswith(MCP_TOOL_PREFIX):
        return safe_name[len(MCP_TOOL_PREFIX) :]
    return None


async def execute_mcp_tool(safe_name: str, arguments: dict[str, Any], name_map: dict[str, str]) -> dict[str, Any]:
    orig = resolve_mcp_tool_name(safe_name, name_map)
    if not orig:
        return {"ok": False, "error": "unknown_mcp_tool"}
    await ensure_mcp_started()
    host = get_mcp_host()
    result = await host.call_tool(orig, arguments)
    text_parts = []
    for block in result.get("content") or []:
        if isinstance(block, dict) and block.get("type") == "text":
            text_parts.append(str(block.get("text", "")))
    payload = {
        "ok": not bool(result.get("isError")),
        "mcp_tool": orig,
        "text": "\n".join(text_parts)[:12000],
        "raw": result,
    }
    return payload


async def maybe_broadcast_tool_log(
    *,
    task_id: str | None,
    role: str,
    safe_name: str,
    ok: bool,
) -> None:
    if not task_id:
        return
    try:
        from app.websocket import broadcast_task_log

        await broadcast_task_log(
            task_id,
            {
                "level": "tool" if ok else "error",
                "message": f"MCP {safe_name} {'ok' if ok else 'failed'}",
                "agent": role,
            },
        )
    except Exception:
        pass
