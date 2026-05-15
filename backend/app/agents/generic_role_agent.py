"""LLM-only agent for arbitrary corporate roles — uses tenant prompts + skill SOPs."""
from __future__ import annotations

import json
from typing import Any
from app.agents.agent_tool_runner import parse_agent_json_output, run_agent_with_capability_tools
from app.agents.base_agent import BaseAgent, TaskResult, TaskStub
from app.core.database import AsyncSessionLocal


class GenericRoleAgent(BaseAgent):
    """Runs any `Agent.role` through the shared LLM path with memory/skill enrichment."""

    def __init__(self, agent_id: str, tenant_id: str, current_prompt: str, *, role_key: str) -> None:
        super().__init__(agent_id, tenant_id, current_prompt)
        self.role = role_key

    async def run(self, task: TaskStub) -> TaskResult:
        prompt = await self.get_enhanced_prompt(task) or self.current_prompt
        payload = json.dumps(task.input, ensure_ascii=False, default=str)[:12000]

        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": (
                    f"Your role id: {self.role}\n"
                    f"Task type: {task.type}\n"
                    f"Input JSON:\n{payload}\n\n"
                    "You may call integration tools when needed (Slack, email, CRM, etc.). "
                    "After tool use, respond with JSON only: "
                    '{"summary": "string", "artifacts": {}, "next_actions": []}\n'
                    "Optional: task input may include invoke_capability (catalog id) and "
                    "invoke_capability_params (object); those run after the JSON response."
                ),
            },
        ]
        async with AsyncSessionLocal() as session:
            text, tokens, tool_results = await run_agent_with_capability_tools(
                tenant_id=self.tenant_id,
                role=self.role,
                messages=messages,
                session=session,
                correlation_id=task.id,
                actor=f"agent:{self.agent_id}",
            )

        out = parse_agent_json_output(text)
        if tool_results:
            out["tool_results"] = tool_results

        invoke = task.input.get("invoke_capability")
        if isinstance(invoke, str) and invoke.strip():
            from app.integrations.executor import execute_capability

            raw_params = task.input.get("invoke_capability_params")
            cap_params = dict(raw_params) if isinstance(raw_params, dict) else {}
            cap_params.setdefault("_correlation_id", task.id)
            cap_params.setdefault("_actor", f"agent:{self.agent_id}")
            out["capability_result"] = await execute_capability(
                invoke.strip(),
                cap_params,
                tenant_id=self.tenant_id,
            )

        return TaskResult(output=out, token_used=tokens)
