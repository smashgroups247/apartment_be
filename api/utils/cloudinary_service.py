"""
Cloudinary Service
File: api/utils/cloudinary_service.py
"""

import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile, status
from api.utils.settings import settings
from api.loggers.app_logger import app_logger

# Configure Cloudinary
if settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY:
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )

class CloudinaryService:
    async def upload_media(
        self, file: UploadFile, folder: str, resource_type: str = "auto"
    ) -> dict:
        """
        Uploads a file to Cloudinary.
        
        :param file: UploadFile object
        :param folder: Cloudinary folder path
        :param resource_type: 'image', 'video', or 'auto'
        :return: Dict containing url and public_id
        """
        if not file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided."
            )

        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty."
            )

        try:
            full_folder = f"{settings.CLOUDINARY_FOLDER}/{folder}"
            
            # Using synchronous upload since cloudinary uploader doesn't have an async interface out of the box,
            # but we read the file bytes async above.
            result = cloudinary.uploader.upload(
                content,
                folder=full_folder,
                resource_type=resource_type,
            )
            
            return {
                "url": result.get("secure_url"),
                "public_id": result.get("public_id"),
                "resource_type": result.get("resource_type"),
                "format": result.get("format"),
            }
        except Exception as e:
            error_msg = str(e)
            app_logger.error(f"Cloudinary upload failed: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Cloudinary upload failed: {error_msg}",
            )

cloudinary_service = CloudinaryService()
