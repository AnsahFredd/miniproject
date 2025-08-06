import traceback
from fastapi import HTTPException, status, Response, Request, Cookie, BackgroundTasks
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from pymongo import WriteConcern
from pymongo.read_concern import ReadConcern
from pymongo.read_preferences import ReadPreference
from bson import ObjectId
from app.schemas.auth import PasswordResetConfirm, PasswordResetRequest, EmailResetResponse
from app.models.user import PasswordResetToken
from app.utils.email import (
    send_reset_email,
    send_password_changed_notification, 
    send_confirmation_email_with_retry
    )
from app.core.config import settings
import secrets
import logging

from app.crud.user_crud import get_user_by_email


is_production = settings.ENV == "production"

from app.core.config import settings
from app.models.user import User
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse
from app.schemas.user import UserRead

# Configure logging
logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def signup_user(payload: SignupRequest, response: Response, background_tasks: BackgroundTasks):
    """Register a new user and return authentication tokens."""
    client = User.get_motor_collection().database.client


    try:
        async with await client.start_session() as session:
            async with session.start_transaction(
                read_concern=ReadConcern("local"),
                write_concern=WriteConcern("majority"),
                read_preference=ReadPreference.PRIMARY,
            ):
                
                existing = await User.find_one(User.email == payload.email)
                if existing:
                    logger.warning(f"Email already registered: {payload.email}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already registered",
                    )

                hashed_password = pwd_context.hash(payload.password)
                confirmation_token = secrets.token_urlsafe(32)
                confirmation_token_expires = datetime.now(timezone.utc) + timedelta(hours=24)


                user = User(
                    full_name=payload.name,
                    email=payload.email,
                    hashed_password=hashed_password,
                    is_active=False,
                    is_verified=False,
                    confirmation_token=confirmation_token,
                    confirmation_token_expires=confirmation_token_expires
                )
                await user.insert()
                logger.info(f"New user created: {user.email}")

                # Queue confirmatin email AFTER successful database transaction
                background_tasks.add_task(
                    send_confirmation_email_with_retry,
                    user.email,
                    confirmation_token
                )

                logger.info(f"Confirmation email queued for {user.email}")

                return {
                    "message": "Registration successfull. Please check you email to confirm your accoun.",
                    "email": user.email,
                    "requires_confirmation": True
                }

    except Exception as e:
        logger.error(f"Signup failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

async def confirm_user_email(token: str):

    logger.info(f"Confirming email with token: {token}")

    user = await User.find_one(User.confirmation_token == token)
    if not user:
        logger.error(f"No user found with confirmation token: {token}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid confirmation token"
        )
    
    logger.info(f"User found: {user.email}, is_verified: {user.is_verified}")

    
    if user.confirmation_token_expires and user.confirmation_token_expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation token has expired"
        )
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already confirmed"
        )
    
    # Mark user as active and verified
    user.is_active = True
    user.is_verified = True
    user.confirmation_token = None
    user.confirmation_token_expires = None
    await user.save()

    logger.info(f"Email confirmed for user: {user.email}")
    return {"message": "Email confirmed successfully", "email": user.email}


async def resend_confirmation_email(email: str, background_tasks: BackgroundTasks):
    user = await User.find_one(User.email == email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already confirmed"
        )
    
     # Generate new token and expiry
    confirmation_token = secrets.token_urlsafe(32)
    confirmation_token_expires = datetime.now(timezone.utc) + timedelta(hours=24)
    user.confirmation_token = confirmation_token
    user.confirmation_token_expires = confirmation_token_expires
    await user.save()

    # Queue email in background
    background_tasks.add_task(
        send_confirmation_email_with_retry,
        user.email,
        confirmation_token
    )

    logger.info(f"Confirmation email resent for: {user.email}")
    return {"message": "Confirmation email resent. Please check your inbox."}
    


