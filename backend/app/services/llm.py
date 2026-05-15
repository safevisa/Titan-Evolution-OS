"""LiteLLM entry — configure provider keys in .env and choose models by id."""

from __future__ import annotations

import os
from typing import Any

from litellm import acompletion

from app.core.config import settings

PROVIDER_CATALOG: dict[str, dict[str, object]] = {
    "openai": {
        "env": ["OPENAI_API_KEY"],
        "models": ["gpt-4o-mini", "gpt-4o", "o3-mini"],
    },
    "anthropic": {
        "env": ["ANTHROPIC_API_KEY"],
        "models": ["anthropic/claude-3-5-sonnet-20241022", "anthropic/claude-3-5-haiku-20241022"],
    },
    "google": {
        "env": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
        "models": ["gemini/gemini-1.5-flash", "gemini/gemini-1.5-pro"],
    },
    "groq": {
        "env": ["GROQ_API_KEY"],
        "models": ["groq/llama-3.1-70b-versatile", "groq/llama-3.1-8b-instant"],
    },
    "deepseek": {
        "env": ["DEEPSEEK_API_KEY"],
        "models": [
            "deepseek/deepseek-v4-pro",
            "deepseek/deepseek-v4-flash",
            "deepseek/deepseek-v3.2",
            "deepseek/deepseek-chat",
            "deepseek/deepseek-reasoner",
        ],
    },
    "mistral": {
        "env": ["MISTRAL_API_KEY"],
        "models": ["mistral/mistral-large-latest", "mistral/codestral-latest"],
    },
    "cohere": {
        "env": ["COHERE_API_KEY"],
        "models": ["command-r-plus", "command-r"],
    },
    "togetherai": {
        "env": ["TOGETHERAI_API_KEY"],
        "models": ["together_ai/meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"],
    },
    "openrouter": {
        "env": ["OPENROUTER_API_KEY"],
        "models": ["openrouter/openai/gpt-4o-mini", "openrouter/anthropic/claude-3.5-sonnet"],
    },
    "xai": {
        "env": ["XAI_API_KEY"],
        "models": ["xai/grok-2-latest"],
    },
    "perplexity": {
        "env": ["PERPLEXITYAI_API_KEY"],
        "models": ["perplexity/llama-3.1-sonar-large-128k-online"],
    },
    "dashscope": {
        "env": ["DASHSCOPE_API_KEY"],
        "models": [
            "dashscope/qwen-max",
            "dashscope/qwen-plus",
            "dashscope/qwen-turbo",
        ],
    },
    "moonshot": {
        "env": ["MOONSHOT_API_KEY"],
        "models": ["moonshot/moonshot-v1-8k", "moonshot/moonshot-v1-32k"],
    },
    "zhipuai": {
        "env": ["ZHIPUAI_API_KEY"],
        "models": ["zhipuai/glm-4"],
    },
    "baichuan": {
        "env": ["BAICHUAN_API_KEY"],
        "models": ["baichuan/baichuan4"],
    },
    "siliconflow": {
        "env": ["SILICONFLOW_API_KEY"],
        "models": [
            "siliconflow/Qwen/Qwen2.5-72B-Instruct",
            "siliconflow/deepseek-ai/DeepSeek-V3",
        ],
    },
    "minimax": {
        "env": ["MINIMAX_API_KEY"],
        "models": [
            "minimax/MiniMax-M2.5",
            "minimax/MiniMax-M2.1",
        ],
    },
    "volcengine": {
        "env": ["VOLCENGINE_API_KEY", "ARK_API_KEY"],
        "models": [
            "volcengine/doubao-seed-2-0-pro-260215",
            "volcengine/doubao-seed-2-0-lite-260215",
        ],
    },
    "azure": {
        "env": ["AZURE_API_KEY", "AZURE_API_BASE", "AZURE_API_VERSION"],
        "models": ["azure/<deployment-name>"],
    },
    "bedrock": {
        "env": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION_NAME"],
        "models": ["bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0"],
    },
}


def _set_env_if_configured(env_name: str, value: str | None) -> None:
    if value:
        os.environ.setdefault(env_name, value)


