"""
Authentication Service
File: api/v1/services/auth.py

Business logic for registration, login, token refresh,
logout, and password reset (Async Version).
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.loggers.app_logger import app_logger
from api.v1.models.users import User
from api.v1.schemas.auth import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserLoginRequest,
    UserRegisterRequest,
)
from api.utils.jwt_handler import (
    create_access_token,
    create_refresh_token,
    create_reset_token,
    hash_password,
    verify_password,
    verify_refresh_token,
    _hash_token,
    _verify_hashed_token,
    _sha256_hex,
)
from api.utils.settings import settings


class AuthService:
    """Authentication service – handles all auth business logic (async)."""

    # -----------------------------------------------------------------------
    # Registration
    # -----------------------------------------------------------------------

    async def register(self, schema: UserRegisterRequest, db: AsyncSession) -> dict:
        """
        Register a new user.

        Raises:
            HTTPException 409 – if email or username already exists.
        """
        # Duplicate email check
        result = await db.execute(select(User).filter(User.email == schema.email.lower()))
        existing_email = result.scalars().first()
        
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            )

        # Duplicate username check
        if schema.username:
            result = await db.execute(select(User).filter(User.username == schema.username.lower()))
            existing_username = result.scalars().first()
            if existing_username:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This username is already taken.",
                )

        # Create user
        user = User(
            first_name=schema.first_name.strip(),
            last_name=schema.last_name.strip(),
            username=schema.username.lower() if schema.username else None,
            email=schema.email.lower(),
            hashed_password=hash_password(schema.password),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        app_logger.info(f"New user registered: {user.email} (id={user.id})")

        # Issue tokens
        return await self._issue_token_pair(user=user, db=db)

    # -----------------------------------------------------------------------
    # Login
    # -----------------------------------------------------------------------

    async def login(self, schema: UserLoginRequest, db: AsyncSession) -> dict:
        """
        Authenticate user by email OR username + password.

        Raises:
            HTTPException 401 – on invalid credentials.
            HTTPException 403 – if account is inactive.
        """
        login_value = schema.login.strip().lower()

        # Try email first, then username
        result = await db.execute(
            select(User).filter((User.email == login_value) | (User.username == login_value))
        )
        user: Optional[User] = result.scalars().first()

        if user is None or not verify_password(schema.password, user.hashed_password):
            # Return identical error regardless of which check failed (timing-safe-ish)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email/username or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated. Please contact support.",
            )

        app_logger.info(f"User logged in: {user.email} (id={user.id})")
        return await self._issue_token_pair(user=user, db=db)

    # -----------------------------------------------------------------------
    # Refresh Token
    # -----------------------------------------------------------------------

    async def refresh(self, raw_refresh_token: str, db: AsyncSession) -> dict:
        """
        Issue a new access token (and rotate the refresh token).

        Raises:
            HTTPException 401 – on any validation failure.
        """
        # 1. Validate the JWT signature & expiry
        payload = verify_refresh_token(raw_refresh_token)
        user_id: Optional[str] = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload.",
            )

        # 2. Fetch the user
        result = await db.execute(select(User).filter(User.id == user_id))
        user: Optional[User] = result.scalars().first()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found.",
            )

        # 3. Verify the token matches the stored hash
        if not user.hashed_refresh_token or not _verify_hashed_token(
            raw_refresh_token, user.hashed_refresh_token
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked or does not match.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated.",
            )

        # 4. Rotate – issue new pair
        app_logger.info(f"Refresh token rotated for user id={user.id}")
        return await self._issue_token_pair(user=user, db=db)

    # -----------------------------------------------------------------------
    # Logout
    # -----------------------------------------------------------------------

    async def logout(self, raw_refresh_token: str, db: AsyncSession) -> None:
        """
        Invalidate the user's session by clearing the stored refresh token hash.

        Raises:
            HTTPException 401 – if the token cannot be decoded or user is missing.
        """
        payload = verify_refresh_token(raw_refresh_token)
        user_id: Optional[str] = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token.",
            )

        result = await db.execute(select(User).filter(User.id == user_id))
        user: Optional[User] = result.scalars().first()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found.",
            )

        user.hashed_refresh_token = None
        await db.commit()

        app_logger.info(f"User logged out: id={user.id}")

    # -----------------------------------------------------------------------
    # Forgot password
    # -----------------------------------------------------------------------

    async def forgot_password(self, schema: ForgotPasswordRequest, db: AsyncSession) -> str:
        """
        Generate a password-reset token and store its SHA-256 hash in the DB.
        """
        result = await db.execute(select(User).filter(User.email == schema.email.lower()))
        user: Optional[User] = result.scalars().first()
        
        if user is None:
            app_logger.info(
                f"Forgot-password requested for non-existent email: {schema.email}"
            )
            return ""

        raw_token, hashed, expires_at = create_reset_token()

        user.hashed_reset_token = hashed
        user.reset_token_expires_at = expires_at
        await db.commit()

        app_logger.info(f"Password reset token generated for user id={user.id}")
        return raw_token

    # -----------------------------------------------------------------------
    # Reset password
    # -----------------------------------------------------------------------

    async def reset_password(self, schema: ResetPasswordRequest, db: AsyncSession) -> None:
        """
        Validate the reset token and update the user's password.
        """
        hashed = _sha256_hex(schema.reset_token)
        result = await db.execute(select(User).filter(User.hashed_reset_token == hashed))
        user: Optional[User] = result.scalars().first()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token.",
            )

        # Check expiry
        now = datetime.now(tz=timezone.utc)
        if user.reset_token_expires_at is None or user.reset_token_expires_at < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset token has expired.",
            )

        # Update password, clear reset token fields
        user.hashed_password = hash_password(schema.new_password)
        user.hashed_reset_token = None
        user.reset_token_expires_at = None
        user.hashed_refresh_token = None
        await db.commit()

        app_logger.info(f"Password reset successful for user id={user.id}")

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    async def _issue_token_pair(self, user: User, db: AsyncSession) -> dict:
        """
        Create an access + refresh token pair for ``user``.

        The raw refresh token is hashed with bcrypt and stored in the DB.
        Only the raw tokens are returned to the caller.
        """
        payload = {"sub": user.id, "email": user.email, "role": user.role}

        access_token = create_access_token(data=payload)
        raw_refresh_token = create_refresh_token(data=payload)

        # Store hashed refresh token
        user.hashed_refresh_token = _hash_token(raw_refresh_token)
        await db.commit()

        return {
            "access_token": access_token,
            "refresh_token": raw_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

# Singleton
auth_service = AuthService()