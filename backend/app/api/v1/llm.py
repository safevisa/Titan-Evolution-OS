from typing import Optional

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.services.llm import complete_chat, list_llm_providers

router = APIRouter(prefix="/llm", tags=["llm"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    model: Optional[str] = Field(default=None, max_length=200)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)


class ChatResponse(BaseModel):
    reply: str
    tokens: int


@router.post("/complete", response_model=ChatResponse)
async def llm_complete(body: ChatRequest) -> ChatResponse:
    if not any(p["configured"] for p in list_llm_providers()):
        raise HTTPException(status_code=503, detail="No LLM provider API key is configured")
    text, tokens = await complete_chat(
        [{"role": "user", "content": body.message}],
        model=body.model or settings.litellm_default_model,
        temperature=body.temperature,
    )
    return ChatResponse(reply=text, tokens=tokens)


@router.get("/providers")
async def llm_providers() -> dict:
    return {
        "default_model": settings.litellm_default_model,
        "providers": list_llm_providers(),
    }
