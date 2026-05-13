"""
Rides Service
File: api/v1/services/rides.py
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
        self, schema: RideCreate, files: List[UploadFile], user: User, db: AsyncSession
    ) -> Ride:
        # Validate files
        images = []
        videos = []
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
                # Video duration is not available from raw file object here. Rely on Cloudinary or just size.
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
                detail="At least 1 photo is required."
            )
        if len(images) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum of 5 photos allowed."
            )
        if len(videos) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum of 1 video allowed."
            )

        # Check for duplicates manually before DB
        result = await db.execute(
            select(Ride).filter(
                Ride.user_id == user.id,
                Ride.ride_type == schema.ride_type,
                Ride.seat_count == schema.seat_count,
                Ride.door_count == schema.door_count,
                Ride.pickup_location == schema.pickup_location,
            )
        )
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already listed a similar ride at this location."
            )

        # Create ride record
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
            currency=schema.currency
        )
        db.add(new_ride)
        try:
            await db.flush() # To get new_ride.id
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already listed a similar ride at this location."
            )

        # Upload files and create RideMedia
        media_records = []
        pos = 0
        for img in images:
            upload_result = await cloudinary_service.upload_media(
                file=img,
                folder=f"rides/{user.id}/photos",
                resource_type="image"
            )
            media_records.append(RideMedia(
                ride_id=new_ride.id,
                media_type="image",
                url=upload_result["url"],
                public_id=upload_result["public_id"],
                resource_type=upload_result.get("resource_type"),
                format=upload_result.get("format"),
                position=pos
            ))
            pos += 1
            
        for vid in videos:
            upload_result = await cloudinary_service.upload_media(
                file=vid,
                folder=f"rides/{user.id}/videos",
                resource_type="video"
            )
            # Check duration from cloudinary if available, else skip. (TODO: Add duration check)
            media_records.append(RideMedia(
                ride_id=new_ride.id,
                media_type="video",
                url=upload_result["url"],
                public_id=upload_result["public_id"],
                resource_type=upload_result.get("resource_type"),
                format=upload_result.get("format"),
                position=pos
            ))
            pos += 1

        db.add_all(media_records)
        await db.commit()
        await db.refresh(new_ride)
        
        return self.compute_vat(new_ride)

    async def get_my_rides(self, user: User, db: AsyncSession) -> List[Ride]:
        result = await db.execute(
            select(Ride)
            .options(selectinload(Ride.media))
            .filter(Ride.user_id == user.id)
            .order_by(Ride.created_at.desc())
        )
        rides = result.scalars().all()
        return [self.compute_vat(r) for r in rides]

    async def get_ride(self, ride_id: str, db: AsyncSession) -> Ride:
        result = await db.execute(
            select(Ride)
            .options(selectinload(Ride.media))
            .filter(Ride.id == ride_id)
        )
        ride = result.scalars().first()
        if not ride:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found.")
        return self.compute_vat(ride)

    async def update_ride(self, ride_id: str, schema: RideUpdate, user: User, db: AsyncSession) -> Ride:
        ride = await self.get_ride(ride_id, db)
        if ride.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this ride.")
        
        update_data = schema.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(ride, field, value)
            
        # Re-validate passenger capacity dynamically
        total = ride.adult_passenger_count + ride.children_passenger_count + ride.infant_passenger_count
        if total > ride.seat_count:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Total passengers ({total}) exceed seat count ({ride.seat_count})")

        try:
            await db.commit()
            await db.refresh(ride)
        except IntegrityError:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicate ride details.")

        return self.compute_vat(ride)

    async def delete_ride(self, ride_id: str, user: User, db: AsyncSession) -> None:
        ride = await self.get_ride(ride_id, db)
        if ride.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this ride.")
        
        await db.delete(ride)
        await db.commit()

    async def update_ride_status(self, ride_id: str, schema: RideStatusUpdate, user: User, db: AsyncSession) -> Ride:
        ride = await self.get_ride(ride_id, db)
        if ride.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this ride.")
        
        ride.status = schema.status
        await db.commit()
        await db.refresh(ride)
        return self.compute_vat(ride)

ride_service = RideService()
