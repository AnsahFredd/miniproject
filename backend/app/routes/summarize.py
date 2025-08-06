# Summarize endpoint

from fastapi import APIRouter, Depends
from app.schemas.summarization import SummarizationRequest, SummarizationResponse
from app.services.summarization_service import summarize_text
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/summarize", tags=["Summarization"])


@router.post("/", response_model=SummarizationResponse)
async def summarize(req: SummarizationRequest, user=Depends(get_current_user)):
    return await summarize_text(req.text)
