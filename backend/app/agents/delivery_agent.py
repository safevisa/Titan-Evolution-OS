"""Delivery Agent — compiles and formats final deliverable from task outputs."""
from __future__ import annotations

from app.agents.base_agent import BaseAgent, TaskResult, TaskStub
from app.services.llm import complete_chat


class DeliveryAgent(BaseAgent):
    role = "delivery"

    _DEFAULT_PROMPT = (
        "You are a Delivery Agent. Compile the provided inputs into a clear, "
        "professional summary report in Markdown. Include: Executive Summary, "
        "Key Findings, Recommended Next Steps."
    )

    async def run(self, task: TaskStub) -> TaskResult:
        prompt = await self.get_enhanced_prompt(task) or self._DEFAULT_PROMPT
        inp = task.input
        content = inp.get("content", str(inp))

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Task type: {task.type}\nInput data:\n{content}"},
        ]
        text, tokens = await complete_chat(messages)

        return TaskResult(output={"report_md": text}, token_used=tokens)
