"""
Fixed Question Routes - Fixes the database query issues in your existing code
"""

from fastapi import APIRouter, Depends, HTTPException
from app.schemas.question import QuestionRequest, QuestionResponse
from app.services import qa_service
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
            return QuestionResponse(
                answer="Please provide a question",
                confidence_score=0.0,
                source_document=None,
                
            )
            
        result = None
        source_document_ids = []

        # If context from search results is provided, use that
        if req.context and len(req.context) > 0:
            # Extract the text content from context items
            context_text = ""
            source_document_ids = []
            
            for item in req.context:
                # Combine the relevant text fields
                item_text = f"{item.title}\n{item.description}\n{item.section}\n"
                context_text += item_text + "\n"
                
                # Track document IDs
                if item.id and ObjectId.is_valid(item.id):
                    source_document_ids.append(item.id)

            result = await qa_service.answer_question(
                question=req.question,
                user_id=str(user.id),
                document_id=source_document_ids[0] if source_document_ids else None
            )
            

            # Map the response to match expected format
            result = {
                "answer": result.get("answer", "No answer found"),
                "confidence_score": result.get("confidence", 0.0),
                "source_document": source_document_ids[0] if source_document_ids else "none",
                "model_used": "context-based"
            }
            
        else:
            # No context provided - use the regular answer_question method
            result = await qa_service.answer_question(
                question=req.question,
                user_id=str(user.id),
                document_id=None
            )

        # Track the question and answer in the database
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
    Track question and answer in the document records - FIXED VERSION
    """
    try:
        # Create Q&A record
        qa_record = {
            "question": question,
            "answer": answer,
            "confidence_score": confidence_score,
            "model_used": model_used,
            "asked_at": datetime.utcnow(),
            "qa_id": str(ObjectId())
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
        
        # ✅ FIXED: If no specific documents or no documents were updated,
        # find the most relevant document and update it
        if documents_updated == 0:
            try:
                # ✅ FIXED: Use proper Beanie query syntax
                recent_doc = await AcceptedDocument.find({
                    "user_id": user_id
                }).sort([("upload_date", -1)]).limit(1).to_list()
                
                if recent_doc and len(recent_doc) > 0:
                    doc = recent_doc[0]  # Get the first (and only) document
                    
                    if not hasattr(doc, 'questions_asked') or doc.questions_asked is None:
                        doc.questions_asked = []
                    
                    doc.questions_asked.append(qa_record)
                    await doc.save()
                    documents_updated += 1
                    
                    logger.info(f"Tracked Q&A in most recent document {doc.id}: {question[:50]}...")
                
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


@router.get("/history")
async def get_question_history(user=Depends(get_current_user), limit: int = 20):
    """Get user's question and answer history."""
    try:
        # ✅ FIXED: Proper MongoDB query syntax with Beanie
        documents = await AcceptedDocument.find({
            "user_id": str(user.id),
            "questions_asked": {"$exists": True, "$ne": None}
        }).to_list()
        
        # Extract all questions from documents
        history = []
        for doc in documents:
            if hasattr(doc, 'questions_asked') and doc.questions_asked:
                for qa in doc.questions_asked:
                    history.append({
                        "question": qa.get("question"),
                        "answer": qa.get("answer"),
                        "confidence_score": qa.get("confidence_score"),
                        "model_used": qa.get("model_used"),
                        "asked_at": qa.get("asked_at"),
                        "document_filename": getattr(doc, 'filename', 'Unknown'),
                        "document_id": str(doc.id)
                    })
        
        # Sort by asked_at descending and limit
        history.sort(key=lambda x: x.get('asked_at', datetime.min), reverse=True)
        history = history[:limit]
        
        return {
            "questions": history,
            "total": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error fetching question history: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching question history: {str(e)}")


@router.get("/stats")
async def get_qa_stats(user=Depends(get_current_user)):
    """Get user's Q&A statistics."""
    try:
        # ✅ FIXED: Proper MongoDB query
        documents = await AcceptedDocument.find({
            "user_id": str(user.id)
        }).to_list()
        
        documents_with_questions = 0
        total_questions = 0
        
        for doc in documents:
            if hasattr(doc, 'questions_asked') and doc.questions_asked:
                documents_with_questions += 1
                total_questions += len(doc.questions_asked)
        
        return {
            "total_questions": total_questions,
            "documents_with_questions": documents_with_questions,
            "avg_questions_per_document": round(total_questions / max(documents_with_questions, 1), 2)
        }
        
    except Exception as e:
        logger.error(f"Error fetching Q&A stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching Q&A stats: {str(e)}")


# ============================================================================
# ADDITIONAL ENDPOINTS FOR ENHANCED FUNCTIONALITY
# ============================================================================

@router.post("/generate-questions/{document_id}")
async def generate_questions_for_document(
    document_id: str,
    user=Depends(get_current_user),
    max_questions: int = 5
):
    """
    Generate relevant questions for a specific document
    """
    try:
        # Validate document_id
        if not ObjectId.is_valid(document_id):
            raise HTTPException(status_code=400, detail="Invalid document_id format")
        
        # Check if document exists and belongs to user
        document = await AcceptedDocument.find_one({
            "_id": ObjectId(document_id),
            "user_id": str(user.id)
        })
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Try to use unified service for question generation
        try:
            from app.services.qa_service import qa_service
            questions = await qa_service.generate_questions_for_document(
                document_id=document_id,
                user_id=str(user.id)
            )
        except ImportError:
            # Fallback: generate basic questions based on document content
            content = getattr(document, 'content', '')
            content_lower = content.lower()
            
            questions = []
            
            # Contract/legal questions
            if any(word in content_lower for word in ['contract', 'agreement', 'lease', 'legal']):
                questions.extend([
                    "What is the effective date of this agreement?",
                    "Who are the parties involved in this contract?",
                    "What are the main terms and conditions?",
                    "What are the payment terms specified?",
                    "When does this agreement expire?"
                ])
            
            # Generic questions
            questions.extend([
                "What is this document about?",
                "What are the key points discussed?",
                "What important information is contained here?"
            ])
        
        # Limit the number of questions
        if len(questions) > max_questions:
            questions = questions[:max_questions]
        
        return {
            "questions": questions,
            "document_id": document_id,
            "document_title": getattr(document, "title", None) or getattr(document, "filename", "Unknown")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate questions: {str(e)}"
        )


@router.get("/health")
async def qa_health_check():
    """
    Health check for the Q&A service
    """
    try:
        # Try to get model info from qa_service
        model_info = qa_service.get_model_info()
        health_info = qa_service.health_check()
        
        return {
            "status": "healthy" if health_info.get("healthy", False) else "unhealthy",
            "qa_service_available": True,
            "models_loaded": {
                "general_qa": model_info.get("general_model", {}).get("loaded", False),
                "legal_qa": model_info.get("legal_model", {}).get("loaded", False)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "qa_service_available": False,
            "timestamp": datetime.utcnow().isoformat()
        }