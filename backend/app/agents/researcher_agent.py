"""Researcher Agent — deep-researches a company/contact via LLM."""
from __future__ import annotations

from app.agents.base_agent import BaseAgent, TaskResult, TaskStub
from app.services.llm import complete_chat


class ResearcherAgent(BaseAgent):
    role = "researcher"

    _DEFAULT_PROMPT = (
        "You are a Research Agent. Given a company name and optional context, "
        "produce a structured research brief. Return JSON: "
        "{\"summary\": \"...\", \"pain_points\": [...], \"opportunities\": [...], "
        "\"recommended_approach\": \"...\"}"
    )

    async def run(self, task: TaskStub) -> TaskResult:
        prompt = await self.get_enhanced_prompt(task) or self._DEFAULT_PROMPT
        inp = task.input
        company = inp.get("company_name", inp.get("company", "Unknown Company"))
        context = inp.get("context", "")

        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": (
                    f"Task type: {task.type}\n"
                    f"Company: {company}\nContext: {context}\nReturn JSON only."
                ),
            },
        ]
        text, tokens = await complete_chat(messages)

        import json, re

        brief: dict = {"raw": text}
        try:
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                brief = json.loads(m.group())
        except Exception:
            pass

        return TaskResult(output={"brief": brief, "company": company}, token_used=tokens)