def configure_llm_environment() -> None:
    _set_env_if_configured("OPENAI_API_KEY", settings.openai_api_key)
    _set_env_if_configured("ANTHROPIC_API_KEY", settings.anthropic_api_key)
    google_key = settings.google_api_key or settings.gemini_api_key
    _set_env_if_configured("GOOGLE_API_KEY", google_key)
    _set_env_if_configured("GEMINI_API_KEY", google_key)
    _set_env_if_configured("GROQ_API_KEY", settings.groq_api_key)
    _set_env_if_configured("DEEPSEEK_API_KEY", settings.deepseek_api_key)
    _set_env_if_configured("DEEPSEEK_API_BASE", settings.deepseek_api_base)
    _set_env_if_configured("MISTRAL_API_KEY", settings.mistral_api_key)
    _set_env_if_configured("COHERE_API_KEY", settings.cohere_api_key)
    _set_env_if_configured("TOGETHERAI_API_KEY", settings.togetherai_api_key)
    _set_env_if_configured("OPENROUTER_API_KEY", settings.openrouter_api_key)
    _set_env_if_configured("XAI_API_KEY", settings.xai_api_key)
    _set_env_if_configured("PERPLEXITYAI_API_KEY", settings.perplexityai_api_key)
    _set_env_if_configured("DASHSCOPE_API_KEY", settings.dashscope_api_key)
    _set_env_if_configured("MOONSHOT_API_KEY", settings.moonshot_api_key)
    _set_env_if_configured("ZHIPUAI_API_KEY", settings.zhipuai_api_key)
    _set_env_if_configured("BAICHUAN_API_KEY", settings.baichuan_api_key)
    _set_env_if_configured("SILICONFLOW_API_KEY", settings.siliconflow_api_key)
    _set_env_if_configured("MINIMAX_API_KEY", settings.minimax_api_key)
    _set_env_if_configured("MINIMAX_API_BASE", settings.minimax_api_base)
    vk = settings.volcengine_api_key or settings.ark_api_key
    if vk:
        os.environ.setdefault("VOLCENGINE_API_KEY", vk)
        os.environ.setdefault("ARK_API_KEY", vk)
    _set_env_if_configured("AZURE_API_KEY", settings.azure_api_key)
    _set_env_if_configured("AZURE_API_BASE", settings.azure_api_base)
    _set_env_if_configured("AZURE_API_VERSION", settings.azure_api_version)
    _set_env_if_configured("AWS_ACCESS_KEY_ID", settings.aws_access_key_id)
    _set_env_if_configured("AWS_SECRET_ACCESS_KEY", settings.aws_secret_access_key)
    _set_env_if_configured("AWS_REGION_NAME", settings.aws_region_name)


def list_llm_providers() -> list[dict[str, object]]:
    configure_llm_environment()
    providers: list[dict[str, object]] = []
    for provider, info in PROVIDER_CATALOG.items():
        env_names = list(info["env"])  # type: ignore[arg-type]
        if provider == "azure":
            configured = all(bool(os.getenv(env_name)) for env_name in env_names)
        else:
            configured = any(bool(os.getenv(env_name)) for env_name in env_names)
        providers.append(
            {
                "provider": provider,
                "configured": configured,
                "required_env": env_names,
                "models": info["models"],
            }
        )
    return providers


async def complete_chat(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float = 0.2,
) -> tuple[str, int]:
    """Returns (assistant_text, total_tokens_or_0)."""
    configure_llm_environment()

    resp: Any = await acompletion(
        model=model or settings.litellm_default_model,
        messages=messages,
        temperature=temperature,
    )
    text = resp.choices[0].message.content or ""
    usage = getattr(resp, "usage", None)
    tokens = int(getattr(usage, "total_tokens", 0) or 0) if usage else 0
    return text, tokens


def _message_tool_calls(msg: Any) -> list[dict[str, Any]]:
    raw = getattr(msg, "tool_calls", None) or []
    out: list[dict[str, Any]] = []
    for tc in raw:
        fn = getattr(tc, "function", None)
        if fn is None:
            continue
        out.append(
            {
                "id": getattr(tc, "id", "") or "",
                "type": "function",
                "function": {
                    "name": getattr(fn, "name", "") or "",
                    "arguments": getattr(fn, "arguments", "{}") or "{}",
                },
            }
        )
    return out


async def complete_chat_with_tools(
    messages: list[dict[str, Any]],
    *,
    tools: list[dict[str, Any]],
    model: str | None = None,
    temperature: float = 0.2,
) -> tuple[str, int, list[dict[str, Any]]]:
    """Returns (assistant_text, total_tokens_or_0, tool_calls)."""
    configure_llm_environment()

    resp: Any = await acompletion(
        model=model or settings.litellm_default_model,
        messages=messages,
        tools=tools,
        temperature=temperature,
    )
    msg = resp.choices[0].message
    text = getattr(msg, "content", None) or ""
    usage = getattr(resp, "usage", None)
    tokens = int(getattr(usage, "total_tokens", 0) or 0) if usage else 0
    return text, tokens, _message_tool_calls(msg)
