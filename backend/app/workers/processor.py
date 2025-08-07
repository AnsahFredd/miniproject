# Background doc parsing using Celery

import os
from LawLens.backend.app.workers.celery_worker import celery_app
from app.utils.file_utils import extract_text_from_file
from app.services.embedding_service import generate_embedding
from app.database.mongo import init_beanie
from app.models.document import Document
from app.models.rejected_document import RejectedDocument
from app.core.config import settings
import asyncio
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="app.workers.processor.process_document_task")
def process_document_task(document_id: str, file_path: str, user_id: str):
    asyncio.run(_process_document(document_id, file_path, user_id))


async def _process_document(document_id: str, file_path: str, user_id: str):
    await init_beanie()

    try:
        content = extract_text_from_file(file_path)
        if not content or len(content.strip()) < 20:
            raise ValueError("Insufficient content extracted")

        embedding = generate_embedding(content)

        doc = await Document.get(document_id)
        if doc:
            doc.text_content = content
            doc.embedding = embedding
            doc.status = "processed"
            await doc.save()

        logger.info(f"✅ Document {document_id} processed for user {user_id}")
        os.remove(file_path)

    except Exception as e:
        logger.error(f"Failed to process doc {document_id}: {str(e)}")

        await RejectedDocument(
            user_id=user_id,
            original_document_id=document_id,
            reason=str(e),
        ).insert()

        doc = await Document.get(document_id)
        if doc:
            doc.status = "rejected"
            await doc.save()

        if os.path.exists(file_path):
            os.remove(file_path)
