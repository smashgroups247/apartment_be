"""
Users Router
File: api/v1/routes/users.py

Endpoints:
  GET  /users/me               – fetch current user profile
  PUT  /users/update           – update profile fields
  PUT  /users/change-password  – change password
  POST /users/upload-avatar    – upload profile picture
  POST /users/upload-id        – upload ID verification document
  GET  /users/me/vendor-status – get vendor eligibility fields
  POST /users/request-vendor   – submit vendor verification request
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
    VendorStatusResponse,
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
    updated_user = await user_service.upload_avatar(
        file=file, user=current_user, db=db
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Avatar uploaded successfully.",
        data=UserProfileResponse.model_validate(updated_user).model_dump(),
    )


# ---------------------------------------------------------------------------
# POST /users/upload-id
# ---------------------------------------------------------------------------

@users.post(
    "/upload-id",
    status_code=status.HTTP_200_OK,
    summary="Upload ID verification document",
    response_model=None,
)
async def upload_id(
    file: UploadFile = File(..., description="ID document: jpg, jpeg, png, webp, pdf. Max 5MB."),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    updated_user = await user_service.upload_id_verification(
        file=file, user=current_user, db=db
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="ID verification document uploaded successfully.",
        data=UserProfileResponse.model_validate(updated_user).model_dump(),
    )


# ---------------------------------------------------------------------------
# GET /users/me/vendor-status
# ---------------------------------------------------------------------------

@users.get(
    "/me/vendor-status",
    status_code=status.HTTP_200_OK,
    summary="Get vendor eligibility status for the current user",
    response_model=None,
)
async def get_vendor_status(
    current_user: User = Depends(get_current_user),
):
    """
    Returns all fields the frontend needs to determine vendor eligibility
    and show the correct state in the VendorCriteriaModal.
    """
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Vendor status retrieved successfully.",
        data=VendorStatusResponse.model_validate(current_user).model_dump(),
    )


# ---------------------------------------------------------------------------
# POST /users/request-vendor
# ---------------------------------------------------------------------------

@users.post(
    "/request-vendor",
    status_code=status.HTTP_200_OK,
    summary="Submit a vendor verification request",
    response_model=None,
)
async def request_vendor(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Sets the user's role to 'vendor' and id_verification_status to 'pending'.

    Raises:
        400 – if no ID document has been uploaded yet
        409 – if the user is already a verified vendor
    """
    updated_user = await user_service.request_vendor_verification(
        user=current_user, db=db
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Vendor verification request submitted. Awaiting admin approval.",
        data=VendorStatusResponse.model_validate(updated_user).model_dump(),
    )