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
        """
        Verify current password then store new bcrypt hash.
        Invalidates all existing sessions.

        Raises:
            HTTPException 401 – if current password is wrong.
            HTTPException 400 – if new password is same as current.
        """
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
        user.hashed_refresh_token = None  # Invalidate all sessions
        await db.commit()
        app_logger.info(f"Password changed for user id={user.id}")

    # -----------------------------------------------------------------------
    # Upload Avatar — Cloudinary
    # -----------------------------------------------------------------------

    async def upload_avatar(
        self, file: UploadFile, user: User, db: AsyncSession
    ) -> User:
        """
        Validate the image and upload to Cloudinary.

        Raises:
            HTTPException 400 – invalid file format or exceeds size limit.
            HTTPException 502 - Cloudinary upload failure.
        """
        # Validate extension
        file_ext = file.filename.split(".")[-1].lower() if file.filename else ""
        if file_ext not in AVATAR_ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file format. Allowed: {', '.join(AVATAR_ALLOWED_EXTENSIONS)}",
            )

        # Validate file size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        size_mb = file_size / (1024 * 1024)
        if size_mb > AVATAR_MAX_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size is {AVATAR_MAX_SIZE_MB}MB.",
            )

        from api.utils.cloudinary_service import cloudinary_service

        upload_result = await cloudinary_service.upload_media(
            file=file,
            folder=f"avatars/{user.id}",
            resource_type="image",
        )

        # Persist to DB
        user.avatar_url = upload_result["url"]
        await db.commit()
        await db.refresh(user)

        app_logger.info(f"Avatar uploaded (cloudinary) for user id={user.id}")
        return user


# Singleton
user_service = UserService()