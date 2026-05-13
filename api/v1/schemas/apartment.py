"""Apartment Schemas"""

from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime


class ApartmentBase(BaseModel):
    name: Optional[str] = None
    type: str
    location: Optional[str] = None
    description: Optional[str] = None
    beds: int = 1
    baths: int = 1
    adults: int = 0
    children: int = 0
    infants: int = 0
    images: Optional[List[str]] = None
    video: Optional[str] = None
    features: Optional[Dict[str, bool]] = None
    price: float
    account_number: Optional[str] = None
    bank: Optional[str] = None
    account_name: Optional[str] = None


class ApartmentCreate(ApartmentBase):
    pass


class ApartmentUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    beds: Optional[int] = None
    baths: Optional[int] = None
    adults: Optional[int] = None
    children: Optional[int] = None
    infants: Optional[int] = None
    images: Optional[List[str]] = None
    video: Optional[str] = None
    features: Optional[Dict[str, bool]] = None
    price: Optional[float] = None
    account_number: Optional[str] = None
    bank: Optional[str] = None
    account_name: Optional[str] = None
    status: Optional[str] = None


class ApartmentResponse(ApartmentBase):
    id: str
    user_id: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedApartmentResponse(BaseModel):
    items: List[ApartmentResponse]
    total: int
    page: int
    size: int
    pages: int
