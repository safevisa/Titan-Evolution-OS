from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.services.llm import complete_chat

router = APIRouter(prefix="/llm", tags=["llm"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)


class ChatResponse(BaseModel):
    reply: str
    tokens: int


@router.post("/complete", response_model=ChatResponse)
async def llm_complete(body: ChatRequest) -> ChatResponse:
    if not settings.openai_api_key:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured")
    text, tokens = await complete_chat([{"role": "user", "content": body.message}])
    return ChatResponse(reply=text, tokens=tokens)