async def login_user(payload: LoginRequest, response: Response) -> TokenResponse:
    """Authenticate user and return authentication tokens."""
    try:
        client = User.get_motor_collection().database.client
        async with await client.start_session() as session:
            async with session.start_transaction(
                read_concern=ReadConcern("local"),
                write_concern=WriteConcern("majority"),
                read_preference=ReadPreference.PRIMARY,
            ):
                user = await User.find_one(User.email == payload.email)
                if not user or not pwd_context.verify(payload.password, user.hashed_password):
                    logger.warning(f"Failed login attempt for email: {payload.email}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid credentials",
                    )

                # Check if email is verified
                if not user.is_verified:
                    logger.warning(f"Login attempt with unverified email: {payload.email}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Please verify your email address before logging in. Check your inbox for the confirmation email.",
                    )

                # Check if user account is active
                if not user.is_active:
                    logger.warning(f"Login attempt for inactive user: {payload.email}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Your account has been deactivated. Please contact support.",
                    )

        access_token = _create_access_token(str(user.id))
        refresh_token = _create_refresh_token(str(user.id))
        _set_refresh_cookie(response, refresh_token)
        logger.info(f"User logged in successfully: {user.email}")

        user_data = user.model_dump(by_alias=True)
        user_data["_id"] = str(user_data["_id"])  # Convert ObjectId to str

        return TokenResponse(
            accessToken=access_token,
            refreshToken=refresh_token,
            user=UserRead.model_validate(user_data)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed for {payload.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

async def refresh_access_token(
    request: Request, response: Response, refresh_token: str = Cookie(None, alias="refresh_token")
) -> TokenResponse:
    """Generate a new access token using a valid refresh token."""
    logger.info(f"Refresh attempt. Cookies: {list(request.cookies.keys())}")

    if not refresh_token:
        logger.warning("Refresh attempt with missing token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )

    try:
        payload = jwt.decode(
            refresh_token,
            settings.JWT_REFRESH_TOKEN,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if not user_id:
            logger.warning("Refresh token with empty payload")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        user = await User.find_one(User.id == ObjectId(user_id))
        if not user:
            logger.warning(f"Refresh attempt for non-existent user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        new_access_token = _create_access_token(user_id)
        new_refresh_token = _create_refresh_token(user_id)
        _set_refresh_cookie(response, new_refresh_token)
        logger.info(f"Token refreshed for user: {user.email}")

        user_dict = user.model_dump()
        return TokenResponse(
            accessToken=new_access_token,
            refreshToken=new_refresh_token,
            user=UserRead.model_validate(user_dict)
        )


    except JWTError as e:
        logger.warning(f"Invalid refresh token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    except Exception as e:
        logger.error(f"Refresh token processing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


async def logout_user(response: Response):
    """Clear authentication cookies."""
    try:
        response.delete_cookie(
            key="refresh_token",
            path="/",
            secure=is_production,
            domain=None,
            samesite="none" if is_production else "lax"
        )
        logger.info("User logged out successfully")
        return {"message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


def _create_access_token(user_id: str) -> str:
    """Generate a new JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": user_id, "exp": expire}
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)


def _create_refresh_token(user_id: str) -> str:
    """Generate a new JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"sub": user_id, "exp": expire}
    return jwt.encode(to_encode, settings.JWT_REFRESH_TOKEN, algorithm=settings.ALGORITHM)


def _set_refresh_cookie(response: Response, refresh_token: str):
    """Set the refresh token as an HTTP-only cookie with production-ready configuration."""
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_production,
        samesite="none" if is_production else "lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path="/",
        domain=None
    )


def to_user_read(user: User) -> UserRead:
    data = user.model_dump(by_alias=True)
    data["_id"] = str(data["_id"])
    return UserRead.model_validate(data)


def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)

def get_token_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=1)

def is_token_expired(expires_at: datetime) -> bool:
    # Check if token has expired
    current_time = datetime.now(timezone.utc)
    # Ensure expires_at is timezone-aware
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return current_time > expires_at

async def request_password_reset(
    payload: PasswordResetRequest,
    background_tasks: BackgroundTasks
) -> EmailResetResponse:
    """Request password reset by sending reset link to email"""
    try:
        logger.info(f"Payload received: {payload}") 


        # Check if user exists
        user = await get_user_by_email(payload.email)
        logger.info(f"User fetched for reset: {user}")


        # Always return the same response to prevent leaking which emails exist
        generic_response = EmailResetResponse(
            message="We've sent a password reset link to your email.",
            success=True
        )

        if not user:
            logger.info(f"Password reset requested for non-existing email: {payload.email}")
            return generic_response

        # Generate reset token
        reset_token = generate_reset_token()
        expires_at = get_token_expiry()

        # Check if there's an existing valid (not used and not expired) token
        existing_token = await PasswordResetToken.find_one({
            "$and": [
                {"email": payload.email},
                {"used": False},
                {"expires_at": {"$gt": datetime.now(timezone.utc)}}
            ]
        })

        if existing_token:
            # Update the existing token
            existing_token.token = reset_token
            existing_token.expires_at = expires_at
            existing_token.created_at = datetime.now(timezone.utc)
            await existing_token.save()
        else:
            # Create a new reset token
            db_token = PasswordResetToken(
                token=reset_token,
                email=payload.email,
                expires_at=expires_at,
                used=False
            )
            await db_token.insert()

        # Update user model with tracking info
        user.reset_token = reset_token
        user.reset_token_expires = expires_at
        await user.save()

        # Send email in background
        background_tasks.add_task(send_reset_email, payload.email, reset_token)
        logger.info(f"Password reset link sent to: {payload.email}")

        return generic_response

    except Exception as e:
        logger.error(f"Password reset request failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process password reset request"
        )


async def reset_password(payload: PasswordResetConfirm) -> EmailResetResponse:
    """"Reset password using token"""
    try:
        # Find reset token
        token_record = await PasswordResetToken.find_one(
            PasswordResetToken.token == payload.token
        )

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Check if the token was already used
        if token_record.used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has already been used"
            )
        
        # Find the user
        user = await User.find_one(User.email == token_record.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )
        
        # Hash the new password using the same method as signup/login
        hashed_password = pwd_context.hash(payload.new_password)

        # Update password
        user.hashed_password = hashed_password
        user.reset_token = None
        user.reset_token_expires = None
        await user.save()

        # Mark the token as used
        token_record.used = True
        await token_record.save()

        # Send confirmation email
        try:
            await send_password_changed_notification(user.email)
        except Exception as e:
            logger.warning(f"Failed to send change password notification: {e}")

        logger.info(f"Password reset successfully")
        return EmailResetResponse(message="Password reset successfully", success=True)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in reset_password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to reset password"
        )


async def verify_reset_token(token: str) -> dict:
    """"Verify if a reset token is valid"""
    try:
        token_record = await PasswordResetToken.find_one(
            PasswordResetToken.token == token
        )

        if not token_record or is_token_expired(token_record.expires_at) or token_record.used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Reset token has already been used"
            )
        
        if token_record.used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has already been used"
            )
        
        if is_token_expired(token_record.expires_at):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired"
            )
        
        return {"valid": True, "email": token_record.email}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in verify_reset_token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to verify token"
        )
