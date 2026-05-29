"""
Rides Router
File: api/v1/routes/rides.py
"""

from typing import List, Optional
import json
from fastapi import APIRouter, Depends, File, UploadFile, status, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.database import get_db
from api.utils.jwt_handler import get_current_user
from api.utils.success_response import success_response
from api.v1.models.users import User
from api.v1.schemas.rides import RideCreate, RideResponse, RideUpdate, RideStatusUpdate
from api.v1.services.rides import ride_service

rides = APIRouter(prefix="/rides", tags=["Rides"])


def serialize_ride(ride):
    """Call compute_vat before serializing to avoid missing field errors."""
    ride_service.compute_vat(ride)
    return RideResponse.model_validate(ride).model_dump()


@rides.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new ride listing",
    response_model=None,
)
async def create_ride(
    ride_type: str = Form(...),
    seat_count: int = Form(...),
    door_count: int = Form(...),
    pickup_location: str = Form(...),
    adult_passenger_count: int = Form(...),
    children_passenger_count: int = Form(...),
    infant_passenger_count: int = Form(...),
    price: float = Form(...),
    pickup_latitude: Optional[str] = Form(None),
    pickup_longitude: Optional[str] = Form(None),
    currency: str = Form("NGN"),
    features: str = Form("[]"),
    files: Optional[List[UploadFile]] = File(None),
    photos: Optional[List[UploadFile]] = File(None),
    images: Optional[List[UploadFile]] = File(None),
    video: Optional[UploadFile] = File(None),
    photo_urls: Optional[str] = Form(None),
    video_url: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    parsed_lat = None
    if pickup_latitude and pickup_latitude.strip():
        try:
            parsed_lat = float(pickup_latitude)
        except ValueError:
            pass

    parsed_lon = None
    if pickup_longitude and pickup_longitude.strip():
        try:
            parsed_lon = float(pickup_longitude)
        except ValueError:
            pass

    files_list = []
    if files:
        files_list.extend(files)
    if photos:
        files_list.extend(photos)
    if images:
        files_list.extend(images)
    if video:
        files_list.append(video)

    try:
        raw_features = json.loads(features)
        features_list = []
        if isinstance(raw_features, list):
            for item in raw_features:
                if isinstance(item, str):
                    features_list.append(item)
                elif isinstance(item, dict):
                    name = item.get("name") or item.get(
                        "label") or item.get("value")
                    features_list.append(
                        str(name) if name else json.dumps(item))
                else:
                    features_list.append(str(item))
        elif isinstance(raw_features, dict):
            # Handle {"air_condition": true, "music": true} format from Postman
            features_list = [k for k, v in raw_features.items() if v]
    except json.JSONDecodeError:
        features_list = []

    from pydantic import ValidationError
    try:
        schema = RideCreate(
            ride_type=ride_type,
            seat_count=seat_count,
            door_count=door_count,
            pickup_location=pickup_location,
            pickup_latitude=parsed_lat,
            pickup_longitude=parsed_lon,
            adult_passenger_count=adult_passenger_count,
            children_passenger_count=children_passenger_count,
            infant_passenger_count=infant_passenger_count,
            price=price,
            currency=currency,
            features=features_list,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[f"{err['loc']}: {err['msg']}" for err in e.errors()],
        )

    parsed_photo_urls = []
    parsed_video_url = None
    if photo_urls:
        try:
            parsed_photo_urls = json.loads(photo_urls)
            if not isinstance(parsed_photo_urls, list):
                parsed_photo_urls = []
        except json.JSONDecodeError:
            parsed_photo_urls = []
    if video_url and video_url.strip():
        parsed_video_url = video_url.strip()

    new_ride = await ride_service.create_ride(
        schema=schema, files=files_list, user=current_user, db=db,
        photo_urls=parsed_photo_urls, video_url=parsed_video_url,
    )

    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Ride created successfully.",
        data=serialize_ride(new_ride),
    )


@rides.get(
    "/public",
    status_code=status.HTTP_200_OK,
    summary="Get all published rides (public, no auth)",
    response_model=None,
)
async def get_public_rides(
    db: AsyncSession = Depends(get_db),
):
    rides_list = await ride_service.get_published_rides(db=db)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Public rides retrieved successfully.",
        data=[serialize_ride(r) for r in rides_list],
    )


@rides.get(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Get authenticated user's rides",
    response_model=None,
)
async def get_my_rides(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rides_list = await ride_service.get_user_rides(user=current_user, db=db)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Rides retrieved successfully.",
        data=[serialize_ride(r) for r in rides_list],
    )


@rides.get(
    "/{ride_id}",
    status_code=status.HTTP_200_OK,
    summary="Get a specific ride",
    response_model=None,
)
async def get_ride(
    ride_id: str,
    db: AsyncSession = Depends(get_db),
):
    ride = await ride_service.get_ride(ride_id, db)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Ride retrieved successfully.",
        data=serialize_ride(ride),
    )


@rides.put(
    "/{ride_id}",
    status_code=status.HTTP_200_OK,
    summary="Update a ride listing",
    response_model=None,
)
async def update_ride(
    ride_id: str,
    schema: RideUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ride = await ride_service.update_ride(ride_id, schema, current_user, db)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Ride updated successfully.",
        data=serialize_ride(ride),
    )


@rides.delete(
    "/{ride_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a ride",
    response_model=None,
)
async def delete_ride(
    ride_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await ride_service.delete_ride(ride_id, current_user, db)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Ride deleted successfully.",
    )


@rides.patch(
    "/{ride_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Update ride status",
    response_model=None,
)
async def update_ride_status(
    ride_id: str,
    schema: RideStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ride = await ride_service.update_ride_status(ride_id, schema, current_user, db)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Ride status updated successfully.",
        data=serialize_ride(ride),
    )