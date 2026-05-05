"""Car Rental Schemas"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class CarRentalResponse(BaseModel):
    id: str
    user_id: str
    car_name: str
    location: str
    car_image: Optional[str] = None
    car_rating: Optional[float] = None
    pick_up_date: datetime
    pick_up_time: str
    return_date: datetime
    return_time: str
    total_price: float
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedCarRentalsResponse(BaseModel):
    items: List[CarRentalResponse]
    total: int
    page: int
    size: int
    pages: int