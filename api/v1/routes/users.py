"""
Users Router
File: api/v1/routes/users.py

Endpoints for user account management:
  GET  /users/me              – fetch current user profile
  PUT  /users/update          – update profile fields
  PUT  /users/change-password – change password
  POST /users/upload-avatar   – upload profile picture
"""

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.database import get_db
from api.utils.jwt_handler import get_current_user
from api.utils.success_response import success_response
from api.v1.models.users import User
from api.v1.schemas.users import (
    ChangePasswordRequest,
    UpdateProfileRequest,
    UserProfileResponse,
)
from api.v1.services.users import user_service


users = APIRouter(prefix="/users", tags=["Users"])


# ---------------------------------------------------------------------------
# GET /users/me
# ---------------------------------------------------------------------------

@users.get(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    response_model=None,
)
async def get_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Returns the full profile of the currently authenticated user,
    including phone_number and avatar_url.
    """
    profile = user_service.get_profile(current_user)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Profile retrieved successfully.",
        data=UserProfileResponse.model_validate(profile).model_dump(),
    )


# ---------------------------------------------------------------------------
# PUT /users/update
# ---------------------------------------------------------------------------

@users.put(
    "/update",
    status_code=status.HTTP_200_OK,
    summary="Update user profile fields",
    response_model=None,
)
async def update_profile(
    schema: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update one or more profile fields: first_name, last_name, username,
    phone_number. Only provided fields are updated (partial update).
    """
    updated_user = await user_service.update_profile(
        schema=schema, user=current_user, db=db
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Profile updated successfully.",
        data=UserProfileResponse.model_validate(updated_user).model_dump(),
    )


# ---------------------------------------------------------------------------
# PUT /users/change-password
# ---------------------------------------------------------------------------

@users.put(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change authenticated user password",
    response_model=None,
)
async def change_password(
    schema: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify current_password, then hash and store new_password.
    All existing sessions are invalidated on success.
    """
    await user_service.change_password(
        schema=schema, user=current_user, db=db
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Password changed successfully. Please log in again.",
    )


# ---------------------------------------------------------------------------
# POST /users/upload-avatar
# ---------------------------------------------------------------------------

@users.post(
    "/upload-avatar",
    status_code=status.HTTP_200_OK,
    summary="Upload or replace profile avatar",
    response_model=None,
)
async def upload_avatar(
    file: UploadFile = File(..., description="Image file: jpg, jpeg, png, webp. Max 5MB."),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a profile avatar image. Accepted formats: jpg, jpeg, png, webp.
    Maximum file size: 5MB. Returns the updated user profile with the new avatar_url.
    """
    updated_user = await user_service.upload_avatar(
        file=file, user=current_user, db=db
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Avatar uploaded successfully.",
        data=UserProfileResponse.model_validate(updated_user).model_dump(),
    )