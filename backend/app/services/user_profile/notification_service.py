import logging
from datetime import datetime, timedelta
from typing import List
from app.models.user import User
from app.models.document import AcceptedDocument
from app.models.rejected_document import RejectedDocument
from app.schemas.user import NotificationResponse

logger = logging.getLogger(__name__)

class NotificationService:
    """Service class for user notifications"""

    @staticmethod
    async def get_user_notifications(user: User, limit: int = 10) -> List[NotificationResponse]:
        try:
            notifications = []

            if not getattr(user, 'is_verified', True):
                notifications.append(NotificationResponse(
                    id="email_verification",
                    message="Your email is not verified. Please check your inbox and verify your email.",
                    type="warning",
                    createdAt=datetime.utcnow()
                ))

            if not getattr(user, 'is_active', True):
                notifications.append(NotificationResponse(
                    id="account_inactive",
                    message="Your account is inactive. Please contact support.",
                    type="warning",
                    createdAt=datetime.utcnow()
                ))

            recent_docs_count = await AcceptedDocument.find(
                AcceptedDocument.user_id == user.id,
                AcceptedDocument.upload_date >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            if recent_docs_count > 0:
                notifications.append(NotificationResponse(
                    id="recent_upload",
                    message=f"Document analysis complete for {recent_docs_count} files",
                    type="success",
                    createdAt=datetime.utcnow() - timedelta(hours=2)
                ))

            rejected_docs_count = await RejectedDocument.find(
                RejectedDocument.user_id == user.id,
                RejectedDocument.upload_date >= datetime.utcnow() - timedelta(days=7)
            ).count()
            if rejected_docs_count > 0:
                notifications.append(NotificationResponse(
                    id="rejected_docs",
                    message=f"{rejected_docs_count} documents were rejected this week",
                    type="warning",
                    createdAt=datetime.utcnow() - timedelta(days=1)
                ))

            pending_docs_count = await AcceptedDocument.find(
                AcceptedDocument.user_id == user.id,
                AcceptedDocument.analysis_status == "pending"
            ).count()
            if pending_docs_count > 0:
                notifications.append(NotificationResponse(
                    id="pending_analysis",
                    message=f"{pending_docs_count} documents are pending analysis",
                    type="info",
                    createdAt=datetime.utcnow() - timedelta(minutes=30)
                ))

            if not notifications:
                notifications.append(NotificationResponse(
                    id="welcome",
                    message="Welcome to LawLens! Start by uploading your first legal document for analysis.",
                    type="info",
                    createdAt=datetime.utcnow() - timedelta(hours=1)
                ))

            notifications.sort(key=lambda x: x.createdAt, reverse=True)
            return notifications[:limit]

        except Exception as e:
            logger.error(f"Failed to get notifications: {e}")
            raise
