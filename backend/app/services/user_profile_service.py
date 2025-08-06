# app/services/user_profile_service.py

from datetime import datetime, timedelta
import logging
from typing import List, Optional, Dict, Any
from beanie import PydanticObjectId

from app.models.user import User
from app.models.document import AcceptedDocument
from app.models.rejected_document import RejectedDocument
from app.schemas.user import (
    UserProfileResponse,
    ActivityStatsResponse,
    NotificationResponse,
    RecentActivityResponse,
    AIAssistantSummaryResponse
)

logger = logging.getLogger("app.services.user_profile_service")


class UserProfileService:
    """Service class for user profile related operations"""
    
    @staticmethod
    async def get_user_profile(user: User) -> UserProfileResponse:
        """
        Get user profile information and update last login
        """
        try:
            logger.info(f"Processing user profile for user ID: {user.id}")
            logger.debug(f"User fields available: {list(user.__dict__.keys())}")


            # Update last_login
            try:
                if hasattr(user, 'last_login'):
                    user.last_login = datetime.utcnow()
                    logger.debug("Updated existing last_login field")
                else:
                    # Dynamically add the field if it doesn't exist
                    setattr(user, 'last_login', datetime.utcnow())
                    logger.debug("Added new last_login field")
                
                await user.save()
                logger.debug("User saved successfully with last_login update")
                
            except Exception as save_error:
                logger.warning(f"Could not update last_login: {save_error}")

            # Handle name construction based on available fields
            name = ""

            # Check for first_name and last_name combination
            if hasattr(user, 'first_name') and hasattr(user, 'last_name'):
                first = getattr(user, 'first_name', '') or ''
                last = getattr(user, 'last_name', '') or ''
                name = f"{first} {last}".strip()
                logger.debug(f"Using first_name + last_name: '{name}'")
                
            # Fallback to full_name if available and no name constructed yet
            elif hasattr(user, 'full_name') and user.full_name:
                name = user.full_name.strip()
                logger.debug(f"Using full_name: '{name}'")
                
            # Final fallback to email username
            if not name:
                name = user.email.split('@')[0]
                logger.debug(f"Using email fallback: '{name}'")
            
            # Get role with fallback
            role = getattr(user, 'role', 'User')
            
            # Get last_login with fallback
            last_login = getattr(user, 'last_login', datetime.utcnow())
            
            response = UserProfileResponse(
                name=name,
                email=user.email,
                role=role,
                lastLogin=last_login
            )

            logger.info(f"Successfully created user profile response for {user.email}")
            return response
        

        except Exception as e:
            logger.error(f"Failed to get user profile: {str(e)}")
            logger.error(f"User object dict: {user.__dict__}")
            raise Exception(f"Failed to get user profile: {str(e)}")
        


    @staticmethod
    async def get_activity_stats(user: User) -> ActivityStatsResponse:
        """
        Get user's activity statistics
        """
        try:
           
            logger.info(f"Getting activity stats for user: {user.id}")
            
            documents_uploaded = 0
            contracts_analyzed = 0
            questions_answered = 0


            try:
                logger.debug("AcceptedDocument model imported successfully")
                documents_uploaded = await AcceptedDocument.find(
                    AcceptedDocument.user_id == user.id
                ).count()
                logger.debug(f"Documents uploaded: {documents_uploaded}")

                # Count contracts analyzed (documents with completed analysis)
                contracts_analyzed = await AcceptedDocument.find(
                    AcceptedDocument.user_id == user.id,
                    AcceptedDocument.analysis_status == "completed"
                ).count()
                logger.debug(f"Contracts analyzed: {contracts_analyzed}")

                # Count questions answered (documents with questions_asked field)
                questions_answered = await AcceptedDocument.find(
                    AcceptedDocument.user_id == user.id,
                    AcceptedDocument.questions_asked.exists(True)
                ).count()
                logger.debug(f"Questions answered: {questions_answered}")
            
            
            except ImportError as import_error:
                logger.warning(f"Could not import AcceptedDocument model: {import_error}")
                logger.info("Using default values for activity stats")
                
            except AttributeError as attr_error:
                logger.warning(f"Document model missing expected fields: {attr_error}")
                logger.info("Using default values for activity stats")
                
            except Exception as query_error:
                logger.error(f"Error querying documents: {query_error}")
                logger.info("Using default values for activity stats")
            
            
            response = ActivityStatsResponse(
                documentsUploaded=documents_uploaded,
                contractsAnalyzed=contracts_analyzed,
                questionsAnswered=questions_answered
            )

            logger.info(f"Activity stats response: uploaded={documents_uploaded}, analyzed={contracts_analyzed}, questions={questions_answered}")
            return response
        

        except Exception as e:
            logger.error(f"Failed to get activity stats: {str(e)}")
            raise Exception(f"Failed to get activity stats: {str(e)}")
        


    @staticmethod
    async def get_user_notifications(user: User, limit: int = 10) -> List[NotificationResponse]:
        """
        Get user's notifications based on their current state and recent activity
        """
        try:

            logger.info(f"Getting notifications for user: {user.id}, limit: {limit}")
            notifications = []
            
            is_verified = getattr(user, 'is_verified', True)
            if not is_verified:
                notifications.append(NotificationResponse(
                    id="email_verification",
                    message="Your email is not verified. Please check your inbox and verify your email.",
                    type="warning",
                    createdAt=datetime.utcnow()
                ))
                logger.debug("Added email verification notification")

            
            # Check if account is active
            is_active = getattr(user, 'is_active', True)
            if not is_active:
                notifications.append(NotificationResponse(
                    id="account_inactive",
                    message="Your account is inactive. Please contact support.",
                    type="warning",
                    createdAt=datetime.utcnow()
                ))
                logger.debug("Added account inactive notification")
            
            try:
            # Check for recent document uploads
                recent_docs_count = await AcceptedDocument.find(
                    AcceptedDocument.user_id == user.id,
                    AcceptedDocument.created_at >= datetime.utcnow() - timedelta(hours=24)
                ).count()
            
                if recent_docs_count > 0:
                    notifications.append(NotificationResponse(
                        id="recent_upload",
                        message=f"Document analysis complete for {recent_docs_count} files",
                        type="success",
                        createdAt=datetime.utcnow() - timedelta(hours=2)
                    ))
                    logger.debug(f"Added recent upload notification for {recent_docs_count} documents")

            
                # Check for rejected documents
                rejected_docs_count = await RejectedDocument.find(
                    RejectedDocument.user_id == user.id,
                    RejectedDocument.created_at >= datetime.utcnow() - timedelta(days=7)
                ).count()
            
                if rejected_docs_count > 0:
                    notifications.append(NotificationResponse(
                        id="rejected_docs",
                        message=f"{rejected_docs_count} documents were rejected this week",
                        type="warning",
                        createdAt=datetime.utcnow() - timedelta(days=1)
                    ))

                    logger.debug(f"Added rejected documents notification for {rejected_docs_count} documents")

            
                # Check for pending documents
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

                    logger.debug(f"Added pending analysis notification for {pending_docs_count} documents")
            
            except ImportError:
                logger.warning("Document models not available, skipping document-related notifications")
            except Exception as doc_error:
                logger.warning(f"Could not fetch document-related notifications: {doc_error}")
            
            # Add a welcome notification if user has no other notifications
            if not notifications:
                notifications.append(NotificationResponse(
                    id="welcome",
                    message="Welcome to LawLens! Start by uploading your first legal document for analysis.",
                    type="info",
                    createdAt=datetime.utcnow() - timedelta(hours=1)
                ))
                logger.debug("Added welcome notification")


            # Sort notifications by creation time (newest first) and limit
            notifications.sort(key=lambda x: x.createdAt, reverse=True)
            result = notifications[:limit]

            logger.info(f"Returning {len(result)} notifications")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get notifications: {str(e)}")
            raise Exception(f"Failed to get notifications: {str(e)}")



    @staticmethod
    async def get_recent_activity(user: User, limit: int = 10) -> List[RecentActivityResponse]:
        """
        Get user's recent activity based on document operations
        """
        try:

            logger.info(f"Getting recent activity for user: {user.id}, limit: {limit}")

            activities = []

            try:
            
                # Get recent accepted documents
                recent_accepted = await AcceptedDocument.find(
                    AcceptedDocument.user_id == user.id
                ).sort(-AcceptedDocument.created_at).limit(limit).to_list()
            
                for doc in recent_accepted:
                    # Determine action based on document status
                    action = "Uploaded"
                    if getattr(doc, 'analysis_status', None) == "completed":
                        action = "Analyzed"
                    elif getattr(doc, 'analysis_status', None) == "processing":
                        action = "Processing"
                    elif getattr(doc, 'analysis_status', None) == "pending":
                        action = "Pending Analysis"
                
                filename = getattr(doc, 'filename', 'Unknown File')
                
                activities.append(RecentActivityResponse(
                    id=str(doc.id),
                    action=action,
                    fileName=filename,
                    timestamp=doc.created_at
                ))

                logger.debug(f"Found {len(activities)} accepted document activities")
            
                # Get recent rejected documents if we need more activities
                if len(activities) < limit:
                    remaining_limit = limit - len(activities)
                    recent_rejected = await RejectedDocument.find(
                        RejectedDocument.user_id == user.id
                    ).sort(-RejectedDocument.created_at).limit(remaining_limit).to_list()
                
                    for doc in recent_rejected:
                        activities.append(RecentActivityResponse(
                            id=str(doc.id),
                            action="Rejected",
                            fileName=doc.filename,
                            timestamp=doc.created_at
                        ))

                        logger.debug(f"Added {len(recent_rejected)} rejected document activities")
            
            except ImportError:
                logger.warning("Document models not available")
            except Exception as doc_error:
                logger.warning(f"Could not get document activities: {doc_error}")
            

            # Add account creation activity if no other activities found
            if not activities:
                activities.append(RecentActivityResponse(
                    id="account_created",
                    action="Account Created",
                    fileName="Welcome to LawLens",
                    timestamp=getattr(user, 'created_at', datetime.utcnow())
                ))
                logger.debug("Added account creation activity")
            
            # Sort all activities by timestamp (newest first)
            activities.sort(key=lambda x: x.timestamp, reverse=True)
            result = activities[:limit]

            logger.info(f"Returning {len(result)} activities")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get recent activity: {str(e)}")
            raise Exception(f"Failed to get recent activity: {str(e)}")


    @staticmethod
    async def get_ai_summary(user: User) -> AIAssistantSummaryResponse:
        """
        Get AI assistant summary with weekly statistics
        """
        try:
            logger.info(f"Getting AI summary for user: {user.id}")
            week_ago = datetime.utcnow() - timedelta(days=7)

            documents_this_week = 0
            contract_reviews = 0
            weekly_questions = 0
            most_active_day = "Monday"  # Default

            try:
                # Documents uploaded this week
                documents_this_week = await AcceptedDocument.find(
                    AcceptedDocument.user_id == user.id,
                    AcceptedDocument.created_at >= week_ago
                ).count()
            
                # Contract reviews this week (documents analyzed)
                contract_reviews = await AcceptedDocument.find(
                    AcceptedDocument.user_id == user.id,
                    AcceptedDocument.analysis_status == "completed",
                    AcceptedDocument.updated_at >= week_ago
                ).count()
                logger.debug(f"Documents this week: {documents_this_week}")

                # Contract reviews this week (documents analyzed)
                contract_reviews = await AcceptedDocument.find(
                    AcceptedDocument.user_id == user.id,
                    AcceptedDocument.analysis_status == "completed",
                    AcceptedDocument.updated_at >= week_ago
                    ).count()
                logger.debug(f"Contract reviews: {contract_reviews}")
            
                # Questions asked this week (simplified - based on documents with questions)
                weekly_questions = await AcceptedDocument.find(
                    AcceptedDocument.user_id == user.id,
                    AcceptedDocument.questions_asked.exists(True),
                    AcceptedDocument.created_at >= week_ago
                ).count()
                logger.debug(f"Weekly questions: {weekly_questions}")

                most_active_day = await UserProfileService._get_most_active_day(user.id)
                logger.debug(f"Most active day: {most_active_day}")

            except ImportError:
                logger.warning("Document model not available for AI summary")
            except Exception as doc_error:
                logger.warning(f"Could not get document data for AI summary: {doc_error}")
            
            response = AIAssistantSummaryResponse(
                weeklyQuestions=weekly_questions,
                documentsThisWeek=documents_this_week,
                mostActiveDay=most_active_day,
                contractReviews=contract_reviews
            )

            logger.info(f"AI summary: questions={weekly_questions}, docs={documents_this_week}, reviews={contract_reviews}, active_day={most_active_day}")
            return response
        

        except Exception as e:
            logger.error(f"Failed to get AI summary: {str(e)}")
            raise Exception(f"Failed to get AI summary: {str(e)}")



    @staticmethod
    async def _get_most_active_day(user_id: PydanticObjectId) -> str:
        """
        Analyze user's document activity to find the most active day of the week
        Using MongoDB aggregation pipeline
        """
        try:
            pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "created_at": {"$gte": datetime.utcnow() - timedelta(days=30)}
                    }
                },
                {
                    "$group": {
                        "_id": {"$dayOfWeek": "$created_at"},  # 1=Sunday, 2=Monday, etc.
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"count": -1}},
                {"$limit": 1}
            ]
            
            result = await AcceptedDocument.aggregate(pipeline).to_list()
            
            if result and len(result) > 0:
                day_number = result[0]["_id"]
                days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
                return days[day_number - 1]  # MongoDB dayOfWeek is 1-indexed
            
        except Exception as e:
            logger.debug(f"Could not determine most active day: {e}")
        
        return "Monday"  # Default fallback


