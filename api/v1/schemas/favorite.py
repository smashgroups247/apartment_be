"""Favorite Schemas"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AddFavoriteRequest(BaseModel):
    item_id:       str
    item_type:     str = Field(..., pattern="^(stay|car_rental)$")
    item_name:     str
    item_location: str
    item_image:    Optional[str]   = None
    item_rating:   Optional[float] = None
    item_price:    float


class FavoriteResponse(BaseModel):
    id:            str
    user_id:       str
    item_id:       str
    item_type:     str
    item_name:     str
    item_location: str
    item_image:    Optional[str]   = None
    item_rating:   Optional[float] = None
    item_price:    float
    created_at:    datetime
    updated_at:    datetime

    model_config = {"from_attributes": True}


class PaginatedFavoritesResponse(BaseModel):
    items: List[FavoriteResponse]
    total: int
    page:  int
    size:  int
    pages: int