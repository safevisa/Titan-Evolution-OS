"""Researcher Agent — deep-researches a company/contact via LLM."""
from __future__ import annotations

from app.agents.base_agent import BaseAgent, TaskResult, TaskStub
from app.services.goal_entity_extract import extract_entities_from_goal
from app.services.llm import complete_chat

_BAD_COMPANY = frozenset(
    {
        "",
        "unknown",
        "unknown company",
        "未知公司",
        "未指定",
        "n/a",
        "na",
        "none",
        "null",
        "待定",
    },
)


def _norm_company(s: object) -> str:
    if s is None:
        return ""
    t = str(s).strip()
    return "" if t.lower() in _BAD_COMPANY else t


def _label_from_goal(goal: str, max_len: int = 100) -> str:
    g = (goal or "").strip().replace("\n", " ")
    if not g:
        return "Research request"
    return g[:max_len] + ("…" if len(g) > max_len else "")


class ResearcherAgent(BaseAgent):
    role = "researcher"

    _DEFAULT_PROMPT = (
        "You are a Research Agent. You receive a research focus (often a company name) and rich context "
        "that may include the user's full natural-language goal, inferred region, and sector. "
        "If no single company is named, produce useful market/sector/regional research from the context "
        "instead of refusing for 'missing company'. "
        "Always return valid JSON with keys: "
        "summary (string), pain_points (array of strings), opportunities (array of strings), "
        "recommended_approach (string). "
        "Write in the same primary language as the user's goal when obvious; otherwise use English."
    )

    _EXECUTION_APPEND = (
        "\n\n--- Execution requirements ---\n"
        "The user turn includes 'Full user goal' and may include inferred region or sector. "
        "Ground your answer in that goal. If no single legal entity is named, still deliver "
        "actionable guidance for the described market, geography, or sector. "
        "Do not reply with only 'insufficient input data' or placeholder unknown company/country "
        "when the goal already states a market, region, or topic."
    )

    async def run(self, task: TaskStub) -> TaskResult:
        base = await self.get_enhanced_prompt(task) or self._DEFAULT_PROMPT
        prompt = base.rstrip() + self._EXECUTION_APPEND
        inp = task.input or {}
        raw_goal = str(inp.get("goal") or inp.get("criteria") or "").strip()
        company = _norm_company(inp.get("company_name", inp.get("company")))

        ctx_parts: list[str] = []
        if inp.get("context"):
            ctx_parts.append(str(inp["context"]).strip())
        if raw_goal:
            ctx_parts.append(f"Full user goal:\n{raw_goal}")

        if not company:
            extracted = await extract_entities_from_goal(raw_goal)
            if extracted.get("company_name"):
                company = _norm_company(extracted["company_name"])
            reg = extracted.get("country_or_region")
            if isinstance(reg, str) and reg.strip():
                ctx_parts.append(f"Inferred region: {reg.strip()}")
            sec = extracted.get("sector_or_topic")
            if isinstance(sec, str) and sec.strip():
                ctx_parts.append(f"Inferred sector/topic: {sec.strip()}")

        if not company:
            company = _label_from_goal(raw_goal)

        context = "\n\n".join(p for p in ctx_parts if p)

        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": (
                    f"Task type: {task.type}\n"
                    f"Research focus (company or short label): {company}\n"
                    f"Context:\n{context or '(none)'}\n\nReturn JSON only."
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
