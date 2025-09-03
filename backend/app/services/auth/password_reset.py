import secrets
import traceback
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, BackgroundTasks
from app.models.user import User, PasswordResetToken
from app.schemas.auth import PasswordResetRequest, PasswordResetConfirm, EmailResetResponse
from app.utils.email import send_reset_email, send_password_changed_notification
from app.crud.user_crud import get_user_by_email
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)

def get_token_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=1)

def is_token_expired(expires_at: datetime) -> bool:
    current_time = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return current_time > expires_at


async def request_password_reset(payload: PasswordResetRequest, background_tasks: BackgroundTasks) -> EmailResetResponse:
    try:
        user = await get_user_by_email(payload.email)

        generic_response = EmailResetResponse(
            message="We've sent a password reset link to your email.",
            success=True
        )

        if not user:
            logger.info(f"Password reset requested for non-existing email: {payload.email}")
            return generic_response

        reset_token = generate_reset_token()
        expires_at = get_token_expiry()

        existing_token = await PasswordResetToken.find_one({
            "$and": [
                {"email": payload.email},
                {"used": False},
                {"expires_at": {"$gt": datetime.now(timezone.utc)}}
            ]
        })

        if existing_token:
            existing_token.token = reset_token
            existing_token.expires_at = expires_at
            existing_token.created_at = datetime.now(timezone.utc)
            await existing_token.save()
        else:
            db_token = PasswordResetToken(
                token=reset_token,
                email=payload.email,
                expires_at=expires_at,
                used=False
            )
            await db_token.insert()

        user.reset_token = reset_token
        user.reset_token_expires = expires_at
        await user.save()

        background_tasks.add_task(send_reset_email, payload.email, reset_token)
        logger.info(f"Password reset link sent to: {payload.email}")

        return generic_response

    except Exception as e:
        logger.error(f"Password reset request failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process password reset request")


async def reset_password(payload: PasswordResetConfirm) -> EmailResetResponse:
    try:
        token_record = await PasswordResetToken.find_one(PasswordResetToken.token == payload.token)
        if not token_record:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
        if token_record.used:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset token has already been used")

        user = await User.find_one(User.email == token_record.email)
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

        hashed_password = pwd_context.hash(payload.new_password)

        user.hashed_password = hashed_password
        user.reset_token = None
        user.reset_token_expires = None
        await user.save()

        token_record.used = True
        await token_record.save()

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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reset password")


async def verify_reset_token(token: str) -> dict:
    try:
        token_record = await PasswordResetToken.find_one(PasswordResetToken.token == token)

        if (not token_record) or is_token_expired(token_record.expires_at) or token_record.used:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset token has already been used or expired")

        return {"valid": True, "email": token_record.email}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in verify_reset_token: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to verify token")
