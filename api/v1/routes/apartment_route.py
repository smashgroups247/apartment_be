"""Apartment Router"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.database import get_db
from api.utils.jwt_handler import get_current_user
from api.utils.success_response import success_response
from api.v1.models.users import User
from api.v1.schemas.apartment import ApartmentCreate, ApartmentUpdate, ApartmentResponse, PaginatedApartmentResponse
from api.v1.services.apartment import apartment_service


apartment = APIRouter(prefix="/apartments", tags=["Apartments"])


@apartment.post("", status_code=status.HTTP_201_CREATED)
async def create_apartment(
    apartment_data: ApartmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await apartment_service.create_apartment(
        apartment_data=apartment_data, user_id=current_user.id, db=db
    )
    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Apartment created successfully.",
        data=ApartmentResponse.model_validate(data).model_dump(),
    )


@apartment.get("", status_code=status.HTTP_200_OK)
async def get_apartments(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    data = await apartment_service.get_all_apartments(db=db, page=page, size=size)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Apartments retrieved successfully.",
        data=data,
    )


@apartment.get("/me", status_code=status.HTTP_200_OK)
async def get_my_apartments(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await apartment_service.get_user_apartments(
        user_id=current_user.id, db=db, page=page, size=size
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="My apartments retrieved successfully.",
        data=data,
    )


@apartment.get("/{apartment_id}", status_code=status.HTTP_200_OK)
async def get_apartment(
    apartment_id: str,
    db: AsyncSession = Depends(get_db),
):
    data = await apartment_service.get_apartment_by_id(apartment_id=apartment_id, db=db)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Apartment retrieved successfully.",
        data=ApartmentResponse.model_validate(data).model_dump(),
    )


@apartment.patch("/{apartment_id}", status_code=status.HTTP_200_OK)
async def update_apartment(
    apartment_id: str,
    update_data: ApartmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await apartment_service.update_apartment(
        apartment_id=apartment_id, update_data=update_data, user_id=current_user.id, db=db
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Apartment updated successfully.",
        data=ApartmentResponse.model_validate(data).model_dump(),
    )


@apartment.delete("/{apartment_id}", status_code=status.HTTP_200_OK)
async def delete_apartment(
    apartment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await apartment_service.delete_apartment(
        apartment_id=apartment_id, user_id=current_user.id, db=db
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Apartment deleted successfully.",
    )
