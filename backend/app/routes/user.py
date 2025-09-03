# app/routers/user_profile.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import logging
import traceback

from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.user_profile import (
    UserProfileService, 
    UserStatsService, 
    ActivityStatsService, 
    NotificationService, 
    RecentActivityService, 
    AISummaryService
    )

from app.schemas.user import (
    UserProfileResponse,
    ActivityStatsResponse,
    NotificationResponse,
    RecentActivityResponse,
    AIAssistantSummaryResponse,
    UserAnalyticsResponse
)

# Set up logger with specific name for this module
logger = logging.getLogger("app.routers.user_profile")
router = APIRouter(tags=["user"])


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user's profile information
    """
    try:
        logger.info(f"Getting profile for user: {current_user.id}")
        logger.info(f"User email: {current_user.email}")
        logger.info(f"User fields: {list(current_user.__dict__.keys())}")
        
        result = await UserProfileService.get_user_profile(current_user)
        logger.info(f"Profile result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in get_user_profile: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile error: {str(e)}"
        )


@router.get("/activity-stats", response_model=ActivityStatsResponse)
async def get_user_activity_stats(current_user: User = Depends(get_current_user)):
    """
    Get user's activity statistics
    """
    try:
        logger.info(f"Getting activity stats for user: {current_user.id}")
        
        # Check if AcceptedDocument is accessible
        try:
            logger.info("AcceptedDocument model imported successfully")
        except ImportError as import_error:
            logger.error(f"Failed to import AcceptedDocument: {import_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Document model not available"
            )
        
        result = await ActivityStatsService.get_activity_stats(current_user)
        logger.info(f"Activity stats result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in get_user_activity_stats: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Activity stats error: {str(e)}"
        )


@router.get("/notifications", response_model=List[NotificationResponse])
async def get_user_notifications(
    current_user: User = Depends(get_current_user),
    limit: int = 10
):
    """
    Get user's recent notifications
    """
    try:
        logger.info(f"Getting notifications for user: {current_user.id}")
        
        result = await NotificationService.get_user_notifications(current_user, limit)
        logger.info(f"Notifications result: {len(result)} notifications")
        return result
        
    except Exception as e:
        logger.error(f"Error in get_user_notifications: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Notifications error: {str(e)}"
        )


@router.get("/recent-activity", response_model=List[RecentActivityResponse])
async def get_user_recent_activity(
    current_user: User = Depends(get_current_user),
    limit: int = 10
):
    """
    Get user's recent activity
    """
    try:
        logger.info(f"Getting recent activity for user: {current_user.id}")
        
        result = await RecentActivityService.get_recent_activity(current_user, limit)
        logger.info(f"Recent activity result: {len(result)} activities")
        return result
        
    except Exception as e:
        logger.error(f"Error in get_user_recent_activity: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recent activity error: {str(e)}"
        )


@router.get("/ai-summary", response_model=AIAssistantSummaryResponse)
async def get_ai_summary(current_user: User = Depends(get_current_user)):
    """
    Get AI assistant summary for the user
    """
    try:
        logger.info(f"Getting AI summary for user: {current_user.id}")
        
        result = await AISummaryService.get_ai_summary(current_user)
        logger.info(f"AI summary result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in get_ai_summary: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI summary error: {str(e)}"
        )


@router.get("/analytics", response_model=UserAnalyticsResponse)
async def get_user_analytics(
    current_user: User = Depends(get_current_user),
    days: int = 30
):
    """
    Get comprehensive user analytics for the specified number of days
    """
    try:
        logger.info(f"Getting analytics for user: {current_user.id}, days: {days}")
        
        if days < 1 or days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Days parameter must be between 1 and 365"
            )
        
        result = await UserStatsService.get_user_analytics(current_user, days)
        logger.info(f"Analytics result keys: {list(result.keys())}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_user_analytics: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analytics error: {str(e)}"
        )


# Additional endpoints for profile management

@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_data: dict,  # You can create a proper schema for this
    current_user: User = Depends(get_current_user)
):
    """
    Update user profile information
    """
    try:
        logger.info(f"Updating profile for user: {current_user.id}")
        logger.info(f"Profile data: {profile_data}")
        
        # Update allowed fields based on what exists in the User model
        updated = False
        
        if "first_name" in profile_data and hasattr(current_user, 'first_name'):
            current_user.first_name = profile_data["first_name"]
            updated = True
            
        if "last_name" in profile_data and hasattr(current_user, 'last_name'):
            current_user.last_name = profile_data["last_name"]
            updated = True
            
        if "full_name" in profile_data and hasattr(current_user, 'full_name'):
            current_user.full_name = profile_data["full_name"]
            updated = True
        
        if updated:
            await current_user.save()
            logger.info("Profile updated successfully")
        else:
            logger.warning("No valid fields found to update")
        
        result = await UserProfileService.get_user_profile(current_user)
        logger.info(f"Updated profile result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in update_user_profile: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.delete("/account")
async def delete_user_account(current_user: User = Depends(get_current_user)):
    """
    Delete user account and all associated data
    """
    try:
        logger.info(f"Deleting account for user: {current_user.id}")
        logger.warning("Account deletion requested - this is a destructive operation")
        
        # This should be implemented carefully with proper data cleanup
        # You might want to soft delete or anonymize data instead
        
        documents_deleted = 0
        rejected_docs_deleted = 0
        
        try:
            # Delete user's documents first
            from app.models.document import AcceptedDocument
            from app.models.rejected_document import RejectedDocument
            
            logger.info("Attempting to delete user documents...")
            
            # Delete accepted documents
            accepted_result = await AcceptedDocument.find(
                AcceptedDocument.user_id == current_user.id
            ).delete()
            documents_deleted = accepted_result.deleted_count if accepted_result else 0
            logger.info(f"Deleted {documents_deleted} accepted documents")
            
            # Delete rejected documents
            rejected_result = await RejectedDocument.find(
                RejectedDocument.user_id == current_user.id
            ).delete()
            rejected_docs_deleted = rejected_result.deleted_count if rejected_result else 0
            logger.info(f"Deleted {rejected_docs_deleted} rejected documents")
            
        except ImportError as import_error:
            logger.warning(f"Could not import document models: {import_error}")
            # Continue with user deletion even if document models don't exist
        except Exception as doc_error:
            logger.error(f"Error deleting documents: {doc_error}")
            # Continue with user deletion even if document deletion fails
            # You might want to fail here instead, depending on your requirements
        
        # Delete user account
        logger.info("Deleting user account...")
        await current_user.delete()
        
        logger.info(f"Successfully deleted user account: {current_user.id}")
        logger.info(f"Total cleanup: {documents_deleted} accepted docs, {rejected_docs_deleted} rejected docs")
        
        return {
            "message": "Account deleted successfully",
            "documentsDeleted": documents_deleted,
            "rejectedDocumentsDeleted": rejected_docs_deleted
        }
        
    except Exception as e:
        logger.error(f"Error in delete_user_account: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )


# Health check endpoint for this router
@router.get("/health")
async def user_health_check():
    """Health check for user endpoints"""
    try:
        # Test basic imports
        from app.models.user import User
        from app.services.user_profile import UserProfileService
        
        return {
            "status": "healthy",
            "message": "User endpoints are working",
            "imports": "successful"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )
    