"""Run LLM with OpenAI-style tools mapped to execute_capability."""
from __future__ import annotations

import json
import re
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.agent_capabilities import list_agent_capabilities
from app.integrations.agent_tool_bridge import (
    capabilities_to_openai_tools,
    parse_capability_tool_call,
)
from app.integrations.connections_repo import list_providers_for_tenant
from app.integrations.executor import execute_capability
from app.models.domain import Tenant
from app.services.llm import complete_chat, complete_chat_with_tools


async def load_tenant_capability_context(
    session: AsyncSession,
    tenant_id: UUID,
) -> tuple[dict[str, Any] | None, frozenset[str], str]:
    tenant = await session.get(Tenant, tenant_id)
    cfg = tenant.config if tenant and isinstance(tenant.config, dict) else None
    provs = await list_providers_for_tenant(session, tenant_id)
    plan = str(tenant.plan) if tenant and tenant.plan else "starter"
    return cfg, provs, plan


async def run_agent_with_capability_tools(
    *,
    tenant_id: str,
    role: str,
    messages: list[dict[str, Any]],
    session: AsyncSession | None,
    correlation_id: str,
    actor: str,
    max_tool_rounds: int = 3,
) -> tuple[str, int, list[dict[str, Any]]]:
    """
    Returns (final_text, total_tokens, tool_results).
    Falls back to plain complete_chat when no executable tools are available.
    """
    tid = UUID(str(tenant_id))
    if session is not None:
        tenant_config, connection_providers, _plan = await load_tenant_capability_context(session, tid)
    else:
        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as s:
            tenant_config, connection_providers, _plan = await load_tenant_capability_context(s, tid)

    caps = list_agent_capabilities(
        role=role,
        tenant_config=tenant_config,
        connection_providers=connection_providers,
    )
    tools, name_to_ref = capabilities_to_openai_tools(caps, only_executable=True)
    if not tools:
        text, tokens = await complete_chat(messages)
        return text, tokens, []

    tool_results: list[dict[str, Any]] = []
    total_tokens = 0
    convo = list(messages)

    for _ in range(max_tool_rounds):
        text, tokens, tool_calls = await complete_chat_with_tools(convo, tools=tools)
        total_tokens += tokens
        if not tool_calls:
            return text, total_tokens, tool_results

        convo.append({"role": "assistant", "content": text or "", "tool_calls": tool_calls})
        for tc in tool_calls:
            fn = tc.get("function") or {}
            name = str(fn.get("name", ""))
            raw_args = fn.get("arguments", "{}")
            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args or {})
            except json.JSONDecodeError:
                args = {}
            parsed = parse_capability_tool_call(name, args, name_to_ref=name_to_ref)
            if not parsed:
                tool_results.append({"tool": name, "ok": False, "error": "unknown_tool"})
                convo.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.get("id", name),
                        "content": json.dumps({"ok": False, "error": "unknown_tool"}),
                    }
                )
                continue
            cap_ref, params = parsed
            params = dict(params)
            params.setdefault("_correlation_id", correlation_id)
            params.setdefault("_actor", actor)
            result = await execute_capability(
                cap_ref,
                params,
                tenant_id=tenant_id,
                db=session,
            )
            tool_results.append({"capability_ref": cap_ref, "result": result})
            convo.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.get("id", name),
                    "content": json.dumps(result, ensure_ascii=False, default=str)[:8000],
                }
            )

    text, tokens = await complete_chat(convo)
    total_tokens += tokens
    return text, total_tokens, tool_results


def parse_agent_json_output(text: str) -> dict[str, Any]:
    out: dict[str, Any] = {"raw": text}
    try:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            out = json.loads(m.group())
    except Exception:
        pass
    return out
