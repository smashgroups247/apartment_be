"""
User Pydantic Schemas
File: api/v1/schemas/users.py
"""

import re
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# Update Profile
# ---------------------------------------------------------------------------

class UpdateProfileRequest(BaseModel):
    """Schema for updating user profile fields. All fields are optional."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = Field(None)
    phone_number: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError(
                "Username may only contain letters, digits, and underscores."
            )
        return v.lower()

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        cleaned = v.strip().replace(" ", "").replace("-", "")
        if not re.match(r"^\+?[1-9]\d{6,14}$", cleaned):
            raise ValueError("Invalid phone number format.")
        return cleaned

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_names(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return v.strip()


# ---------------------------------------------------------------------------
# Change Password
# ---------------------------------------------------------------------------

class ChangePasswordRequest(BaseModel):
    """Schema for changing the authenticated user's password."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character.")
        return v


# ---------------------------------------------------------------------------
# User Profile Response
# ---------------------------------------------------------------------------

class UserProfileResponse(BaseModel):
    """Full user profile returned by /users/me and update endpoints."""

    id: str
    first_name: str
    last_name: str
    username: Optional[str]
    email: str
    phone_number: Optional[str]
    address: Optional[str]
    avatar_url: Optional[str]
    id_verification_url: Optional[str]
    is_active: bool
    is_verified: bool
    role: str
    vendor_verified: bool = False
    vendor_verified_at: Optional[datetime] = None
    id_verification_status: str = "none"

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Vendor Status Response
# ---------------------------------------------------------------------------

class VendorStatusResponse(BaseModel):
    """
    Returned by GET /users/me/vendor-status and POST /users/request-vendor.
    Contains all fields the frontend needs for the VendorCriteriaModal.
    """

    role: str
    vendor_verified: bool
    id_verification_status: str          # "none" | "pending" | "approved" | "rejected"
    id_verification_url: Optional[str]   # None if no ID uploaded yet
    is_verified: bool                    # email verified
    phone_number: Optional[str]          # for phone check (auto-pass for now)
    address: Optional[str]              # for address check (auto-pass for now)

    model_config = {"from_attributes": True}