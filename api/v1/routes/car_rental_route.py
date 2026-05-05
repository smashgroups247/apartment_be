"""Car Rental Router"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.database import get_db
from api.utils.jwt_handler import get_current_user
from api.utils.success_response import success_response
from api.v1.models.users import User
from api.v1.schemas.car_rental import CarRentalResponse
from api.v1.services.car_rental import car_rental_service


car_rental = APIRouter(prefix="/car-rentals", tags=["Car Rentals"])


@car_rental.get("", status_code=status.HTTP_200_OK)
async def get_car_rentals(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await car_rental_service.get_user_car_rentals(
        user_id=current_user.id, db=db, page=page, size=size
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Car rentals retrieved successfully.",
        data=data,
    )


@car_rental.get("/{rental_id}", status_code=status.HTTP_200_OK)
async def get_car_rental(
    rental_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await car_rental_service.get_car_rental_by_id(
        rental_id=rental_id, user_id=current_user.id, db=db
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Car rental retrieved successfully.",
        data=CarRentalResponse.model_validate(data).model_dump(),
    )


@car_rental.patch("/cancel/{rental_id}", status_code=status.HTTP_200_OK)
async def cancel_car_rental(
    rental_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await car_rental_service.cancel_car_rental(
        rental_id=rental_id, user_id=current_user.id, db=db
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Car rental cancelled successfully.",
        data=CarRentalResponse.model_validate(data).model_dump(),
    )