# app/tasks/document_tasks.py - FIXED VERSION
import logging
import time
from datetime import datetime, timezone
from bson import ObjectId
from typing import Dict, Any
import asyncio

from app.core.celery_app import celery_app
from app.database.mongo import ensure_connection, get_database_async
from app.services.model_preloader import model_preloader
from app.models.document import AcceptedDocument
from app.services.classification.service import DocumentClassificationService

logger = logging.getLogger("document_processing")

# Global state - but reset properly between tasks
_task_models_cache = {}
classification_service = None


def _reset_task_state():
    """Reset global task state to prevent interference between tasks"""
    global _task_models_cache, classification_service
    _task_models_cache.clear()
    classification_service = None


def _get_or_create_event_loop():
    """Safely get or create event loop, handling existing loops"""
    try:
        # Try to get current event loop
        loop = asyncio.get_running_loop()
        # If we get here, there's already a running loop
        # We should create a new one for our task
        logger.debug("Found existing event loop, creating new one for task")
        return asyncio.new_event_loop()
    except RuntimeError:
        # No running loop, safe to create new one
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_document_async(self, document_id: str, user_id: str) -> Dict[str, Any]:
    """
    Synchronous Celery wrapper for async document processing.
    Creates a new event loop to avoid conflicts.
    Returns a JSON-serializable dict result.
    """
    # Reset state at start of each task
    _reset_task_state()
    
    loop = None
    try:
        # Create and set new event loop for this task
        loop = _get_or_create_event_loop()
        asyncio.set_event_loop(loop)
        
        logger.info(f"[TASK START] Processing document {document_id} with new event loop")
        
        try:
            result = loop.run_until_complete(_process_document_async(document_id, user_id, self))
            logger.info(f"[TASK SUCCESS] Document {document_id} processed successfully")
            return result
        except Exception as async_error:
            logger.error(f"[TASK ERROR] Async processing failed: {async_error}", exc_info=True)
            raise async_error
            
    except Exception as e:
        logger.error(f"[TASK CRITICAL] Critical failure in async wrapper: {e}", exc_info=True)
        
        # Only retry for retryable errors
        if self.request.retries < self.max_retries:
            # Don't retry document not found errors
            if "DocumentNotFound" in str(e) or "not found" in str(e).lower():
                logger.info(f"Not retrying for document not found error: {e}")
            else:
                logger.info(f"Retrying task (attempt {self.request.retries + 1}/{self.max_retries})")
                raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        
        return {
            "status": "failed",
            "document_id": document_id,
            "error_type": type(e).__name__,
            "error_message": str(e),
        }
    finally:
        # CRITICAL: Always clean up the event loop
        if loop:
            try:
                # Cancel any remaining tasks
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                
                # Wait for cancelled tasks to complete
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                
                # Close the loop
                loop.close()
                logger.debug(f"Event loop cleaned up for document {document_id}")
            except Exception as cleanup_error:
                logger.warning(f"Event loop cleanup warning: {cleanup_error}")
        
        # Reset state after each task
        _reset_task_state()


