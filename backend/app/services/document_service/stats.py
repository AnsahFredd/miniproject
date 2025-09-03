import logging
from app.models.document import AcceptedDocument
from app.models.rejected_document import RejectedDocument

logger = logging.getLogger("document_stats")

async def get_user_validation_stats(user_id: str) -> dict:
    try:
        accepted_docs = await AcceptedDocument.find(
            AcceptedDocument.user_id == user_id
        ).count()
        rejected_docs = await RejectedDocument.find(
            RejectedDocument.user_id == user_id
        ).count()
        validation_rejections = await RejectedDocument.find({
            "user_id": user_id,
            "reason": {"$regex": "Invalid legal contract", "$options": "i"}
        }).count()
        return {
            "total_uploads": accepted_docs + rejected_docs,
            "valid_contracts": accepted_docs,
            "total_rejections": rejected_docs,
            "validation_rejections": validation_rejections,
            "success_rate": round((accepted_docs / (accepted_docs + rejected_docs)) * 100, 2) if (accepted_docs + rejected_docs) > 0 else 0
        }
    except Exception as e:
        logger.error(f"Error fetching validation stats: {e}")
        return {
            "total_uploads": 0,
            "valid_contracts": 0,
            "total_rejections": 0,
            "validation_rejections": 0,
            "success_rate": 0
        }
