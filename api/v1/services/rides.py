"""
Rides Service
File: api/v1/services/rides.py

ONE CHANGE from original:
  - new_ride default status set to RideStatus.pending_approval
    (was: no explicit status — relied on model default of 'published')
  All other logic is unchanged.
"""

from typing import List, Optional
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
import json

from api.loggers.app_logger import app_logger
from api.v1.models.rides import Ride, RideMedia, RideStatus
from api.v1.models.users import User
from api.v1.schemas.rides import RideCreate, RideUpdate, RideStatusUpdate
from api.utils.cloudinary_service import cloudinary_service
from api.utils.settings import settings

ALLOWED_IMAGE_EXTS = ["jpg", "jpeg", "png", "webp"]
ALLOWED_VIDEO_EXTS = ["mp4", "mov", "webm"]
MAX_IMAGE_SIZE_MB = 5
MAX_VIDEO_SIZE_MB = 20

class RideService:

    def compute_vat(self, ride: Ride) -> Ride:
        """Helper to attach VAT dynamically since it's computed."""
        vat_percentage = settings.VAT_PERCENTAGE
        ride.vat_amount = ride.price * (vat_percentage / 100)
        ride.total_with_vat = ride.price + ride.vat_amount
        ride.total_passenger_count = ride.adult_passenger_count + ride.children_passenger_count + ride.infant_passenger_count
        return ride

    async def create_ride(
        self, schema: RideCreate, files: List[UploadFile], user: User, db: AsyncSession,
        photo_urls: List[str] = None, video_url: str = None
    ) -> Ride:
        # Determine if we have pre-uploaded URLs or raw files
        has_url_photos = photo_urls and len(photo_urls) > 0

        # Validate files only if no pre-uploaded URLs
        images = []
        videos = []
        if not has_url_photos:
            for file in files:
                if not file.filename:
                    continue
                ext = file.filename.split(".")[-1].lower()
                
                # Check size
                file.file.seek(0, 2)
                file_size = file.file.tell()
                file.file.seek(0)
                size_mb = file_size / (1024 * 1024)

                if ext in ALLOWED_IMAGE_EXTS:
                    if size_mb > MAX_IMAGE_SIZE_MB:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Image {file.filename} is too large. Max {MAX_IMAGE_SIZE_MB}MB."
                        )
                    images.append(file)
                elif ext in ALLOWED_VIDEO_EXTS:
                    if size_mb > MAX_VIDEO_SIZE_MB:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Video {file.filename} is too large. Max {MAX_VIDEO_SIZE_MB}MB."
                        )
                    videos.append(file)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid file format: {file.filename}"
                    )

            if not images:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least one image is required."
                )

        # ---------------------------------------------------------------------------
        # KEY CHANGE: default status is now pending_approval, not published
        # ---------------------------------------------------------------------------
        new_ride = Ride(
            user_id=user.id,
            ride_type=schema.ride_type,
            seat_count=schema.seat_count,
            door_count=schema.door_count,
            pickup_location=schema.pickup_location,
            pickup_latitude=schema.pickup_latitude,
            pickup_longitude=schema.pickup_longitude,
            adult_passenger_count=schema.adult_passenger_count,
            children_passenger_count=schema.children_passenger_count,
            infant_passenger_count=schema.infant_passenger_count,
            features=schema.features,
            price=schema.price,
            currency=schema.currency,
            status=RideStatus.pending_approval,   # ← CHANGED from published
        )
        db.add(new_ride)

        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A ride with these details already exists."
            )

        # Upload media to Cloudinary or use pre-uploaded URLs
        if has_url_photos:
            for i, url in enumerate(photo_urls):
                media = RideMedia(
                    ride_id=new_ride.id,
                    media_type="image",
                    url=url,
                    public_id="",
                    position=i,
                )
                db.add(media)

            if video_url:
                media = RideMedia(
                    ride_id=new_ride.id,
                    media_type="video",
                    url=video_url,
                    public_id="",
                    position=len(photo_urls),
                )
                db.add(media)
        else:
            # Upload images to Cloudinary
            for i, img in enumerate(images):
                result = await cloudinary_service.upload_media(
                    file=img,
                    folder=f"rides/{user.id}",
                    resource_type="image",
                )
                media = RideMedia(
                    ride_id=new_ride.id,
                    media_type="image",
                    url=result["url"],
                    public_id=result.get("public_id", ""),
                    resource_type=result.get("resource_type"),
                    format=result.get("format"),
                    position=i,
                )
                db.add(media)

            for video in videos:
                result = await cloudinary_service.upload_media(
                    file=video,
                    folder=f"rides/{user.id}",
                    resource_type="video",
                )
                media = RideMedia(
                    ride_id=new_ride.id,
                    media_type="video",
                    url=result["url"],
                    public_id=result.get("public_id", ""),
                    resource_type=result.get("resource_type"),
                    format=result.get("format"),
                    position=len(images),
                )
                db.add(media)

        await db.commit()
        await db.refresh(new_ride)
        app_logger.info(
            f"Ride created: id={new_ride.id} user_id={user.id} status=pending_approval"
        )
        return new_ride

    async def get_ride(self, ride_id: str, db: AsyncSession) -> Ride:
        result = await db.execute(
            select(Ride).options(selectinload(Ride.media)).filter(Ride.id == ride_id)
        )
        ride = result.scalars().first()
        if not ride:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found.")
        return ride

    async def get_user_rides(self, user: User, db: AsyncSession) -> List[Ride]:
        result = await db.execute(
            select(Ride)
            .options(selectinload(Ride.media))
            .filter(Ride.user_id == user.id)
            .order_by(Ride.created_at.desc())
        )
        return result.scalars().unique().all()

    async def get_published_rides(self, db: AsyncSession) -> List[Ride]:
        """Return only published rides for public listing pages."""
        result = await db.execute(
            select(Ride)
            .options(selectinload(Ride.media))
            .filter(Ride.status == RideStatus.published)
            .order_by(Ride.created_at.desc())
        )
        return result.scalars().unique().all()

    async def update_ride(self, ride_id: str, schema: RideUpdate, user: User, db: AsyncSession) -> Ride:
        ride = await self.get_ride(ride_id, db)
        if ride.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this ride.")

        update_data = schema.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(ride, field, value)

        await db.commit()
        await db.refresh(ride)
        return ride

    async def update_ride_status(self, ride_id: str, schema: RideStatusUpdate, user: User, db: AsyncSession) -> Ride:
        ride = await self.get_ride(ride_id, db)
        if ride.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this ride.")
        
        ride.status = schema.status
        await db.commit()
        await db.refresh(ride)
        return ride

    async def delete_ride(self, ride_id: str, user: User, db: AsyncSession) -> None:
        ride = await self.get_ride(ride_id, db)
        if ride.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this ride.")
        await db.delete(ride)
        await db.commit()
        app_logger.info(f"Ride deleted: id={ride_id} user_id={user.id}")


ride_service = RideService()