# app/routes/embedding.py
from fastapi import APIRouter, Depends
from app.services.embedding_service import generate_and_store_embeddings
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/embedding", tags=["Embedding"])

@router.post("/generate")
async def generate_embeddings(user=Depends(get_current_user)):
    result = await generate_and_store_embeddings(user.id)
    return result
