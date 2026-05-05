"""Booking Service"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from api.v1.models.booking import Booking


class BookingService:

    async def get_user_bookings(self, user_id: str, db: AsyncSession, page: int = 1, size: int = 10):
        offset = (page - 1) * size

        count_result = await db.execute(
            select(func.count()).select_from(Booking).where(Booking.user_id == user_id)
        )
        total = count_result.scalar()

        result = await db.execute(
            select(Booking)
            .where(Booking.user_id == user_id)
            .order_by(Booking.created_at.desc())
            .offset(offset)
            .limit(size)
        )
        bookings = result.scalars().all()

        return {
            "items": bookings,
            "total": total,
            "page": page,
            "size": size,
            "pages": -(-total // size) if total > 0 else 1,
        }

    async def get_booking_by_id(self, booking_id: str, user_id: str, db: AsyncSession):
        result = await db.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        booking = result.scalars().first()

        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

        if booking.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        return booking

    async def cancel_booking(self, booking_id: str, user_id: str, db: AsyncSession):
        booking = await self.get_booking_by_id(booking_id, user_id, db)

        if booking.status not in ("pending", "confirmed"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel a booking with status '{booking.status}'"
            )

        booking.status = "cancelled"
        await db.commit()
        await db.refresh(booking)
        return booking


booking_service = BookingService()