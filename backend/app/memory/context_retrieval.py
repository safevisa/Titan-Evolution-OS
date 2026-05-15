"""Inject auto-synced context into agent prompts."""
from __future__ import annotations

from app.memory.long_term import search_sync_context
from app.memory.token_compress import compress_for_llm


async def fetch_sync_context_block(
    *,
    tenant_id: str,
    query: str,
    max_tokens: int = 4096,
) -> str:
    hits = await search_sync_context(
        tenant_id=tenant_id,
        query=query,
        top_k=12,
    )
    if not hits:
        return ""

    max_chars = max(500, max_tokens * 4)
    lines: list[str] = []
    used = 0
    for h in hits:
        title = str(h.get("title") or "")
        summary = compress_for_llm(str(h.get("summary") or ""), max_chars=2000)
        source = str(h.get("source") or "?")
        occurred = str(h.get("occurred_at") or "")
        line = f"- [{source}] {title} ({occurred})\n  {summary}"
        if used + len(line) > max_chars:
            break
        lines.append(line)
        used += len(line)

    if not lines:
        return ""
    return "## Synced context (auto-fetched)\n" + "\n".join(lines)
