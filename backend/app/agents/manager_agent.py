"""Manager Agent — decomposes goals into sub-tasks for other agents."""
from __future__ import annotations

from app.agents.base_agent import BaseAgent, TaskResult, TaskStub
from app.services.llm import complete_chat


class ManagerAgent(BaseAgent):
    role = "manager"

    _DEFAULT_PROMPT = (
        "You are an Evolution Manager Agent. Break down the given goal into "
        "an ordered list of sub-tasks, each assigned to one of: hunter, researcher, "
        "outreach, delivery. Return JSON: "
        "{\"plan\": [{\"step\": 1, \"role\": \"...\", \"task_type\": \"...\", "
        "\"description\": \"...\"}]}"
    )

    async def run(self, task: TaskStub) -> TaskResult:
        prompt = await self.get_enhanced_prompt(task) or self._DEFAULT_PROMPT
        goal = task.input.get("goal", str(task.input))

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Task type: {task.type}\nGoal: {goal}\nReturn JSON only."},
        ]
        text, tokens = await complete_chat(messages)

        import json, re

        plan: list = []
        try:
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                plan = json.loads(m.group()).get("plan", [])
        except Exception:
            plan = [{"raw": text}]

        return TaskResult(output={"plan": plan}, token_used=tokens)
