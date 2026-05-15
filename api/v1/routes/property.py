"""
Property Router
File: api/v1/routes/property.py
"""

from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.database import get_db
from api.utils.cloudinary_service import cloudinary_service
from api.utils.jwt_handler import get_current_user
from api.utils.success_response import success_response
from api.v1.models.users import User
from api.v1.schemas.property import CreatePropertyRequest, PropertyResponse
from api.v1.services.property import property_service

properties = APIRouter(prefix="/properties", tags=["Properties"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}
MAX_IMAGE_SIZE_MB   = 5
MAX_VIDEO_SIZE_MB   = 50


# ---------------------------------------------------------------------------
# POST /properties/upload-media  — MUST be before /{property_id} routes
# ---------------------------------------------------------------------------

@properties.post("/upload-media", status_code=status.HTTP_200_OK, response_model=None)
async def upload_media(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload 1–5 images or a single video to Cloudinary. Returns list of URLs."""
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 files per request.")

    urls: List[str] = []

    for file in files:
        content_type = file.content_type or ""

        if content_type not in (ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported type: {content_type}. Allowed: jpg, png, webp, mp4, webm, mov.",
            )

        # Check size without consuming the stream
        file.file.seek(0, 2)
        size_mb = file.file.tell() / (1024 * 1024)
        file.file.seek(0)

        max_mb = MAX_VIDEO_SIZE_MB if content_type in ALLOWED_VIDEO_TYPES else MAX_IMAGE_SIZE_MB
        if size_mb > max_mb:
            raise HTTPException(status_code=400, detail=f"'{file.filename}' exceeds {max_mb}MB limit.")

        resource_type = "video" if content_type in ALLOWED_VIDEO_TYPES else "image"

        result = await cloudinary_service.upload_media(
            file=file,
            folder=f"listings/{current_user.id}",
            resource_type=resource_type,
        )
        urls.append(result["url"])

    return success_response(
        status_code=200,
        message="Media uploaded successfully.",
        data={"urls": urls, "count": len(urls)},
    )


# ---------------------------------------------------------------------------
# POST /properties
# ---------------------------------------------------------------------------

@properties.post("", status_code=status.HTTP_201_CREATED, response_model=None)
async def create_property(
    schema: CreatePropertyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    prop = await property_service.create_property(schema=schema, user=current_user, db=db)
    return success_response(
        status_code=201,
        message="Listing created successfully.",
        data=PropertyResponse.model_validate(prop).model_dump(),
    )


# ---------------------------------------------------------------------------
# GET /properties
# ---------------------------------------------------------------------------

@properties.get("", status_code=status.HTTP_200_OK, response_model=None)
async def get_properties(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    props = await property_service.get_user_properties(user=current_user, db=db)
    data  = [PropertyResponse.model_validate(p).model_dump() for p in props]
    return success_response(
        status_code=200,
        message="Listings retrieved successfully.",
        data={"total": len(data), "properties": data},
    )


# ---------------------------------------------------------------------------
# GET /properties/{property_id}
# ---------------------------------------------------------------------------

@properties.get("/{property_id}", status_code=status.HTTP_200_OK, response_model=None)
async def get_property(
    property_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    prop = await property_service.get_property(property_id=property_id, user=current_user, db=db)
    return success_response(
        status_code=200,
        message="Listing retrieved successfully.",
        data=PropertyResponse.model_validate(prop).model_dump(),
    )


# ---------------------------------------------------------------------------
# DELETE /properties/{property_id}
# ---------------------------------------------------------------------------

@properties.delete("/{property_id}", status_code=status.HTTP_200_OK, response_model=None)
async def delete_property(
    property_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await property_service.delete_property(property_id=property_id, user=current_user, db=db)
    return success_response(status_code=200, message="Listing deleted successfully.")