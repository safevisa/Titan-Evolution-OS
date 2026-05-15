"""Outreach Agent — writes personalised emails via LLM and sends via Resend."""
from __future__ import annotations

import json
import re

from app.agents.base_agent import BaseAgent, TaskResult, TaskStub
from app.integrations.executor import execute_capability
from app.services.llm import complete_chat


class OutreachAgent(BaseAgent):
    role = "outreach"

    _DEFAULT_PROMPT = (
        "You are an Outreach Agent. Write a personalised, concise cold email "
        "(≤120 words) for the given contact. Be specific, avoid clichés. "
        "Return JSON: {\"subject\": \"...\", \"body\": \"...\"}"
    )

    async def run(self, task: TaskStub) -> TaskResult:
        prompt = await self.get_enhanced_prompt(task) or self._DEFAULT_PROMPT
        inp = task.input

        to_email: str = inp.get("email", "")
        contact = inp.get("contact_name", "there")
        company = inp.get("company_name", "your company")
        context = inp.get("context", "")

        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": (
                    f"Task type: {task.type}\n"
                    f"Contact: {contact} at {company}\n"
                    f"Extra context: {context}\n"
                    "Return JSON only."
                ),
            },
        ]
        text, tokens = await complete_chat(messages)

        subject, body = "Follow-up", text
        try:
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                d = json.loads(m.group())
                subject = d.get("subject", subject)
                body = d.get("body", body)
        except Exception:
            pass

        sent = False
        if to_email:
            cap_result = await execute_capability(
                "resend_email",
                {
                    "to": to_email,
                    "subject": subject,
                    "body": body,
                    "_correlation_id": task.id,
                    "_actor": f"agent:{self.agent_id}",
                },
                tenant_id=self.tenant_id,
            )
            sent = bool(cap_result.get("ok") and cap_result.get("data"))

        return TaskResult(
            output={"subject": subject, "body": body, "sent": sent, "to": to_email},
            token_used=tokens,
        )
