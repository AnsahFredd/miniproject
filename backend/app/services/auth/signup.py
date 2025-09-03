import secrets
import logging
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, BackgroundTasks
from passlib.context import CryptContext

from app.models.user import User
from app.schemas.auth import SignupRequest
from app.utils.email import send_confirmation_email_with_retry

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _generate_confirmation_token(hours_valid: int = 24):
    """Helper to generate a token and expiry timestamp."""
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(hours=hours_valid)
    return token, expires


async def signup_user(payload: SignupRequest, background_tasks: BackgroundTasks):
    client = User.get_motor_collection().database.client
    try:
        async with await client.start_session() as session:
            async with session.start_transaction():
                existing = await User.find_one(User.email == payload.email)
                if existing:
                    logger.warning(f"Signup attempt with existing email: {payload.email}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already registered",
                    )

                hashed_password = pwd_context.hash(payload.password)
                confirmation_token, confirmation_token_expires = _generate_confirmation_token()

                user = User(
                    full_name=payload.name,
                    email=payload.email,
                    hashed_password=hashed_password,
                    is_active=False,
                    is_verified=False,
                    confirmation_token=confirmation_token,
                    confirmation_token_expires=confirmation_token_expires,
                )
                await user.insert()
                logger.info(f"New user created (unverified): {user.email}")

                background_tasks.add_task(
                    send_confirmation_email_with_retry,
                    user.email,
                    confirmation_token,
                )

                return {
                    "message": "Registration successful. Please check your email to confirm your account.",
                    "email": user.email,
                    "requires_confirmation": True,
                }

    except HTTPException:
        raise  # let deliberate API errors bubble up
    except Exception as e:
        logger.exception(f"Signup failed for {payload.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


async def confirm_user_email(token: str):
    user = await User.find_one(User.confirmation_token == token)
    if not user:
        logger.error("Invalid confirmation attempt with token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid confirmation token",
        )

    if user.confirmation_token_expires and user.confirmation_token_expires < datetime.now(timezone.utc):
        logger.warning(f"Expired confirmation token used by {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation token has expired",
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already confirmed",
        )

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
        logger.warning(f"Resend requested for non-existent email: {email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already confirmed",
        )

    confirmation_token, confirmation_token_expires = _generate_confirmation_token()
    user.confirmation_token = confirmation_token
    user.confirmation_token_expires = confirmation_token_expires
    await user.save()

    background_tasks.add_task(
        send_confirmation_email_with_retry,
        user.email,
        confirmation_token,
    )

    logger.info(f"Confirmation email resent to: {user.email}")
    return {"message": "Confirmation email resent. Please check your inbox."}
