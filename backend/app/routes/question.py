# routes/question.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.question import QuestionRequest, QuestionResponse
from app.services.qa_service import qa_service
from app.dependencies.auth import get_current_user
from app.models.document import AcceptedDocument
from datetime import datetime
from bson import ObjectId
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

        result = None
        source_document_ids = []

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

            # Extract document IDs from context for tracking
            source_document_ids = [item.id for item in req.context if item.id]

            result = await qa_service.answer_question_with_context(
                question=req.question,
                search_results=context_dicts,
                user_id=str(user.id)
            )
        else:
            result = {
                "answer": "Please provide search results or context to answer your question.",
                "confidence_score": 0.0,
                "source_document": "none",
                "model_used": None
            }

        # ✅ NEW: Track the question and answer in the database
        await _track_question_answer(
            user_id=str(user.id),
            question=req.question,
            answer=result["answer"],
            confidence_score=result["confidence_score"],
            model_used=result.get("model_used", "unknown"),
            source_document_ids=source_document_ids
        )

        return QuestionResponse(
            answer=result["answer"],
            confidence_score=result["confidence_score"],
            source_document=result["source_document"]
        )
    
    except Exception as e:
        logger.error(f"Error in ask_question endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")


async def _track_question_answer(
    user_id: str, 
    question: str, 
    answer: str, 
    confidence_score: float, 
    model_used: str,
    source_document_ids: list
):
    """
    Track question and answer in the document records
    """
    try:
        # Create Q&A record
        qa_record = {
            "question": question,
            "answer": answer,
            "confidence_score": confidence_score,
            "model_used": model_used,
            "asked_at": datetime.utcnow(),
            "id": str(ObjectId())  # Unique ID for each Q&A
        }

        documents_updated = 0

        # If we have specific source documents, update those
        if source_document_ids:
            for doc_id in source_document_ids:
                try:
                    if ObjectId.is_valid(doc_id):
                        doc = await AcceptedDocument.find_one({
                            "_id": ObjectId(doc_id),
                            "user_id": user_id
                        })
                        
                        if doc:
                            # Initialize questions_asked if it doesn't exist
                            if not hasattr(doc, 'questions_asked') or doc.questions_asked is None:
                                doc.questions_asked = []
                            
                            # Add the Q&A record
                            doc.questions_asked.append(qa_record)
                            await doc.save()
                            documents_updated += 1
                            
                            logger.info(f"Tracked Q&A in document {doc_id}: {question[:50]}...")
                        
                except Exception as doc_error:
                    logger.warning(f"Could not update document {doc_id}: {doc_error}")
                    continue
        
        # If no specific documents or no documents were updated, 
        # find the most relevant document and update it
        if documents_updated == 0:
            try:
                # Find user's most recent document or most relevant document
                recent_doc = await AcceptedDocument.find(
                    AcceptedDocument.user_id == user_id
                ).sort(-AcceptedDocument.upload_date).first()
                
                if recent_doc:
                    if not hasattr(recent_doc, 'questions_asked') or recent_doc.questions_asked is None:
                        recent_doc.questions_asked = []
                    
                    recent_doc.questions_asked.append(qa_record)
                    await recent_doc.save()
                    documents_updated += 1
                    
                    logger.info(f"Tracked Q&A in most recent document {recent_doc.id}: {question[:50]}...")
                
            except Exception as recent_doc_error:
                logger.warning(f"Could not update recent document: {recent_doc_error}")

        logger.info(f"Successfully tracked question in {documents_updated} document(s)")
        
    except Exception as e:
        logger.error(f"Failed to track question/answer: {e}")
        # Don't raise exception - tracking failure shouldn't break Q&A functionality


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


# ✅ NEW: Additional endpoint to get Q&A history
@router.get("/history")
async def get_question_history(user=Depends(get_current_user), limit: int = 20):
    """Get user's question and answer history."""
    try:
        # Aggregate all questions from user's documents
        pipeline = [
            {"$match": {"user_id": str(user.id), "questions_asked": {"$exists": True, "$ne": []}}},
            {"$unwind": "$questions_asked"},
            {"$sort": {"questions_asked.asked_at": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "question": "$questions_asked.question",
                    "answer": "$questions_asked.answer",
                    "confidence_score": "$questions_asked.confidence_score",
                    "model_used": "$questions_asked.model_used",
                    "asked_at": "$questions_asked.asked_at",
                    "document_filename": "$filename",
                    "document_id": {"$toString": "$_id"}
                }
            }
        ]
        
        history = await AcceptedDocument.aggregate(pipeline).to_list()
        
        return {
            "questions": history,
            "total": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error fetching question history: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching question history: {str(e)}")


# ✅ NEW: Endpoint to get Q&A stats
@router.get("/stats")
async def get_qa_stats(user=Depends(get_current_user)):
    """Get user's Q&A statistics."""
    try:
        # Count documents with questions
        documents_with_questions = await AcceptedDocument.find(
            AcceptedDocument.user_id == str(user.id),
            AcceptedDocument.questions_asked.size() > 0
        ).count()
        
        # Count total questions
        pipeline = [
            {"$match": {"user_id": str(user.id), "questions_asked": {"$exists": True}}},
            {"$project": {"question_count": {"$size": "$questions_asked"}}},
            {"$group": {"_id": None, "total_questions": {"$sum": "$question_count"}}}
        ]
        
        result = await AcceptedDocument.aggregate(pipeline).to_list()
        total_questions = result[0]["total_questions"] if result else 0
        
        return {
            "total_questions": total_questions,
            "documents_with_questions": documents_with_questions,
            "avg_questions_per_document": round(total_questions / max(documents_with_questions, 1), 2)
        }
        
    except Exception as e:
        logger.error(f"Error fetching Q&A stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching Q&A stats: {str(e)}")