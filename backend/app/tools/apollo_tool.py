"""Apollo.io people/company search — gracefully skips when key not configured."""
from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings


async def search_leads(criteria: dict) -> list[dict]:
    """Returns list of leads from Apollo. Empty list if key not set or request fails."""
    if not settings.apollo_api_key:
        return []

    payload = {
        "api_key": settings.apollo_api_key,
        "q_organization_domains": criteria.get("domains", []),
        "person_titles": criteria.get("titles", ["CEO", "Founder", "Head of Partnerships"]),
        "organization_industry_tag_ids": criteria.get("industry_ids", []),
        "page": 1,
        "per_page": criteria.get("limit", 10),
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.apollo.io/v1/mixed_people/search",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            people = data.get("people", [])
            return [
                {
                    "company_name": p.get("organization", {}).get("name", ""),
                    "contact_name": p.get("name", ""),
                    "email": p.get("email", ""),
                    "title": p.get("title", ""),
                    "industry": p.get("organization", {}).get("industry", ""),
                    "country": p.get("organization", {}).get("country", ""),
                    "score": 0.7,
                }
                for p in people
            ]
    except Exception:
        return []


async def apollo_search_people(**kwargs: Any) -> list[dict]:
    """Adapter for `tool_registry` / integrations — forwards to `search_leads`."""
    criteria: dict[str, Any] = {
        "domains": kwargs.get("domains", []),
        "titles": kwargs.get("titles", []),
        "industry_ids": kwargs.get("industry_ids", []),
        "limit": kwargs.get("limit", 10),
    }
    extra = kwargs.get("criteria")
    if isinstance(extra, dict):
        for k in ("domains", "titles", "industry_ids", "limit"):
            if k in extra and extra[k] is not None:
                criteria[k] = extra[k]
    return await search_leads(criteria)
