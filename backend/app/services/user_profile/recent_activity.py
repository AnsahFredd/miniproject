import logging
from datetime import datetime
from typing import List
from app.models.user import User
from app.models.document import AcceptedDocument
from app.models.rejected_document import RejectedDocument
from app.schemas.user import RecentActivityResponse

logger = logging.getLogger(__name__)

class RecentActivityService:
    """Service class for recent user activities"""

    @staticmethod
    async def get_recent_activity(user: User, limit: int = 10) -> List[RecentActivityResponse]:
        try:
            activities = []
            recent_accepted = await AcceptedDocument.find(
                AcceptedDocument.user_id == user.id
            ).sort(-AcceptedDocument.upload_date).limit(limit).to_list()

            for doc in recent_accepted:
                action = {
                    "completed": "Analyzed",
                    "processing": "Processing",
                    "pending": "Pending Analysis"
                }.get(getattr(doc, 'analysis_status', None), "Uploaded")

                activities.append(RecentActivityResponse(
                    id=str(doc.id),
                    action=action,
                    fileName=getattr(doc, 'filename', 'Unknown File'),
                    timestamp=doc.upload_date
                ))

            if len(activities) < limit:
                remaining_limit = limit - len(activities)
                recent_rejected = await RejectedDocument.find(
                    RejectedDocument.user_id == user.id
                ).sort(-RejectedDocument.upload_date).limit(remaining_limit).to_list()

                for doc in recent_rejected:
                    activities.append(RecentActivityResponse(
                        id=str(doc.id),
                        action="Rejected",
                        fileName=doc.filename,
                        timestamp=doc.upload_date
                    ))

            if not activities:
                activities.append(RecentActivityResponse(
                    id="account_created",
                    action="Account Created",
                    fileName="Welcome to LawLens",
                    timestamp=getattr(user, 'created_at', datetime.utcnow())
                ))

            activities.sort(key=lambda x: x.timestamp, reverse=True)
            return activities[:limit]

        except Exception as e:
            logger.error(f"Failed to get recent activity: {e}")
            raise
