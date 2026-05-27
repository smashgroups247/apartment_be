"""
Property Schemas
File: api/v1/schemas/property.py
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

VALID_TYPES = {"studio", "duplex", "bungalow"}


class CreatePropertyRequest(BaseModel):
    name:        str   = Field(..., min_length=2, max_length=255)
    type:        str   = Field(..., description="studio | duplex | bungalow")
    location:    str   = Field(..., min_length=3, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)

    beds:   int   = Field(default=1, ge=1, le=20)
    baths:  int   = Field(default=1, ge=1, le=20)
    guests: Optional[Dict[str, Any]] = None

    price: float = Field(..., ge=0)

    photos:    Optional[List[str]] = Field(default_factory=list)
    video_url: Optional[str]       = Field(None, max_length=1000)
    amenities: Optional[List[str]] = Field(default_factory=list)

    payout_account: str = Field(..., min_length=10, max_length=20)
    payout_bank:    str = Field(..., min_length=2, max_length=100)
    payout_name:    str = Field(..., min_length=2, max_length=255)

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in VALID_TYPES:
            raise ValueError(f"type must be one of: {', '.join(sorted(VALID_TYPES))}")
        return v

    @field_validator("name", "location")
    @classmethod
    def strip_string(cls, v: str) -> str:
        return v.strip()

    @field_validator("photos")
    @classmethod
    def validate_photos(cls, v):
        if v is None:
            return []
        if len(v) > 5:
            raise ValueError("Maximum 5 photos allowed.")
        return v


class PropertyResponse(BaseModel):
    id:          str
    user_id:     str
    name:        str
    type:        str
    location:    str
    description: Optional[str]
    beds:        int
    baths:       int
    guests:      Optional[Dict[str, Any]]
    price:       float
    photos:      Optional[List[str]]
    video_url:   Optional[str]
    amenities:   Optional[List[str]]
    payout_account: Optional[str]
    payout_bank:    Optional[str]
    payout_name:    Optional[str]
    status:      str
    admin_notes: Optional[str]
    created_at:  datetime
    updated_at:  datetime

    model_config = {"from_attributes": True}
