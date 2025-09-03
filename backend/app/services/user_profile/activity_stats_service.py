import logging
from app.models.user import User
from app.models.document import AcceptedDocument
from app.schemas.user import ActivityStatsResponse

logger = logging.getLogger(__name__)

class ActivityStatsService:
    """Service class for user activity statistics"""

    @staticmethod
    async def get_activity_stats(user: User) -> ActivityStatsResponse:
        try:
            documents_uploaded = await AcceptedDocument.find(
                AcceptedDocument.user_id == user.id
            ).count()


            # Count contracts that have been analyzed
            contracts_analyzed = await AcceptedDocument.find(
                AcceptedDocument.user_id == user.id,
                AcceptedDocument.contract_analyzed == True,
                AcceptedDocument.last_analyzed != None
            ).count()

            pipeline = [
                {"$match": {"user_id": user.id, "questions_asked": {"$exists": True}}},
                {"$project": {"question_count": {"$size": "$questions_asked"}}},
                {"$group": {"_id": None, "total_questions": {"$sum": "$question_count"}}}
            ]
            result = await AcceptedDocument.aggregate(pipeline).to_list()
            questions_answered = result[0]["total_questions"] if result else 0

            logger.info(f"Activity stats for user {user.id}: docs={documents_uploaded}, contracts={contracts_analyzed}, questions={questions_answered}")

            return ActivityStatsResponse(
                documentsUploaded=documents_uploaded,
                contractsAnalyzed=contracts_analyzed,
                questionsAnswered=questions_answered
            )

        except Exception as e:
            logger.error(f"Failed to get activity stats: {e}")
            raise
