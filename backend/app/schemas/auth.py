# app/schemas/auth.py
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.schemas.user import UserRead

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class MessageResponse(BaseModel):
    message: str 

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class EmailVerificationRequest(BaseModel):
    token: str


class TokenResponse(BaseModel):
    accessToken: str
    refreshToken: str
    user: UserRead

# Password Reset Schemas
class PasswordResetRequest(BaseModel):
    """Schema for password reset request"""
    email: EmailStr = Field(..., description="Email address ti send reset link to")

class PasswordResetConfirm(BaseModel):
    """Schema for confirming password reset"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password to set")

class EmailResetResponse(BaseModel):
    """Schema for email reset response"""
    message: str = Field(..., description="Response message")
    success: bool = Field(..., description="Whether the reset was successful")

class TokenValidatinResponse(BaseModel):
    """Schema for validating reset token"""
    valid: bool = Field(..., description="Whether the reset token is valid")
    email: Optional[str] = Field(None, description="Validation message")

class ResendConfirmationRequest(BaseModel):
    email: str

