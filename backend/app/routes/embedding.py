# app/routes/embedding.py
from fastapi import APIRouter, Depends, HTTPException
from app.services.embedding import generate_and_store_embeddings
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/embedding", tags=["Embedding"])

@router.post("/generate")
async def generate_embeddings(user=Depends(get_current_user)):
    # Generate and store embeding fort he user
    try:
        result = await generate_and_store_embeddings(user.id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed {str(e)}")

