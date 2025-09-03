import logging
from datetime import datetime
from app.models.user import User
from app.schemas.user import UserProfileResponse

logger = logging.getLogger(__name__)

class UserProfileService:
    """Service class for user profile operations"""

    @staticmethod
    async def get_user_profile(user: User) -> UserProfileResponse:
        try:
            logger.info(f"Processing user profile for user ID: {user.id}")
            
            # Instead, use current time as lastLogin for the response
            current_time = datetime.utcnow()
            
            return UserProfileResponse(
                name=getattr(user, 'full_name', 'Unknown User'),
                email=user.email,
                role=getattr(user, 'role', 'User'),
                lastLogin=current_time  # Use current time since we can't update user model
            )
            
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            raise
