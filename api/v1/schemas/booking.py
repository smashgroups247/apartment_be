"""Booking Schemas"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class BookingResponse(BaseModel):
    id: str
    user_id: str
    apartment_name: str
    apartment_location: str
    apartment_image: Optional[str] = None
    apartment_rating: Optional[float] = None
    check_in: datetime
    check_out: datetime
    guests: int
    total_price: float
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedBookingsResponse(BaseModel):
    items: List[BookingResponse]
    total: int
    page: int
    size: int
    pages: int