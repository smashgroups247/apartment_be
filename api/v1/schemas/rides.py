"""
Rides Schemas
File: api/v1/schemas/rides.py
"""

from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, model_validator
from api.v1.models.rides import RideType, RideStatus

class RideMediaResponse(BaseModel):
    id: str
    media_type: str
    url: str
    public_id: Optional[str] = None
    resource_type: Optional[str] = None
    format: Optional[str] = None
    position: int
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}

class RideCreate(BaseModel):
    ride_type: RideType
    seat_count: int = Field(..., gt=0)
    door_count: int = Field(..., gt=0)
    
    pickup_location: str = Field(..., min_length=2, max_length=255)
    pickup_latitude: Optional[float] = None
    pickup_longitude: Optional[float] = None
    
    adult_passenger_count: int = Field(..., ge=0)
    children_passenger_count: int = Field(..., ge=0)
    infant_passenger_count: int = Field(..., ge=0)
    
    features: List[str] = Field(default_factory=list)
    
    price: float = Field(..., gt=0)
    currency: str = Field(default="NGN")
    
    @model_validator(mode='after')
    def check_passenger_capacity(self) -> 'RideCreate':
        total = self.adult_passenger_count + self.children_passenger_count + self.infant_passenger_count
        if total > self.seat_count:
            raise ValueError(f"Total passenger count ({total}) cannot exceed seat count ({self.seat_count})")
        return self

class RideUpdate(BaseModel):
    ride_type: Optional[RideType] = None
    seat_count: Optional[int] = Field(None, gt=0)
    door_count: Optional[int] = Field(None, gt=0)
    
    pickup_location: Optional[str] = Field(None, min_length=2, max_length=255)
    pickup_latitude: Optional[float] = None
    pickup_longitude: Optional[float] = None
    
    adult_passenger_count: Optional[int] = Field(None, ge=0)
    children_passenger_count: Optional[int] = Field(None, ge=0)
    infant_passenger_count: Optional[int] = Field(None, ge=0)
    
    features: Optional[List[str]] = None
    
    price: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = None
    
    @model_validator(mode='after')
    def check_passenger_capacity(self) -> 'RideUpdate':
        if self.adult_passenger_count is not None and self.children_passenger_count is not None and self.infant_passenger_count is not None and self.seat_count is not None:
            total = self.adult_passenger_count + self.children_passenger_count + self.infant_passenger_count
            if total > self.seat_count:
                raise ValueError(f"Total passenger count ({total}) cannot exceed seat count ({self.seat_count})")
        return self

class RideStatusUpdate(BaseModel):
    status: RideStatus

class RideResponse(BaseModel):
    id: str
    user_id: str
    ride_type: RideType
    seat_count: int
    door_count: int
    pickup_location: str
    pickup_latitude: Optional[float]
    pickup_longitude: Optional[float]
    adult_passenger_count: int
    children_passenger_count: int
    infant_passenger_count: int
    features: List[str]
    price: float
    currency: str
    status: RideStatus
    photos: List[RideMediaResponse]
    video: Optional[RideMediaResponse] = None
    created_at: datetime
    updated_at: datetime
    
    vat_amount: float
    total_with_vat: float
    total_passenger_count: int

    model_config = {"from_attributes": True}
