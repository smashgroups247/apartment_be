"""
User Service
File: api/v1/services/users.py
"""

import base64

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.loggers.app_logger import app_logger
from api.utils.jwt_handler import hash_password, verify_password
from api.v1.models.users import User
from api.v1.schemas.users import ChangePasswordRequest, UpdateProfileRequest


AVATAR_ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]
AVATAR_MAX_SIZE_MB = 5


class UserService:

    # -----------------------------------------------------------------------
    # Get Profile
    # -----------------------------------------------------------------------

    def get_profile(self, user: User) -> User:
        """Return user already loaded by JWT dependency — no extra DB call needed."""
        return user

    # -----------------------------------------------------------------------
    # Update Profile
    # -----------------------------------------------------------------------

    async def update_profile(
        self, schema: UpdateProfileRequest, user: User, db: AsyncSession
    ) -> User:
        """
        Partial update — only fields explicitly sent are written to DB.

        Raises:
            HTTPException 409 – if new username is already taken.
        """
        if schema.username and schema.username != user.username:
            result = await db.execute(
                select(User).filter(
                    User.username == schema.username,
                    User.id != user.id,
                )
            )
            if result.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This username is already taken.",
                )

        if schema.email and schema.email != user.email:
            result = await db.execute(
                select(User).filter(
                    User.email == schema.email,
                    User.id != user.id,
                )
            )
            if result.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This email address is already in use.",
                )

        update_data = schema.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        await db.commit()
        await db.refresh(user)
        app_logger.info(
            f"Profile updated for user id={user.id} | fields={list(update_data.keys())}"
        )
        return user

    # -----------------------------------------------------------------------
    # Change Password
    # -----------------------------------------------------------------------

    async def change_password(
        self, schema: ChangePasswordRequest, user: User, db: AsyncSession
    ) -> None:
        if not verify_password(schema.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect.",
            )

        if verify_password(schema.new_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must differ from the current password.",
            )

        user.hashed_password = hash_password(schema.new_password)
        user.hashed_refresh_token = None
        await db.commit()
        app_logger.info(f"Password changed for user id={user.id}")

    # -----------------------------------------------------------------------
    # Upload Avatar
    # -----------------------------------------------------------------------

    async def upload_avatar(
        self, file: UploadFile, user: User, db: AsyncSession
    ) -> User:
        """
        Validate the image then:
        - Upload to Cloudinary if credentials are configured, OR
        - Encode as Base64 data URL and store directly (fallback).
        """
        from api.utils.settings import settings

        file_ext = file.filename.split(".")[-1].lower() if file.filename else ""
        if file_ext not in AVATAR_ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file format. Allowed: {', '.join(AVATAR_ALLOWED_EXTENSIONS)}",
            )

        content = await file.read()
        size_mb = len(content) / (1024 * 1024)
        if size_mb > AVATAR_MAX_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size is {AVATAR_MAX_SIZE_MB}MB.",
            )

        if settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY:
            from api.utils.cloudinary_service import cloudinary_service
            import io
            upload_file = UploadFile(
                filename=file.filename,
                file=io.BytesIO(content),
                headers={"content-type": file.content_type or "image/jpeg"},
            )
            result = await cloudinary_service.upload_media(
                file=upload_file,
                folder=f"avatars/{user.id}",
                resource_type="image",
            )
            user.avatar_url = result["url"]
        else:
            mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
            mime = mime_map.get(file_ext, "image/jpeg")
            b64 = base64.b64encode(content).decode("utf-8")
            user.avatar_url = f"data:{mime};base64,{b64}"

        await db.commit()
        await db.refresh(user)
        app_logger.info(f"Avatar uploaded for user id={user.id}")
        return user

    # -----------------------------------------------------------------------
    # Upload ID Verification
    # -----------------------------------------------------------------------

    async def upload_id_verification(
        self, file: UploadFile, user: User, db: AsyncSession
    ) -> User:
        """
        Validate the ID document, encode as Base64, and save to id_verification_url.
        """
        allowed = AVATAR_ALLOWED_EXTENSIONS + ["pdf"]
        file_ext = file.filename.split(".")[-1].lower() if file.filename else ""
        if file_ext not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file format. Allowed: {', '.join(allowed)}",
            )

        content = await file.read()
        size_mb = len(content) / (1024 * 1024)
        if size_mb > AVATAR_MAX_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size is {AVATAR_MAX_SIZE_MB}MB.",
            )

        mime_map = {
            "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "png": "image/png", "webp": "image/webp", "pdf": "application/pdf",
        }
        mime = mime_map.get(file_ext, "image/jpeg")
        b64 = base64.b64encode(content).decode("utf-8")
        user.id_verification_url = f"data:{mime};base64,{b64}"

        await db.commit()
        await db.refresh(user)
        app_logger.info(f"ID document uploaded for user id={user.id}")
        return user

    # -----------------------------------------------------------------------
    # Request Vendor Verification  ← NEW
    # -----------------------------------------------------------------------

    async def request_vendor_verification(
        self, user: User, db: AsyncSession
    ) -> User:
        """
        Submit a vendor verification request.

        Business rules:
          - User must have uploaded an ID document first (400 if not)
          - User cannot re-submit if already a verified vendor (409)
          - Sets role = 'vendor' and id_verification_status = 'pending'
          - If status is already 'pending', return current state (idempotent)

        Raises:
            HTTPException 400 – no ID document uploaded
            HTTPException 409 – user is already a verified vendor
        """
        # Guard: ID must be uploaded first
        if not user.id_verification_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please upload a government ID before requesting vendor verification.",
            )

        # Guard: already verified
        if user.vendor_verified:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You are already a verified vendor.",
            )

        # Idempotent — if already pending, just return current state
        if user.id_verification_status == "pending":
            return user

        # Set role and status
        user.role = "vendor"
        user.id_verification_status = "pending"

        await db.commit()
        await db.refresh(user)

        app_logger.info(
            f"Vendor verification requested by user id={user.id} email={user.email}"
        )
        return user


# Singleton
user_service = UserService()