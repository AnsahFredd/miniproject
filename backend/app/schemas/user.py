from pydantic import BaseModel, EmailStr, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
from app.schemas.common import PyObjectId
from bson import ObjectId
from pydantic import BaseModel, Field, EmailStr
from app.schemas.common import PyObjectId
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None




class UserRead(BaseModel):
    id: str = Field(..., alias="_id")
    email: EmailStr
    full_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class UserProfileResponse(BaseModel):
    name: str
    email: str
    role: str
    lastLogin: Optional[datetime] = None



class ActivityStatsResponse(BaseModel):
    documentsUploaded: int
    contractsAnalyzed: int
    questionsAnswered: int


class NotificationResponse(BaseModel):
    id: str
    message: str
    type: str  # 'warning', 'info', 'success'
    createdAt: datetime


class RecentActivityResponse(BaseModel):
    id: str
    action: str
    fileName: str
    timestamp: datetime


class AIAssistantSummaryResponse(BaseModel):
    weeklyQuestions: int
    documentsThisWeek: int
    mostActiveDay: str
    contractReviews: int


class UserAnalyticsResponse(BaseModel):
    dailyActivity: List[Dict[str, Any]]
    documentTypeDistribution: List[Dict[str, Any]]
    processingStatistics: Dict[str, Any]
    period: str


class DailyActivityItem(BaseModel):
    date: str
    count: int


class DocumentTypeDistribution(BaseModel):
    documentType: str
    count: int


class ProcessingStatistics(BaseModel):
    statusDistribution: List[Dict[str, Any]]
    totalDocuments: int