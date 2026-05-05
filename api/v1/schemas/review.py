from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CreateReviewRequest(BaseModel):
    booking_id: str
    booking_type: str = Field(default="stay", pattern="^(stay|car_rental)$")
    review_text: str = Field(..., min_length=1)
    rating: int = Field(..., ge=1, le=10)
    item_image: Optional[str] = None
    item_name: Optional[str] = None


class ReviewResponse(BaseModel):
    id: str
    user_id: str
    booking_id: str
    booking_type: str
    review_text: str
    rating: int
    item_image: Optional[str] = None
    item_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}