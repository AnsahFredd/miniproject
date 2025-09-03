from beanie import Document
from pydantic import EmailStr, Field, field_validator
from datetime import datetime, timezone
from typing import Optional
from app.utils.validators import TimezoneAwareMixin



def get_current_utc_time():
    """Utility function to get current UTC time"""
    return datetime.now(timezone.utc)

class User(Document, TimezoneAwareMixin):
    email: EmailStr
    full_name: Optional[str] = None
    first_name: Optional[str] = None  
    last_name: Optional[str] = None   
    hashed_password: str
    is_active: bool = False
    is_verified: bool = False
    role: str = "User"
    created_at: datetime = Field(default_factory=get_current_utc_time)
    last_login: Optional[datetime] = None

    # Email confirmation 
    confirmation_token: Optional[str] = None
    confirmation_token_expires: Optional[datetime] = None


    reset_token: Optional[str] = None
    reset_token_expires: Optional[datetime] = None

    __timezone_fields__ = ["confirmation_token_expires", "reset_token_expires"]

    class Settings:
        name = "users"
    


class PasswordResetToken(Document, TimezoneAwareMixin):
    token: str = Field(..., unique=True)
    email: EmailStr
    expires_at: datetime
    used: bool = False
    created_at: datetime = Field(default_factory=get_current_utc_time)

    __timezone_fields__ = ["expires_at"]

    class Settings:
        name = "password_reset_tokens"
        indexes = [
            "token",
            "email",
            "expires_at"
        ]

