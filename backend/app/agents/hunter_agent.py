"""Hunter Agent — searches for leads using Apollo (or LLM fallback)."""
from __future__ import annotations

import json
import re

from app.agents.base_agent import BaseAgent, TaskResult, TaskStub
from app.integrations.executor import execute_capability
from app.services.llm import complete_chat


class HunterAgent(BaseAgent):
    role = "hunter"

    _DEFAULT_PROMPT = (
        "You are a Growth Hunter Agent. Given a search criteria, find and score "
        "potential B2B leads. Return a JSON list of leads with: company_name, "
        "contact_name, email (if available), industry, country, score (0-1), reason."
    )

    async def run(self, task: TaskStub) -> TaskResult:
        prompt = await self.get_enhanced_prompt(task) or self._DEFAULT_PROMPT
        criteria = task.input.get("criteria", task.input)

        cap_result = await execute_capability(
            "apollo_search",
            {
                "criteria": criteria,
                "_correlation_id": task.id,
                "_actor": f"agent:{self.agent_id}",
            },
            tenant_id=self.tenant_id,
        )
        if cap_result.get("ok") and cap_result.get("data"):
            leads = cap_result["data"]
            if isinstance(leads, list) and leads:
                return TaskResult(output={"leads": leads}, token_used=0)

        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": (
                    f"Task type: {task.type}\n"
                    f"Search criteria: {criteria}\n"
                    "Return JSON only: {\"leads\": [{...}]}"
                ),
            },
        ]
        text, tokens = await complete_chat(messages)

        leads: list = []
        try:
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                leads = json.loads(m.group())["leads"]
        except Exception:
            leads = [{"raw": text}]

        return TaskResult(output={"leads": leads}, token_used=tokens)
