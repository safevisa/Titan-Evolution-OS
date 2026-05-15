"""LiteLLM / OpenAI-style tool definitions from tenant-visible capabilities."""
from __future__ import annotations

import base64
from typing import Any


def _tool_name_for_ref(capability_ref: str) -> str:
    slug = base64.urlsafe_b64encode(capability_ref.encode("utf-8")).decode("ascii").rstrip("=")
    slug = slug.replace("-", "_")
    return f"cap_{slug}"[:64]


def capabilities_to_openai_tools(
    capabilities: list[dict[str, Any]],
    *,
    only_executable: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """
    Build tool schemas for LLM tool-calling from list_agent_capabilities() output.
    Returns (tools_for_llm, tool_name -> capability_ref).
    """
    tools: list[dict[str, Any]] = []
    name_to_ref: dict[str, str] = {}
    for cap in capabilities:
        if only_executable and not cap.get("can_execute_now"):
            continue
        cid = str(cap.get("id", ""))
        cref = str(cap.get("capability_ref") or cid)
        if not cid:
            continue
        tname = _tool_name_for_ref(cref)
        name_to_ref[tname] = cref
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": tname,
                    "description": str(cap.get("description") or cap.get("display_name") or cid)[:512],
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "params": {
                                "type": "object",
                                "description": f"Parameters for capability {cref}",
                                "additionalProperties": True,
                            },
                        },
                        "required": ["params"],
                    },
                },
            }
        )
    return tools, name_to_ref


def parse_capability_tool_call(
    tool_name: str,
    arguments: dict[str, Any],
    *,
    name_to_ref: dict[str, str],
) -> tuple[str, dict[str, Any]] | None:
    """Map OpenAI tool name back to (capability_ref, params)."""
    cap_ref = name_to_ref.get(tool_name)
    if not cap_ref:
        return None
    params = arguments.get("params") if isinstance(arguments.get("params"), dict) else arguments
    return cap_ref, dict(params or {})
