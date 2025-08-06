# routes/question.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.question import QuestionRequest, QuestionResponse
from app.services.qa_service import qa_service
from app.dependencies.auth import get_current_user
import logging


router = APIRouter(tags=["Questions"])

logger = logging.getLogger(__name__)


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(req: QuestionRequest, user=Depends(get_current_user)):
    """
    Ask a question and get an answer based on uploaded documents.
    """
    try:

        logger.info(f"Received question: {req.question}")

        if not req.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # qa_service = ask_question()

         # If context from search results is provided, use that
        if req.context and len(req.context) > 0:
            context_dicts = [
                {
                    "id": item.id,
                    "title": item.title,
                    "section": item.section,
                    "description": item.description,
                    "similarity_score": item.similarity_score
                }
                for item in req.context
            ]

            result = await qa_service.answer_question_with_context(
                question=req.question,
                search_results=context_dicts,
                user_id=user.id
            )
        else:
            result = {
                "answer": "Please provide search results or context to answer your question.",
                "confidence_score": 0.0,
                "source_document": "none"
            }
            
        return QuestionResponse(
            answer=result["answer"],
            confidence_score=result["confidence_score"],
            source_document=result["source_document"]
        )
    
    except Exception as e:
        logger.error(f"Error in ask_question endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")


@router.get("/documents")
async def list_qa_documents(user=Depends(get_current_user)):
    """List all documents available for questioning."""
    try:
        from app.services.document_service import get_user_documents
        documents = await get_user_documents(user.id)
        
        return {
            "documents": [
                {
                    "id": doc.get("document_id") or str(doc.get("id", "")),
                    "filename": doc.get("filename", ""),
                    "upload_date": doc.get("upload_date", ""),
                    "summary": doc.get("summary", "")[:200] + "..." if doc.get("summary", "") else ""
                }
                for doc in documents
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching documents: {str(e)}")