async def _process_document_async(document_id: str, user_id: str, task_self) -> Dict[str, Any]:
    """
    Async document processing: classification, summarization, embeddings, and tagging.
    """
    global _task_models_cache, classification_service
    document = None
    
    try:
        # Fresh MongoDB connection for each task
        logger.debug(f"Establishing fresh MongoDB connection for document {document_id}")
        await ensure_connection()

        logger.info(f"[BACKGROUND] Starting AI processing for document {document_id}")

        # --- Progress update ---
        try:
            task_self.update_state(
                state="PROGRESS",
                meta={"stage": "starting", "progress": 5, "message": "Initializing AI processing..."}
            )
        except Exception as meta_error:
            logger.warning(f"Metadata update failed (non-critical): {meta_error}")

        # --- Fetch document using multiple approaches ---
        try:
            # First try: Beanie get method
            logger.debug(f"Attempting to fetch document {document_id} using Beanie.get()")
            try:
                document = await AcceptedDocument.get(ObjectId(document_id))
            except Exception as beanie_error:
                logger.warning(f"Beanie.get() failed: {beanie_error}")
                document = None

            # Second try: Beanie find_one method
            if not document:
                logger.debug(f"Attempting to fetch document {document_id} using find_one()")
                document = await AcceptedDocument.find_one({"_id": ObjectId(document_id)})

            # Third try: Also search by user_id to ensure it exists
            if not document:
                logger.debug(f"Attempting to fetch document by user_id {user_id}")
                document = await AcceptedDocument.find_one({
                    "_id": ObjectId(document_id),
                    "user_id": user_id
                })

            if not document:
                # Final check: Does the document exist at all?
                all_docs = await AcceptedDocument.find().to_list()
                logger.error(f"Document {document_id} not found. Total documents in DB: {len(all_docs)}")
                if all_docs:
                    doc_ids = [str(doc.id) for doc in all_docs[:5]]  # Show first 5 IDs
                    logger.error(f"Sample document IDs: {doc_ids}")
                
                logger.warning(f"[BACKGROUND] Document {document_id} not found. Skipping task.")
                return {
                    "status": "failed",
                    "document_id": document_id,
                    "error_type": "DocumentNotFound",
                    "error_message": f"Document {document_id} not found"
                }

            logger.info(f"Successfully found document: {document.filename} for user {document.user_id}")
            
        except Exception as e:
            logger.error(f"Failed to fetch document {document_id}: {e}", exc_info=True)
            return {
                "status": "failed",
                "document_id": document_id,
                "error_type": "DocumentFetchError",
                "error_message": f"Document {document_id} could not be fetched: {str(e)}"
            }

        # --- Mark processing started ---
        try:
            document.set_processing_started(task_self.request.id)
            await document.save()
            logger.info(f"Document {document_id} marked as processing started")
        except Exception as e:
            logger.error(f"Failed to mark document as processing started: {e}")
            # Continue anyway, don't fail the task for this

        # --- Initialize models for this task (fresh each time) ---
        logger.info("[TASK MODELS] Starting model initialization for this task...")
        try:
            # Initialize fresh model preloader for this task
            await model_preloader.initialize_models()
            logger.info("[TASK MODELS] Models initialized successfully for this task")
        except Exception as e:
            logger.error(f"Model initialization failed for this task: {e}")
            # Continue with fallback behavior

        # --- Initialize classification service fresh for this task ---
        classification_service = DocumentClassificationService()

        # --- Progress update ---
        try:
            task_self.update_state(
                state="PROGRESS",
                meta={"stage": "loading_document", "progress": 15, "message": "Document loaded, starting analysis..."}
            )
        except Exception:
            pass

        content = document.content or ""
        filename = document.filename or "unknown"
        existing_tags = document.tags or []

        if not content:
            logger.warning(f"Document {document_id} has no content, using filename for analysis")
            content = f"Document: {filename}"

        # --- Get services fresh for this task ---
        try:
            summarizer = await model_preloader.get_summarization_service()
            embedder = await model_preloader.get_embedding_service()
            logger.debug("AI services obtained successfully")
        except Exception as e:
            logger.error(f"Failed to get AI services: {e}")
            summarizer = None
            embedder = None

        # --- Update progress ---
        try:
            task_self.update_state(
                state="PROGRESS",
                meta={"stage": "classification", "progress": 25, "message": "Analyzing document type..."}
            )
        except Exception:
            pass

        # --- Classification ---
        classification_result = {}
        try:
            classification_result = await classification_service.classify_document_async(content, filename)
            logger.info(f"Classification completed: {classification_result.get('document_type', 'unknown')}")
        except Exception as e:
            logger.error(f"Classification failed: {e}", exc_info=True)
            classification_result = {"document_type": "general", "method": "fallback", "error": str(e)}

        # --- Update progress ---
        try:
            task_self.update_state(
                state="PROGRESS",
                meta={"stage": "summarization", "progress": 50, "message": "Generating summary..."}
            )
        except Exception:
            pass

        # --- Summarization ---
        summary = ""
        try:
            if summarizer and len(content) > 100:  # Only summarize if there's enough content
                summary = await summarizer.summarize_text(content)
                logger.info(f"Summary generated: {len(summary)} characters")
            else:
                summary = "Content too short for meaningful summarization" if len(content) <= 100 else "Summarization service unavailable"
        except Exception as e:
            logger.error(f"Summarization failed: {e}", exc_info=True)
            summary = f"Summary generation failed: {str(e)}"

        # --- Update progress ---
        try:
            task_self.update_state(
                state="PROGRESS",
                meta={"stage": "embedding", "progress": 75, "message": "Generating embeddings..."}
            )
        except Exception:
            pass

        # --- Embedding ---
        embedding = []
        try:
            if embedder and len(content.strip()) > 0:
                embedding_result = await embedder.generate_embedding(content)
                if hasattr(embedding_result, "tolist"):
                    embedding = embedding_result.tolist()
                elif isinstance(embedding_result, list):
                    embedding = embedding_result
                logger.info(f"Embedding generated: {len(embedding)} dimensions")
            else:
                logger.warning("Embedding service unavailable or empty content")
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}", exc_info=True)

        # --- AI Tags ---
        ai_tags = []
        doc_type = classification_result.get("document_type", "general")
        legal_domain = classification_result.get("legal_domain", "general")
        urgency = classification_result.get("urgency", "low")
        
        if doc_type != "general":
            ai_tags.append(doc_type)
        if legal_domain != "general":
            ai_tags.append(legal_domain)
        if urgency in ["high", "medium"]:
            ai_tags.append(f"urgency_{urgency}")
        
        all_tags = list(set(existing_tags + ai_tags))

        # --- Update progress ---
        try:
            task_self.update_state(
                state="PROGRESS",
                meta={"stage": "finalizing", "progress": 90, "message": "Saving results..."}
            )
        except Exception:
            pass

        # --- Clause Extraction ---
        clause_overview = []
        try:
            from app.services.document_analysis_service import DocumentAnalysisService
            analysis_service = DocumentAnalysisService()
            
            # Extract clauses using the same logic as the analysis endpoint
            clause_overview = analysis_service._extract_clauses(content)
            logger.info(f"Extracted {len(clause_overview)} clauses for document {document_id}")
            
        except Exception as e:
            logger.error(f"Clause extraction failed: {e}", exc_info=True)
            # Don't fail the entire task for clause extraction failure
            clause_overview = []

        # --- Update document with results ---
        try:
            # Refresh document before updating to avoid stale state
            document = await AcceptedDocument.get(ObjectId(document_id))
            if not document:
                raise Exception("Document disappeared during processing")
            
            # Use helper method to mark completion
            document.set_processing_completed()
            
            # Update additional fields
            document.summary = summary
            document.embedding = embedding
            document.tags = all_tags
            document.classification_result = classification_result
            document.document_type = doc_type
            
            document.analysis_results = {
                "clause_overview": clause_overview,
                "summary": {"text": summary},
                "classification": classification_result,
                "processed_at": datetime.now(timezone.utc).isoformat()
            }
            
            document.analysis_status = "completed"
            document.contract_analyzed = True
            document.analysis_completed_at = datetime.now(timezone.utc)
            
            # Save all changes at once
            await document.save()
            logger.info(f"Successfully updated document {document_id} with AI results and clause extraction")
                
        except Exception as e:
            logger.error(f"Failed to update document results: {e}", exc_info=True)
            # Try to mark as failed before returning error
            if document:
                try:
                    document.set_processing_failed(f"Failed to save results: {str(e)}")
                    document.analysis_status = "failed"
                    await document.save()
                except Exception:
                    pass
            
            return {
                "status": "partial_success",
                "document_id": document_id,
                "classification": classification_result,
                "summary_length": len(summary),
                "ai_tags": ai_tags,
                "total_tags": len(all_tags),
                "embedding_dimensions": len(embedding),
                "clauses_extracted": len(clause_overview),
                "warning": "Processing completed but database update failed",
                "db_error": str(e)
            }

        logger.info(f"[BACKGROUND] Completed AI processing for {document_id}")
        
        # Final progress update
        try:
            task_self.update_state(
                state="SUCCESS",
                meta={"stage": "completed", "progress": 100, "message": "Processing completed successfully"}
            )
        except Exception:
            pass
        
        return {
            "status": "completed",
            "document_id": document_id,
            "classification": classification_result,
            "summary_length": len(summary),
            "ai_tags": ai_tags,
            "total_tags": len(all_tags),
            "embedding_dimensions": len(embedding),
            "clauses_extracted": len(clause_overview),
            "processing_time_seconds": time.time(),
        }

    except Exception as e:
        logger.error(f"[BACKGROUND] Error processing document {document_id}: {e}", exc_info=True)

        # Mark document as failed using helper method
        if document:
            try:
                document.set_processing_failed(str(e))
                document.analysis_status = "failed"
                await document.save()
                logger.info(f"Marked document {document_id} as failed in database")
            except Exception as db_error:
                logger.error(f"Failed to mark document as failed: {db_error}", exc_info=True)

        # Update task state to failed
        try:
            task_self.update_state(
                state="FAILURE",
                meta={"stage": "failed", "progress": 0, "message": f"Processing failed: {str(e)}"}
            )
        except Exception:
            pass

        # Decide whether to retry
        if task_self.request.retries < task_self.max_retries:
            # Don't retry for certain error types
            if "DocumentNotFound" in str(e) or "not found" in str(e).lower():
                logger.info(f"Not retrying for document not found error: {e}")
                return {
                    "status": "failed",
                    "document_id": document_id,
                    "error_type": "DocumentNotFound",
                    "error_message": str(e),
                }
            
            logger.info(f"Retrying document {document_id} (attempt {task_self.request.retries + 1}/{task_self.max_retries})")
            raise task_self.retry(exc=e, countdown=60 * (task_self.request.retries + 1))

        return {
            "status": "failed",
            "document_id": document_id,
            "error_type": type(e).__name__,
            "error_message": str(e),
        }


