"""Enhanced authentication routes with improved error handling."""

from fastapi import APIRouter, Depends, Request, Response, Cookie, BackgroundTasks
from fastapi.responses import RedirectResponse
from typing import Optional
import logging

from app.schemas.auth import (
    SignupRequest, LoginRequest, TokenResponse, 
    PasswordResetRequest, PasswordResetConfirm,
    ResendConfirmationRequest
)
from app.schemas.user import UserRead
from app.services.auth.signup import signup_user, confirm_user_email, resend_confirmation_email
from app.services.auth.login import login_user, logout_user, refresh_access_token
from app.services.auth.password_reset import reset_password, verify_reset_token, request_password_reset
from app.dependencies.auth import get_current_user
from app.core.config import settings
from ..core.exceptions import APIError, AuthenticationError, ValidationError
from ..core.response_models import create_success_response

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Authentication"])

@router.post("/signup")
async def signup(
    request: Request,
    payload: SignupRequest,
    response: Response,
    background_tasks: BackgroundTasks
):
    """Register a new user account."""
    try:
        result = await signup_user(payload, background_tasks)
        
        return create_success_response(
            data={"email": payload.email},
            message="Account created successfully. Please check your email to confirm your account.",
            request_id=getattr(request.state, 'request_id', None)
        )
        
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        if "already exists" in str(e).lower():
            raise ValidationError(
                message="An account with this email already exists",
                field_errors={"email": "This email is already registered"}
            )
        elif "invalid email" in str(e).lower():
            raise ValidationError(
                message="Invalid email format",
                field_errors={"email": "Please enter a valid email address"}
            )
        else:
            raise APIError(
                message="Failed to create account",
                status_code=500,
                error_code="SIGNUP_ERROR",
                user_action="Please try again or contact support if the problem persists"
            )

@router.post("/login")
async def login(
    request: Request,
    payload: LoginRequest,
    response: Response
):
    """Authenticate user and return access tokens."""
    try:
        result = await login_user(payload, response)
        
        return create_success_response(
            data=result,
            message="Login successful",
            request_id=getattr(request.state, 'request_id', None)
        )
    

    except AuthenticationError as auth_err:
        # Explicitly catch authentication-related errors
        logger.warning(f"Authentication failed: {str(auth_err)}")
        raise auth_err
    

    except Exception as e:
        # Log full exception with type and stacktrace
        logger.exception(f"Unexpected login error: {type(e).__name__}: {str(e)}")

        # Try to interpret known messages
        msg_lower = str(e).lower()
        if "invalid credentials" in msg_lower or "not found" in msg_lower:
            raise AuthenticationError("Invalid email or password")
        elif "not confirmed" in msg_lower:
            raise AuthenticationError("Please confirm your email address before logging in")
        else:
            raise APIError(
                message="Login failed due to server error",
                status_code=500,
                error_code="LOGIN_ERROR",
                user_action="Please try again or contact support"
            )

            

@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    refresh_token: Optional[str] = Cookie(None)
):
    """Refresh access token using refresh token."""
    try:
        if not refresh_token:
            raise AuthenticationError("Refresh token required")
        
        result = await refresh_access_token(request, response, refresh_token)
        
        return create_success_response(
            data=result,
            message="Token refreshed successfully",
            request_id=getattr(request.state, 'request_id', None)
        )
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise AuthenticationError("Invalid or expired refresh token")

@router.post("/logout")
async def logout(
    request: Request,
    response: Response
):
    """Logout user and clear tokens."""
    try:
        await logout_user(response)
        
        return create_success_response(
            message="Logged out successfully",
            request_id=getattr(request.state, 'request_id', None)
        )
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        # Even if logout fails, we should clear client-side tokens
        return create_success_response(
            message="Logged out successfully",
            request_id=getattr(request.state, 'request_id', None)
        )

@router.get("/me")
async def get_profile(
    request: Request,
    user: UserRead = Depends(get_current_user)
):
    """Get current user profile."""
    return create_success_response(
        data=user,
        message="Profile retrieved successfully",
        request_id=getattr(request.state, 'request_id', None)
    )

@router.get("/confirm-email")
async def confirm_email(token: Optional[str] = None):
    """Confirm user email address."""
    if not token:
        return RedirectResponse(
            url=f"{settings.CORS_ORIGINS[0]}/confirm-email?status=error&message=no_token",
            status_code=303
        )
    
    try:
        result = await confirm_user_email(token)
        
        if result.get("already_confirmed"):
            return RedirectResponse(
                url=f"{settings.CORS_ORIGINS[0]}/confirm-email?status=already_confirmed",
                status_code=303
            )
        
        return RedirectResponse(
            url=f"{settings.CORS_ORIGINS[0]}/confirm-email?status=success",
            status_code=303
        )
        
    except Exception as e:
        logger.error(f"Email confirmation error: {str(e)}")
        error_message = "confirmation_failed"
        if "invalid" in str(e).lower() or "expired" in str(e).lower():
            error_message = "invalid_or_expired_token"
        
        return RedirectResponse(
            url=f"{settings.CORS_ORIGINS[0]}/confirm-email?status=error&message={error_message}",
            status_code=303
        )

@router.post("/resend-confirmation")
async def resend_confirmation(
    request: Request,
    payload: ResendConfirmationRequest,
    background_tasks: BackgroundTasks
):
    """Resend email confirmation."""
    try:
        result = await resend_confirmation_email(payload.email, background_tasks)
        
        return create_success_response(
            message="Confirmation email sent successfully",
            request_id=getattr(request.state, 'request_id', None)
        )
        
    except Exception as e:
        logger.error(f"Resend confirmation error: {str(e)}")
        raise APIError(
            message="Failed to send confirmation email",
            status_code=500,
            error_code="EMAIL_SEND_ERROR",
            user_action="Please try again or contact support"
        )

@router.post("/forgot-password")
async def forgot_password(
    request: Request,
    payload: PasswordResetRequest,
    background_tasks: BackgroundTasks
):
    """Request password reset."""
    try:
        result = await request_password_reset(payload, background_tasks)
        
        return create_success_response(
            message="Password reset email sent successfully",
            request_id=getattr(request.state, 'request_id', None)
        )
        
    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        # Don't reveal if email exists or not for security
        return create_success_response(
            message="If an account with that email exists, a password reset link has been sent",
            request_id=getattr(request.state, 'request_id', None)
        )

@router.post("/password-reset")
async def reset_password_endpoint(
    request: Request,
    payload: PasswordResetConfirm
):
    """Reset password using token."""
    try:
        result = await reset_password(payload)
        
        return create_success_response(
            message="Password reset successfully",
            request_id=getattr(request.state, 'request_id', None)
        )
        
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        if "invalid" in str(e).lower() or "expired" in str(e).lower():
            raise ValidationError(
                message="Invalid or expired reset token",
                field_errors={"token": "Reset token is invalid or has expired"}
            )
        else:
            raise APIError(
                message="Failed to reset password",
                status_code=500,
                error_code="PASSWORD_RESET_ERROR",
                user_action="Please try requesting a new password reset link"
            )

@router.get("/verify-reset-token/{token}")
async def verify_token_endpoint(
    token: str,
    request: Request
):
    """Verify password reset token."""
    try:
        result = await verify_reset_token(token)
        
        return create_success_response(
            data={"valid": True},
            message="Token is valid",
            request_id=getattr(request.state, 'request_id', None)
        )
        
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return create_success_response(
            data={"valid": False},
            message="Token is invalid or expired",
            request_id=getattr(request.state, 'request_id', None)
        )
