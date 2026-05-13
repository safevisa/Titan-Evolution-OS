"""LiteLLM entry — set OPENAI_API_KEY (or provider keys) in environment."""

from __future__ import annotations

from typing import Any

from litellm import acompletion

from app.core.config import settings


async def complete_chat(
    messages: list[dict[str, str]],
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
) -> tuple[str, int]:
    """Returns (assistant_text, total_tokens_or_0)."""
    if settings.openai_api_key:
        import os

        os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)

    resp: Any = await acompletion(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    text = resp.choices[0].message.content or ""
    usage = getattr(resp, "usage", None)
    tokens = int(getattr(usage, "total_tokens", 0) or 0) if usage else 0
    return text, tokens