# Debug tasks for testing
@celery_app.task(bind=True)
def debug_simple_task(self):
    """Simple debug task to test Celery connection"""
    try:
        logger.info("Debug task started")
        time.sleep(2)
        logger.info("Debug task completed")
        return {"status": "success", "message": "Debug task completed successfully"}
    except Exception as e:
        logger.error(f"Debug task failed: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(bind=True)
def debug_model_loading(self):
    """Debug task to test model loading"""
    try:
        logger.info("Testing model loading...")
        
        # Test without async/await - just check if services can be created
        from app.services.classification.service import DocumentClassificationService
        classifier = DocumentClassificationService()
        
        return {
            "status": "success", 
            "message": "Model loading test completed",
            "classification_service": "loaded"
        }
    except Exception as e:
        logger.error(f"Model loading test failed: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}


@celery_app.task(bind=True)
def debug_event_loop(self):
    """Debug task to test event loop handling"""
    loop = None
    try:
        logger.info("Testing event loop creation...")
        
        loop = _get_or_create_event_loop()
        asyncio.set_event_loop(loop)
        
        async def simple_async_task():
            await asyncio.sleep(0.1)
            return "async task completed"
        
        result = loop.run_until_complete(simple_async_task())
        logger.info(f"Event loop test result: {result}")
        
        return {"status": "success", "message": result}
        
    except Exception as e:
        logger.error(f"Event loop test failed: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}
    finally:
        if loop:
            try:
                loop.close()
            except Exception:
                pass