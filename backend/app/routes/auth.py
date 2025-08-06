from fastapi import APIRouter, Depends, Request, Response, Cookie, status, BackgroundTasks, HTTPException
from app.schemas.auth import (
    SignupRequest, 
    LoginRequest, 
    TokenResponse, 
    EmailResetResponse, 
    PasswordResetRequest, 
    PasswordResetConfirm,
    MessageResponse, 
    ResendConfirmationRequest
    )

from app.schemas.user import UserRead
from fastapi.responses import RedirectResponse
from app.services.auth_service import (
    signup_user, 
    login_user,
    refresh_access_token,
    logout_user,
    request_password_reset,
    reset_password,
    verify_reset_token,
    confirm_user_email,
    resend_confirmation_email
)
from app.core.config import settings
from app.dependencies.auth import get_current_user
import logging

logger = logging.getLogger()

router = APIRouter(tags=["Authentication"])


@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=MessageResponse)
async def signup(payload: SignupRequest, response: Response,background_tasks: BackgroundTasks):
    return await signup_user(payload, response, background_tasks)

@router.get("/confirm-email")
async def confirm_email(token: str = None):
    if not token:
        # If no token provided, redirect to frontend error page
        return RedirectResponse(
            url=f"{settings.CORS_ORIGINS}/confirm-email?status=error&message=no_token",
            status_code=status.HTTP_303_SEE_OTHER
        )
    
    try:
        logger.info(f"Attempting email confirmation with token: {token[:20]}...")
        result = await confirm_user_email(token)  

        # Check if already confirmed
        if result.get("already_confirmed"):
            logger.info("Email was already confirmed, redirecting to login")
            return RedirectResponse(
                url=f"{settings.CORS_ORIGINS}/confirm-email?status=already_confirmed&message=Email already confirmed",
                status_code=status.HTTP_303_SEE_OTHER
            )
        
        logger.info("Email confirmation successful, redirecting to confirm page")

        
        # Redirect to frontend SUCCESS page (not login page)
        return RedirectResponse(
            url=f"{settings.CORS_ORIGINS}/confirm-email?status=success&message=Email confirmed successfully",
            status_code=status.HTTP_303_SEE_OTHER
        )
    
    except HTTPException as e:
        logger.error(f"HTTPException during email confirmation: {e.status_code} - {e.detail}")
        
        # Special handling for invalid token case (likely already confirmed)
        if "Invalid or expired confirmation token" in str(e.detail):
            return RedirectResponse(
                url=f"{settings.CORS_ORIGINS}/confirm-email?status=info&message=If_you_have_already_confirmed_your_email_please_log_in",
                status_code=status.HTTP_303_SEE_OTHER
            )
        
        error_message = str(e.detail).replace(" ", "_").replace(".", "")
        return RedirectResponse(
            url=f"{settings.CORS_ORIGINS}/confirm-email?status=error&message={error_message}",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"Unexpected error during email confirmation: {str(e)}")
        return RedirectResponse(
            url=f"{settings.CORS_ORIGINS}/confirm-email?status=error&message=confirmation_failed",
            status_code=status.HTTP_303_SEE_OTHER
        )
        
    except HTTPException as e:
        # Redirect to frontend with specific error
        error_message = str(e.detail).replace(" ", "_").replace(".", "")
        return RedirectResponse(
            url=f"{settings.CORS_ORIGINS}/confirm-email?status=error&message={error_message}",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"Unexpected error during email confirmation: {str(e)}")
        return RedirectResponse(
            url=f"{settings.CORS_ORIGINS}/confirm-email?status=error&message=confirmation_failed",
            status_code=status.HTTP_303_SEE_OTHER
        )   


@router.post("/resend-confirmation", response_model=MessageResponse)
async def resend_confirmation(payload: ResendConfirmationRequest, background_tasks: BackgroundTasks):
    email = payload.email
    if not email:
        raise HTTPException(
            status_code=400, detail="Email is required"
        )
    return await resend_confirmation_email(email, background_tasks)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, response: Response):
    return await login_user(payload, response)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request, response: Response, refresh_token: str = Cookie(None)):
    return await refresh_access_token(request, response, refresh_token)


@router.post("/logout")
async def logout(response: Response):
    await logout_user(response)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserRead)
async def get_profile(user: UserRead = Depends(get_current_user)):
    return user 


# Password Reset Endpoints
@router.post("/forgot-password", response_model=EmailResetResponse)
async def forgot_password(payload: PasswordResetRequest, background_tasks: BackgroundTasks):
    """"Reuest password reset link"""
    return await request_password_reset(payload, background_tasks)

@router.post("/password-reset", response_model=EmailResetResponse)
async def reset_password_endpoint(payload: PasswordResetConfirm):
    """"Reset password using token"""
    return await reset_password(payload)

@router.get("/verify-reset-token/{token}")
async def verify_token_endpoint(token: str):
    """Verify password reset token"""
    return await verify_reset_token(token)