class UserStatsService:
    """Service class for advanced user statistics and analytics"""
    
    @staticmethod
    async def get_user_analytics(user: User, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive user analytics for the specified number of days
        """
        try:

            logger.info(f"Getting analytics for user: {user.id}, days: {days}")

            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            daily_activity = []
            doc_type_distribution = []
            processing_stats = {
                "statusDistribution": [],
                "totalDocuments": 0
            }

            try:
                daily_activity = await UserStatsService._get_daily_activity(user.id, cutoff_date)
                logger.debug(f"Daily activity entries: {len(daily_activity)}")

                doc_type_distribution = await UserStatsService._get_document_type_distribution(user.id)
                logger.debug(f"Document type entries: {len(doc_type_distribution)}")
                
                # Get processing time statistics
                processing_stats = await UserStatsService._get_processing_statistics(user.id)
                logger.debug(f"Processing stats: {processing_stats}")
            
            except ImportError:
                logger.warning("Document model not available for analytics")
            except Exception as analytics_error:
                logger.warning(f"Could not get analytics data: {analytics_error}")

            
            result = {
                "dailyActivity": daily_activity,
                "documentTypeDistribution": doc_type_distribution,
                "processingStatistics": processing_stats,
                "period": f"Last {days} days"
            }

            logger.info(f"Analytics result prepared for {days} days")
            return result
        

        except Exception as e:
            logger.error(f"Failed to get user analytics: {str(e)}")
            raise Exception(f"Failed to get user analytics: {str(e)}")
    
    @staticmethod
    async def _get_daily_activity(user_id: PydanticObjectId, cutoff_date: datetime) -> List[Dict]:
        """Get daily activity counts using aggregation"""

        try:
            pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "created_at": {"$gte": cutoff_date}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$created_at"
                            }
                        },
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"_id": 1}}
            ]
            
            return await AcceptedDocument.aggregate(pipeline).to_list()
        
        except Exception as e:
                logger.warning(f"Could not get daily activity: {e}")
                return []


    @staticmethod
    async def _get_document_type_distribution(user_id: PydanticObjectId) -> List[Dict]:
        """Get document type distribution"""
        pipeline = [
            {"$match": {"user_id": user_id}},
            {
                "$group": {
                    "_id": "$document_type",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}}
        ]
        
        return await AcceptedDocument.aggregate(pipeline).to_list()
    

    
    @staticmethod
    async def _get_processing_statistics(user_id: PydanticObjectId) -> Dict[str, Any]:
        """Get processing time and status statistics"""
        pipeline = [
            {"$match": {"user_id": user_id}},
            {
                "$group": {
                    "_id": "$analysis_status",
                    "count": {"$sum": 1},
                    "avgProcessingTime": {
                        "$avg": {
                            "$subtract": ["$updated_at", "$created_at"]
                        }
                    }
                }
            }
        ]
        
        results = await AcceptedDocument.aggregate(pipeline).to_list()
        
        # Convert milliseconds to readable format
        for result in results:
            if result.get("avgProcessingTime"):
                # Convert from milliseconds to minutes
                result["avgProcessingTimeMinutes"] = result["avgProcessingTime"] / (1000 * 60)
        
        return {
            "statusDistribution": results,
            "totalDocuments": sum(r["count"] for r in results)
        }