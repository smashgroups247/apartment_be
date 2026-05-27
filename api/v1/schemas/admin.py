"""
Admin Pydantic Schemas
File: api/v1/schemas/admin.py

Schemas for superadmin dashboard endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# User Management – Requests
# ---------------------------------------------------------------------------


class ChangeUserRoleRequest(BaseModel):
    """Change a user's role."""

    role: str = Field(..., description="New role: 'user', 'vendor', or 'superadmin'")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed = {"user", "vendor", "superadmin"}
        v = v.strip().lower()
        if v not in allowed:
            raise ValueError(f"Role must be one of: {', '.join(sorted(allowed))}")
        return v


class VerifyVendorRequest(BaseModel):
    """Approve or reject vendor verification."""

    action: str = Field(..., description="'approve' or 'reject'")
    reason: Optional[str] = Field(None, max_length=1000, description="Reason for rejection")

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        allowed = {"approve", "reject"}
        v = v.strip().lower()
        if v not in allowed:
            raise ValueError(f"Action must be one of: {', '.join(sorted(allowed))}")
        return v


class ChangeUserStatusRequest(BaseModel):
    """Activate or deactivate a user account."""

    is_active: bool


# ---------------------------------------------------------------------------
# Listing Management – Requests
# ---------------------------------------------------------------------------


class ChangePropertyStatusRequest(BaseModel):
    """Change property listing status."""

    status: str = Field(..., description="New status for the listing")
    admin_notes: Optional[str] = Field(None, max_length=2000, description="Admin notes / rejection reason")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"active", "pending_approval", "rejected", "suspended"}
        v = v.strip().lower()
        if v not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(sorted(allowed))}")
        return v


class ChangeRideStatusRequest(BaseModel):
    """Change ride listing status."""

    status: str = Field(..., description="New status for the listing")
    admin_notes: Optional[str] = Field(None, max_length=2000, description="Admin notes / rejection reason")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"active", "pending_approval", "rejected", "suspended", "published", "inactive", "draft"}
        v = v.strip().lower()
        if v not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(sorted(allowed))}")
        return v


# ---------------------------------------------------------------------------
# Support Tickets – Requests
# ---------------------------------------------------------------------------


class ChangeTicketStatusRequest(BaseModel):
    """Update a support ticket's status."""

    status: str = Field(..., description="open | in_progress | resolved")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"open", "in_progress", "resolved"}
        v = v.strip().lower()
        if v not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(sorted(allowed))}")
        return v


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class AdminUserResponse(BaseModel):
    """Full user profile for admin views."""

    id: str
    first_name: str
    last_name: str
    username: Optional[str] = None
    email: str
    phone_number: Optional[str] = None
    address: Optional[str] = None
    avatar_url: Optional[str] = None
    id_verification_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    role: str
    vendor_verified: bool = False
    vendor_verified_at: Optional[datetime] = None
    id_verification_status: str = "none"
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AdminPropertyResponse(BaseModel):
    """Property listing with owner info for admin views."""

    id: str
    user_id: str
    name: str
    type: str
    location: str
    description: Optional[str] = None
    beds: int
    baths: int
    guests: Optional[Dict[str, Any]] = None
    price: float
    photos: Optional[List[str]] = None
    video_url: Optional[str] = None
    amenities: Optional[List[str]] = None
    payout_account: Optional[str] = None
    payout_bank: Optional[str] = None
    payout_name: Optional[str] = None
    status: str
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Owner info (populated by service)
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None

    model_config = {"from_attributes": True}


class AdminRideResponse(BaseModel):
    """Ride listing with owner info for admin views."""

    id: str
    user_id: str
    ride_type: str
    seat_count: int
    door_count: int
    pickup_location: str
    pickup_latitude: Optional[float] = None
    pickup_longitude: Optional[float] = None
    adult_passenger_count: int
    children_passenger_count: int
    infant_passenger_count: int
    features: Optional[List[str]] = None
    price: float
    currency: str
    status: str
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Owner info (populated by service)
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    photos: Optional[List[str]] = None

    model_config = {"from_attributes": True}


class DashboardStatsResponse(BaseModel):
    """Aggregated stats for the admin dashboard."""

    total_users: int = 0
    total_vendors: int = 0
    total_superadmins: int = 0
    verified_vendors: int = 0
    pending_vendor_verifications: int = 0
    total_properties: int = 0
    active_properties: int = 0
    pending_properties: int = 0
    total_rides: int = 0
    published_rides: int = 0
    pending_rides: int = 0
    total_tickets: int = 0
    open_tickets: int = 0
