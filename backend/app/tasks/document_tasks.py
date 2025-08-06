from app.services.summarization_service import summarize_text
from app.services.embedding_service import generate_embedding
from app.models.document import AcceptedDocument
from app.core.celery_app import celery_app


@celery_app.task(name="process_document_task")
def process_document_task(doc_id: str, file_path: str, user_id: str):
    """
    Heavy AI processing (summary & embeddings).
    """
    from app.utils.file_utils import parse_file_content
    import asyncio

    async def _process():
        doc = await AcceptedDocument.get(doc_id)
        if not doc:
            return

        try:
            content = await parse_file_content(file_path)
            summary = summarize_text(content)
            embedding = generate_embedding(content)

            doc.content = content
            doc.summary = summary
            doc.embedding = embedding
            doc.status = "ready"
            await doc.save()
        except Exception as e:
            doc.summary = "Processing failed."
            doc.status = "failed"
            await doc.save()
            print(f"[ERROR] Document processing failed: {e}")

    asyncio.run(_process())
