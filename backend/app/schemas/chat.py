from pydantic import BaseModel
from typing import List


class ChatMessage(BaseModel):
    sender: str  # "user" or "bot"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


class ChatResponse(BaseModel):
    reply: str
