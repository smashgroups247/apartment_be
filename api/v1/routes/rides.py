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
    features: str = Form("[]"), # JSON array string of features
    files: Optional[List[UploadFile]] = File(None),
    photos: Optional[List[UploadFile]] = File(None),
    images: Optional[List[UploadFile]] = File(None),
    video: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new ride with media files (images/videos).
    """
    # Handle empty strings for floats
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
            
    # Ensure files is a list and combine from possible frontend field names
    files_list = []
    if files: files_list.extend(files)
    if photos: files_list.extend(photos)
    if images: files_list.extend(images)
    if video: files_list.append(video)

    try:
        raw_features = json.loads(features)
        features_list = []
        if isinstance(raw_features, list):
            for item in raw_features:
                if isinstance(item, str):
                    features_list.append(item)
                elif isinstance(item, dict):
                    name = item.get("name") or item.get("label") or item.get("value")
                    if name:
                        features_list.append(str(name))
                    else:
                        features_list.append(json.dumps(item))
                else:
                    features_list.append(str(item))
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
            features=features_list
        )
    except ValidationError as e:
        # Pydantic e.errors() might contain non-serializable objects like ValueError.
        # So we just parse the error messages cleanly.
        error_msgs = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msgs
        )
    
    new_ride = await ride_service.create_ride(
        schema=schema, files=files_list, user=current_user, db=db
    )
    
    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Ride created successfully.",
        data=RideResponse.model_validate(new_ride).model_dump()
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
    rides_list = await ride_service.get_my_rides(user=current_user, db=db)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Rides retrieved successfully.",
        data=[RideResponse.model_validate(r).model_dump() for r in rides_list]
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
        data=RideResponse.model_validate(ride).model_dump()
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
        data=RideResponse.model_validate(ride).model_dump()
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
        message="Ride deleted successfully."
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
        data=RideResponse.model_validate(ride).model_dump()
    )
