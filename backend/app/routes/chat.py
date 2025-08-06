# Chat with DialoGPT endpoint

from fastapi import APIRouter, Depends
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat_with_bot
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest, user=Depends(get_current_user)):
    response_text = chat_with_bot(req.message)
    return ChatResponse(reply=response_text)
