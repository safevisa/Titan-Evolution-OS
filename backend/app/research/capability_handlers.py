"""execute_capability dispatch for research_* (M07b)."""
from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

_RESEARCH_IDS = frozenset({"research_web_search", "research_docs_fetch"})


async def _web_search(query: str, *, max_results: int = 5) -> dict[str, Any]:
    q = (query or "").strip()
    if not q:
        return {"ok": False, "error": "empty_query"}

    if settings.exa_api_key:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.exa.ai/search",
                headers={"x-api-key": settings.exa_api_key, "Content-Type": "application/json"},
                json={"query": q, "numResults": max_results, "contents": {"highlights": True}},
            )
            resp.raise_for_status()
            data = resp.json()
        results = []
        for row in data.get("results") or []:
            if isinstance(row, dict):
                results.append(
                    {
                        "title": row.get("title"),
                        "url": row.get("url"),
                        "snippet": (row.get("highlights") or [row.get("text", "")])[0][:500]
                        if row.get("highlights") or row.get("text")
                        else None,
                    }
                )
        return {"ok": True, "provider": "exa", "query": q, "results": results}

    if settings.perplexityai_api_key:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.perplexityai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "sonar",
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Search the web and summarize with sources for: {q}",
                        }
                    ],
                },
            )
            resp.raise_for_status()
            body = resp.json()
        choice = (body.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        return {
            "ok": True,
            "provider": "perplexity",
            "query": q,
            "answer": msg.get("content", ""),
            "citations": body.get("citations") or [],
        }

    return {
        "ok": False,
        "error": "research_not_configured",
        "message": "Set EXA_API_KEY or PERPLEXITYAI_API_KEY on the server.",
    }


async def _docs_fetch(url: str, *, max_chars: int = 12000) -> dict[str, Any]:
    target = (url or "").strip()
    if not target.startswith(("http://", "https://")):
        return {"ok": False, "error": "invalid_url"}

    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers={"User-Agent": "Titan-Evolution-OS/1.0 (research_docs_fetch)"},
    ) as client:
        resp = await client.get(target)
        resp.raise_for_status()
        text = resp.text

    # Strip tags lightly — agents need readable text, not perfect HTML parsing.
    import re

    plain = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)
    plain = re.sub(r"<style[\s\S]*?</style>", " ", plain, flags=re.I)
    plain = re.sub(r"<[^>]+>", " ", plain)
    plain = re.sub(r"\s+", " ", plain).strip()
    if len(plain) > max_chars:
        plain = plain[:max_chars] + "…"

    return {"ok": True, "url": target, "content": plain, "truncated": len(text) > max_chars}


async def try_research_capability(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    capability_id: str,
    clean_params: dict[str, Any],
) -> tuple[bool, dict[str, Any] | None]:
    if capability_id not in _RESEARCH_IDS:
        return False, None
    _ = session, tenant_id

    if capability_id == "research_web_search":
        query = str(clean_params.get("query") or clean_params.get("q") or "")
        max_results = int(clean_params.get("max_results") or 5)
        max_results = max(1, min(max_results, 10))
        inner = await _web_search(query, max_results=max_results)
        return True, {
            "ok": bool(inner.get("ok")),
            "capability_id": capability_id,
            "data": inner,
            "error": inner.get("error"),
        }

    if capability_id == "research_docs_fetch":
        url = str(clean_params.get("url") or "")
        max_chars = int(clean_params.get("max_chars") or 12000)
        inner = await _docs_fetch(url, max_chars=max_chars)
        return True, {
            "ok": bool(inner.get("ok")),
            "capability_id": capability_id,
            "data": inner,
            "error": inner.get("error"),
        }

    return False, None
