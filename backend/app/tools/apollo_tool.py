"""Apollo.io search — requires APOLLO_API_KEY."""

from __future__ import annotations

from typing import Any, Optional

import httpx

from app.core.config import settings

APOLLO_BASE = "https://api.apollo.io/api/v1"


async def apollo_search_people(
    *,
    q_keywords: Optional[str] = None,
    person_titles: Optional[list[str]] = None,
    page: int = 1,
    per_page: int = 10,
) -> dict[str, Any]:
    if not settings.apollo_api_key:
        raise RuntimeError("APOLLO_API_KEY is not configured")
    payload: dict[str, Any] = {"page": page, "per_page": per_page}
    if q_keywords:
        payload["q_keywords"] = q_keywords
    if person_titles:
        payload["person_titles[]"] = person_titles
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": settings.apollo_api_key,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{APOLLO_BASE}/mixed_people/search", json=payload, headers=headers)
        r.raise_for_status()
        return r.json()
