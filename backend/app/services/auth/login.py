from fastapi import HTTPException, status, Response, Request, Cookie
from datetime import datetime, timezone
from jose import jwt, JWTError
from bson import ObjectId
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserRead
from app.core.config import settings
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
is_production = settings.ENV == "production"

from .tokens import _create_access_token, _create_refresh_token, _set_refresh_cookie


async def login_user(payload: LoginRequest, response: Response) -> dict:
    """Login user and return token response as dict for consistent response structure."""
    client = User.get_motor_collection().database.client
    try:
        async with await client.start_session() as session:
            async with session.start_transaction():
                user = await User.find_one(User.email == payload.email)
                if not user or not pwd_context.verify(payload.password, user.hashed_password):
                    logger.warning(f"Failed login attempt for email: {payload.email}")
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

                if not user.is_verified:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Please verify your email address before logging in. Check your inbox for the confirmation email.",
                    )

                if not user.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Your account has been deactivated. Please contact support.",
                    )

        access_token = _create_access_token(str(user.id))
        refresh_token = _create_refresh_token(str(user.id))
        _set_refresh_cookie(response, refresh_token)
        logger.info(f"User logged in successfully: {user.email}")

        # Convert user data to dict with proper ID handling
        user_data = user.model_dump(by_alias=True)
        user_data["_id"] = str(user_data["_id"])
        
        # Also set id field for frontend compatibility
        user_data["id"] = user_data["_id"]

        # Return as dict instead of TokenResponse for consistent structure
        return {
            "accessToken": access_token,
            "refreshToken": refresh_token,  # Still include for potential frontend use
            "user": UserRead.model_validate(user_data).model_dump(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed for {payload.email}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed")


async def refresh_access_token(
    request: Request, response: Response, refresh_token: str = Cookie(None, alias="refresh_token")
) -> dict:
    """Refresh access token and return as dict for consistent response structure."""
    logger.info(f"Refresh attempt. Cookies: {list(request.cookies.keys())}")

    if not refresh_token:
        logger.warning("Refresh attempt with missing token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")

    try:
        payload = jwt.decode(refresh_token, settings.JWT_REFRESH_TOKEN, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

        user = await User.find_one(User.id == ObjectId(user_id))
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        new_access_token = _create_access_token(user_id)
        new_refresh_token = _create_refresh_token(user_id)
        _set_refresh_cookie(response, new_refresh_token)
        logger.info(f"Token refreshed for user: {user.email}")

        # Convert user data to dict with proper ID handling
        user_data = user.model_dump(by_alias=True)
        user_data["_id"] = str(user_data["_id"])
        user_data["id"] = user_data["_id"]

        # Return as dict instead of TokenResponse for consistent structure
        return {
            "accessToken": new_access_token,
            "refreshToken": new_refresh_token,
            "user": UserRead.model_validate(user_data).model_dump(),
        }

    except JWTError as e:
        logger.warning(f"Invalid refresh token: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    except Exception as e:
        logger.error(f"Refresh token processing failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Token refresh failed")


async def logout_user(response: Response):
    try:
        response.delete_cookie(
            key="refresh_token",
            path="/",
            secure=is_production,
            domain=None,
            samesite="none" if is_production else "lax",
        )
        
        logger.info("User logged out successfully")
        return {"message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed")