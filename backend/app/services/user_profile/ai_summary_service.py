import logging
from datetime import datetime, timedelta
from app.models.user import User
from app.models.document import AcceptedDocument
from app.schemas.user import AIAssistantSummaryResponse
from beanie import PydanticObjectId

logger = logging.getLogger(__name__)

class AISummaryService:
    """Service for AI assistant summaries"""

    @staticmethod
    async def get_ai_summary(user: User) -> AIAssistantSummaryResponse:
        try:
            week_ago = datetime.utcnow() - timedelta(days=7)
            logger.info(f"Getting AI summary for user {user.id} from {week_ago}")

            # Count documents uploaded this week
            documents_this_week = await AcceptedDocument.find(
                AcceptedDocument.user_id == user.id,
                AcceptedDocument.upload_date >= week_ago  # Using upload_date instead of created_at
            ).count()
            logger.info(f"Documents this week: {documents_this_week}")

            # Count contract reviews completed this week (more flexible matching)
            contract_reviews_query = AcceptedDocument.find(
                AcceptedDocument.user_id == user.id,
                AcceptedDocument.upload_date >= week_ago  # Changed from updated_at to upload_date
            )
            
            # Try different field combinations for contract analysis status
            try:
                # Try with analysis_status field first
                contract_reviews = await AcceptedDocument.find(
                    AcceptedDocument.user_id == user.id,
                    AcceptedDocument.analysis_status == "completed",
                    AcceptedDocument.upload_date >= week_ago
                ).count()
            except Exception as e:
                logger.warning(f"analysis_status field not found: {e}")
                try:
                    # Try with contract_analyzed field
                    contract_reviews = await AcceptedDocument.find(
                        AcceptedDocument.user_id == user.id,
                        AcceptedDocument.contract_analyzed == True,
                        AcceptedDocument.upload_date >= week_ago
                    ).count()
                except Exception as e2:
                    logger.warning(f"contract_analyzed field not found: {e2}")
                    # Fallback: just count all documents as "reviewed"
                    contract_reviews = documents_this_week

            logger.info(f"Contract reviews: {contract_reviews}")

            # Count weekly questions more flexibly
            try:
                # Try to count questions from questions_asked field
                pipeline = [
                    {
                        "$match": {
                            "user_id": user.id, 
                            "upload_date": {"$gte": week_ago},
                            "questions_asked": {"$exists": True, "$ne": None}
                        }
                    },
                    {
                        "$project": {
                            "question_count": {
                                "$cond": {
                                    "if": {"$isArray": "$questions_asked"},
                                    "then": {"$size": "$questions_asked"},
                                    "else": 1  # If it's not an array, assume it's one question
                                }
                            }
                        }
                    },
                    {
                        "$group": {
                            "_id": None,
                            "total_questions": {"$sum": "$question_count"}
                        }
                    }
                ]
                result = await AcceptedDocument.aggregate(pipeline).to_list()
                weekly_questions = result[0]["total_questions"] if result else 0
            except Exception as e:
                logger.warning(f"Could not aggregate questions: {e}")
                # Fallback: count documents with questions field
                try:
                    weekly_questions = await AcceptedDocument.find(
                        AcceptedDocument.user_id == user.id,
                        AcceptedDocument.questions_asked != None,
                        AcceptedDocument.upload_date >= week_ago
                    ).count()
                except:
                    weekly_questions = 0

            logger.info(f"Weekly questions: {weekly_questions}")

            # Get most active day
            most_active_day = await AISummaryService._get_most_active_day(user.id)
            logger.info(f"Most active day: {most_active_day}")

            return AIAssistantSummaryResponse(
                weeklyQuestions=weekly_questions,
                documentsThisWeek=documents_this_week,
                mostActiveDay=most_active_day,
                contractReviews=contract_reviews
            )

        except Exception as e:
            logger.error(f"Failed to get AI summary: {e}")
            # Return default values instead of raising exception
            return AIAssistantSummaryResponse(
                weeklyQuestions=0,
                documentsThisWeek=0,
                mostActiveDay="Monday",
                contractReviews=0
            )

    @staticmethod
    async def _get_most_active_day(user_id: PydanticObjectId) -> str:
        try:
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "upload_date": {"$gte": thirty_days_ago}  # Using upload_date consistently
                    }
                },
                {
                    "$group": {
                        "_id": {"$dayOfWeek": "$upload_date"},
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"count": -1}},
                {"$limit": 1}
            ]
            
            result = await AcceptedDocument.aggregate(pipeline).to_list()
            if result:
                days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
                day_index = result[0]["_id"] - 1  # MongoDB dayOfWeek is 1-based
                return days[day_index] if 0 <= day_index < 7 else "Monday"
        except Exception as e:
            logger.debug(f"Could not determine most active day: {e}")
        
        return "Monday"  # Default fallback