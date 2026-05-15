"""LLM-only agent for arbitrary corporate roles — uses tenant prompts + skill SOPs."""
from __future__ import annotations

import json
import re
from typing import Any

from app.agents.base_agent import BaseAgent, TaskResult, TaskStub
from app.services.llm import complete_chat


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
                    "Optional: task input may include invoke_capability (catalog id) and "
                    "invoke_capability_params (object); those run after this JSON response.\n"
                    "Respond with JSON only: "
                    '{"summary": "string", "artifacts": {}, "next_actions": []}'
                ),
            },
        ]
        text, tokens = await complete_chat(messages)

        out: dict[str, Any] = {"raw": text}
        try:
            m = re.search(r"\{[\s\S]*\}", text)
            if m:
                out = json.loads(m.group())
        except Exception:
            pass

        invoke = task.input.get("invoke_capability")
        if isinstance(invoke, str) and invoke.strip():
            from app.integrations.executor import execute_capability

            raw_params = task.input.get("invoke_capability_params")
            cap_params = raw_params if isinstance(raw_params, dict) else {}
            out["capability_result"] = await execute_capability(
                invoke.strip(),
                cap_params,
                tenant_id=self.tenant_id,
            )

        return TaskResult(output=out, token_used=tokens)
