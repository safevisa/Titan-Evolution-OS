"""Hunter Agent — searches for leads using Apollo (or LLM fallback)."""
from __future__ import annotations

from app.agents.base_agent import BaseAgent, TaskResult, TaskStub
from app.services.llm import complete_chat
from app.tools.apollo_tool import search_leads


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

        # Try Apollo first; fall back to LLM simulation
        apollo_leads = await search_leads(criteria)

        if apollo_leads:
            return TaskResult(output={"leads": apollo_leads}, token_used=0)

        # LLM fallback — generates plausible example leads for demo/cold-start
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

        import json, re

        leads: list = []
        try:
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                leads = json.loads(m.group())["leads"]
        except Exception:
            leads = [{"raw": text}]

        return TaskResult(output={"leads": leads}, token_used=tokens)
