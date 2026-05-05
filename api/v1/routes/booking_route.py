"""Booking Router"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.database import get_db
from api.utils.jwt_handler import get_current_user
from api.utils.success_response import success_response
from api.v1.models.users import User
from api.v1.schemas.booking import BookingResponse, PaginatedBookingsResponse
from api.v1.services.booking import booking_service


booking = APIRouter(prefix="/bookings", tags=["Bookings"])


@booking.get("", status_code=status.HTTP_200_OK)
async def get_bookings(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await booking_service.get_user_bookings(
        user_id=current_user.id, db=db, page=page, size=size
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Bookings retrieved successfully.",
        data=data,
    )


@booking.get("/{booking_id}", status_code=status.HTTP_200_OK)
async def get_booking(
    booking_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await booking_service.get_booking_by_id(
        booking_id=booking_id, user_id=current_user.id, db=db
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Booking retrieved successfully.",
        data=BookingResponse.model_validate(data).model_dump(),
    )


@booking.patch("/cancel/{booking_id}", status_code=status.HTTP_200_OK)
async def cancel_booking(
    booking_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await booking_service.cancel_booking(
        booking_id=booking_id, user_id=current_user.id, db=db
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Booking cancelled successfully.",
        data=BookingResponse.model_validate(data).model_dump(),
    )