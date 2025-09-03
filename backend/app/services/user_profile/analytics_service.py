import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from beanie import PydanticObjectId
from app.models.document import AcceptedDocument

logger = logging.getLogger(__name__)

class UserStatsService:
    """Service for advanced user statistics and analytics"""


    @staticmethod
    async def get_user_analytics(user_id: PydanticObjectId, days: int = 30) -> Dict[str, Any]:
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            return {
                "dailyActivity": await UserStatsService._get_daily_activity(user_id, cutoff_date),
                "documentTypeDistribution": await UserStatsService._get_document_type_distribution(user_id),
                "processingStatistics": await UserStatsService._get_processing_statistics(user_id),
                "period": f"Last {days} days"
            }
        except Exception as e:
            logger.error(f"Failed to get user analytics: {e}")
            raise

    @staticmethod
    async def _get_daily_activity(user_id: PydanticObjectId, cutoff_date: datetime) -> List[Dict]:
        pipeline = [
            {"$match": {"user_id": user_id, "created_at": {"$gte": cutoff_date}}},
            {
                "$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        return await AcceptedDocument.aggregate(pipeline).to_list()

    @staticmethod
    async def _get_document_type_distribution(user_id: PydanticObjectId) -> List[Dict]:
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": "$document_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        return await AcceptedDocument.aggregate(pipeline).to_list()

    @staticmethod
    async def _get_processing_statistics(user_id: PydanticObjectId) -> Dict[str, Any]:
        pipeline = [
            {"$match": {"user_id": user_id}},
            {
                "$group": {
                    "_id": "$analysis_status",
                    "count": {"$sum": 1},
                    "avgProcessingTime": {"$avg": {"$subtract": ["$updated_at", "$created_at"]}}
                }
            }
        ]
        results = await AcceptedDocument.aggregate(pipeline).to_list()
        for r in results:
            if r.get("avgProcessingTime"):
                r["avgProcessingTimeMinutes"] = r["avgProcessingTime"] / (1000 * 60)
        return {"statusDistribution": results, "totalDocuments": sum(r["count"] for r in results)}
