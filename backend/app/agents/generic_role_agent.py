"""LLM-only agent for arbitrary corporate roles — uses tenant prompts + skill SOPs."""
from __future__ import annotations

import json
from typing import Any
from uuid import UUID
from app.agents.agent_tool_runner import parse_agent_json_output, run_agent_with_capability_tools
from app.agents.base_agent import BaseAgent, TaskResult, TaskStub
from app.agents.discipline_harness import (
    discipline_system_addon,
    intent_gate_heuristic,
    max_tool_rounds_for_mode,
    resolve_harness_mode,
    role_category,
)
from app.core.database import AsyncSessionLocal
from app.models.domain import Tenant


class GenericRoleAgent(BaseAgent):
    """Runs any `Agent.role` through the shared LLM path with memory/skill enrichment."""

    def __init__(self, agent_id: str, tenant_id: str, current_prompt: str, *, role_key: str) -> None:
        super().__init__(agent_id, tenant_id, current_prompt)
        self.role = role_key

    async def run(self, task: TaskStub) -> TaskResult:
        prompt = await self.get_enhanced_prompt(task) or self.current_prompt
        payload = json.dumps(task.input, ensure_ascii=False, default=str)[:12000]

        task_input = task.input if isinstance(task.input, dict) else {}
        harness_mode = "standard"
        goal_text = str(task_input.get("goal") or task_input.get("criteria") or "")
        intent = intent_gate_heuristic(goal_text)
        category = role_category(self.role)
        system_prompt = prompt

        messages = [
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
            tenant_row = await session.get(Tenant, UUID(str(self.tenant_id)))
            tenant_cfg = (
                tenant_row.config
                if tenant_row and isinstance(tenant_row.config, dict)
                else None
            )
            harness_mode = resolve_harness_mode(task_input, tenant_cfg)
            harness_block = discipline_system_addon(
                mode=harness_mode,
                category=category,
                intent=intent,
            )
            system_prompt = f"{prompt}\n\n{harness_block}"
            messages.insert(0, {"role": "system", "content": system_prompt})
            text, tokens, tool_results = await run_agent_with_capability_tools(
                tenant_id=self.tenant_id,
                role=self.role,
                messages=messages,
                session=session,
                correlation_id=task.id,
                actor=f"agent:{self.agent_id}",
                max_tool_rounds=max_tool_rounds_for_mode(harness_mode),
            )

        out = parse_agent_json_output(text)
        if tool_results:
            out["tool_results"] = tool_results

        from app.agents.hashline_edit import is_code_task as _is_code_task
        from app.agents.hashline_edit import parse_hashline_edits, verify_and_apply

        if _is_code_task(task.type):
            raw_edits = ""
            artifacts = out.get("artifacts")
            if isinstance(artifacts, dict):
                raw_edits = str(artifacts.get("hashline_edits") or artifacts.get("edits") or "")
            if not raw_edits and isinstance(out.get("summary"), str):
                raw_edits = out["summary"]
            file_map = task_input.get("file_contents")
            if isinstance(file_map, dict) and raw_edits:
                edits = parse_hashline_edits(raw_edits)
                if edits:
                    str_map = {str(k): str(v) for k, v in file_map.items()}
                    updated, audit = verify_and_apply(str_map, edits)
                    out["hashline_audit"] = audit
                    out["file_contents_applied"] = updated
                    out["hashline_all_ok"] = all(r.get("ok") for r in audit)

        cu_instruction = task_input.get("computer_use_instruction")
        if (
            harness_mode == "ultrawork"
            and isinstance(cu_instruction, str)
            and cu_instruction.strip()
        ):
            from app.integrations.executor import execute_capability

            out["computer_use_result"] = await execute_capability(
                "computer_use_submit",
                {
                    "instruction": cu_instruction.strip(),
                    "task_id": task.id,
                    "_correlation_id": task.id,
                    "_actor": f"agent:{self.agent_id}",
                },
                tenant_id=self.tenant_id,
            )

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
