"""
Authentication Router
File: api/v1/routes/auth_route.py
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.database import get_db
from api.utils.jwt_handler import get_current_user
from api.utils.success_response import success_response
from api.v1.models.users import User
from api.v1.schemas.auth import (
    ForgotPasswordRequest,
    LogoutRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    SignInRequest,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from api.v1.services.auth import auth_service


auth = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------


@auth.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    response_description="User created successfully with an access & refresh token pair.",
)
async def register(
    schema: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new user account.
    """
    data = await auth_service.register(schema=schema, db=db)
    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Registration successful.",
        data=data,
    )


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


@auth.post(
    "/login",
    status_code=status.HTTP_200_OK,
    summary="Login with email/username and password",
)
async def login(
    schema: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate a user with email or username + password.
    """
    data = await auth_service.login(schema=schema, db=db)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Login successful.",
        data=data,
    )


# ---------------------------------------------------------------------------
# Refresh token
# ---------------------------------------------------------------------------


@auth.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
)
async def refresh_token(
    schema: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Exchange a valid refresh token for a new access token.
    """
    data = await auth_service.refresh(raw_refresh_token=schema.refresh_token, db=db)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Token refreshed successfully.",
        data=data,
    )


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


@auth.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout – invalidate session",
)
async def logout(
    schema: LogoutRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Invalidate the user's refresh token.
    """
    await auth_service.logout(raw_refresh_token=schema.refresh_token, db=db)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Logged out successfully.",
    )


# ---------------------------------------------------------------------------
# Current user profile
# ---------------------------------------------------------------------------


@auth.get(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
    response_model=None,
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """
    Returns the profile of the currently authenticated user.
    """
    user_data = UserResponse.model_validate(current_user).model_dump()
    return success_response(
        status_code=status.HTTP_200_OK,
        message="User profile retrieved successfully.",
        data=user_data,
    )


# ---------------------------------------------------------------------------
# Forgot password
# ---------------------------------------------------------------------------


@auth.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Request a password reset email",
)
async def forgot_password(
    schema: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Triggers the password-reset flow.
    """
    raw_token = await auth_service.forgot_password(schema=schema, db=db)
    
    response_data = {}
    if raw_token:
        response_data["reset_token"] = raw_token  # DEVELOPMENT ONLY

    return success_response(
        status_code=status.HTTP_200_OK,
        message=(
            "If an account with that email exists, a password reset link has been sent."
        ),
        data=response_data if response_data else None,
    )


# ---------------------------------------------------------------------------
# Reset password
# ---------------------------------------------------------------------------


@auth.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset user password using a reset token",
)
async def reset_password(
    schema: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Validates the reset token and updates the user's password.
    """
    await auth_service.reset_password(schema=schema, db=db)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Password reset successfully. Please log in with your new password.",
    )


# ---------------------------------------------------------------------------
# Legacy stub: OTP sign-in (kept for backward compatibility)
# ---------------------------------------------------------------------------


@auth.post(
    "/signin",
    status_code=status.HTTP_200_OK,
    summary="Sign In: Request OTP (stub)",
)
async def signin_request_otp(
    request: SignInRequest,
    db: AsyncSession = Depends(get_db),
):
    """Legacy OTP-based sign-in stub endpoint."""
    return success_response(
        status_code=status.HTTP_200_OK,
        message="OTP sent to phone number.",
        data={},
    )
