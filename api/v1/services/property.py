"""
Property Service
File: api/v1/services/property.py
"""

from typing import List
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from api.loggers.app_logger import app_logger
from api.v1.models.property import Property
from api.v1.models.users import User
from api.v1.schemas.property import CreatePropertyRequest

PUBLIC_PROPERTY_STATUS = "active"
PENDING_PROPERTY_STATUS = "pending_approval"


class PropertyService:

    async def create_property(
        self, schema: CreatePropertyRequest, user: User, db: AsyncSession
    ) -> Property:
        if user.role != "vendor" or not user.vendor_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only verified vendors can create property listings.",
            )

        # Explicit duplicate check
        existing = await db.execute(
            select(Property).filter(
                Property.user_id  == user.id,
                Property.name     == schema.name,
                Property.location == schema.location,
            )
        )
        if existing.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have a listing with this name and location.",
            )

        prop = Property(
            user_id        = user.id,
            name           = schema.name,
            type           = schema.type,
            location       = schema.location,
            description    = schema.description,
            beds           = schema.beds,
            baths          = schema.baths,
            guests         = schema.guests or {},
            price          = schema.price,
            photos         = schema.photos or [],
            video_url      = schema.video_url,
            amenities      = schema.amenities or [],
            payout_account = schema.payout_account,
            payout_bank    = schema.payout_bank,
            payout_name    = schema.payout_name,
            status         = PENDING_PROPERTY_STATUS,
        )

        db.add(prop)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have a listing with this name and location.",
            )

        await db.refresh(prop)
        app_logger.info(f"Property created: id={prop.id} user_id={user.id}")
        return prop

    async def get_user_properties(self, user: User, db: AsyncSession) -> List[Property]:
        result = await db.execute(
            select(Property)
            .filter(Property.user_id == user.id)
            .order_by(desc(Property.created_at))
        )
        return result.scalars().all()

    async def get_property(self, property_id: str, user: User, db: AsyncSession) -> Property:
        result = await db.execute(
            select(Property).filter(Property.id == property_id)
        )
        prop = result.scalars().first()

        if not prop:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found.")
        if prop.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access this property.")

        return prop

    async def delete_property(self, property_id: str, user: User, db: AsyncSession) -> None:
        prop = await self.get_property(property_id, user, db)
        await db.delete(prop)
        await db.commit()
        app_logger.info(f"Property deleted: id={property_id} user_id={user.id}")

    async def get_all_active_properties(self, db: AsyncSession) -> List[Property]:
        """Fetch all properties with status 'active' (public, no auth required)."""
        result = await db.execute(
            select(Property)
            .filter(Property.status == PUBLIC_PROPERTY_STATUS)
            .order_by(desc(Property.created_at))
        )
        return result.scalars().all()


property_service = PropertyService()
