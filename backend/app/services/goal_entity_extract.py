"""LLM-assisted extraction of company / region / topic from free-text user goals."""
from __future__ import annotations

import json
import re
from typing import Any

from app.services.llm import complete_chat

_EXTRACT_SYSTEM = (
    "You extract structured fields from a business user's goal (any language). "
    "Return JSON only with keys: "
    "company_name (string|null), "
    "country_or_region (string|null), "
    "sector_or_topic (string|null). "
    "Rules: "
    "If the user asks for a market scan, a list, or ICP without naming one legal entity, set company_name to null. "
    "Infer country_or_region from phrases like MENA, Middle East, 中东, North America, EU, UK, US, 美国, 中国. "
    "sector_or_topic should capture industry or intent (e.g. payment, fintech, SaaS). "
    "No markdown, no commentary outside JSON."
)


async def extract_entities_from_goal(goal: str) -> dict[str, Any]:
    goal = (goal or "").strip()
    if not goal or len(goal) > 12000:
        return {}
    messages = [
        {"role": "system", "content": _EXTRACT_SYSTEM},
        {"role": "user", "content": goal[:8000]},
    ]
    try:
        text, _ = await complete_chat(messages, temperature=0.1)
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            return {}
        data = json.loads(m.group())
        if not isinstance(data, dict):
            return {}
        out: dict[str, Any] = {}
        for k in ("company_name", "country_or_region", "sector_or_topic"):
            v = data.get(k)
            if isinstance(v, str) and v.strip():
                out[k] = v.strip()
            elif v is None:
                out[k] = None
        return out
    except Exception:
        return {}
