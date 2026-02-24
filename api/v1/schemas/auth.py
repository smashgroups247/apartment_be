"""
Authentication Pydantic Schemas
File: api/v1/schemas/auth.py
"""

import re
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class UserRegisterRequest(BaseModel):
    """Schema for user registration"""

    first_name: str = Field(..., min_length=1, max_length=100, examples=["John"])
    last_name: str = Field(..., min_length=1, max_length=100, examples=["Doe"])
    username: Optional[str] = Field(None, min_length=3, max_length=100, examples=["johndoe"])
    email: EmailStr = Field(..., examples=["john@example.com"])
    password: str = Field(..., min_length=8, max_length=128, examples=["Str0ng!Pass"])

    @field_validator("password")
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

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username may only contain letters, digits, and underscores.")
        return v.lower()

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower()


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


class UserLoginRequest(BaseModel):
    """Schema for user login (email or username)"""

    login: str = Field(
        ...,
        description="Email address or username",
        examples=["john@example.com"],
    )
    password: str = Field(..., min_length=1, examples=["Str0ng!Pass"])


# ---------------------------------------------------------------------------
# Token responses
# ---------------------------------------------------------------------------


class TokenResponse(BaseModel):
    """JWT token pair response schema"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token lifetime in seconds")


class AccessTokenResponse(BaseModel):
    """Schema returned from /auth/refresh"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


# ---------------------------------------------------------------------------
# Refresh token request
# ---------------------------------------------------------------------------


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token endpoint"""

    refresh_token: str


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


class LogoutRequest(BaseModel):
    """Schema for logout endpoint"""

    refresh_token: str


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------


class ForgotPasswordRequest(BaseModel):
    """Schema to request a password reset email"""

    email: EmailStr

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower()


class ResetPasswordRequest(BaseModel):
    """Schema for resetting the password using a token"""

    reset_token: str = Field(..., description="Token received via email")
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
# User public profile (response)
# ---------------------------------------------------------------------------


class UserResponse(BaseModel):
    """Public user profile returned in API responses"""

    id: str
    first_name: str
    last_name: str
    username: Optional[str]
    email: str
    is_active: bool
    is_verified: bool
    role: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Sign-in stub (kept for backward compat with existing route)
# ---------------------------------------------------------------------------


class SignInRequest(BaseModel):
    """Legacy sign-in schema (phone-number OTP stub)"""

    phone_number: str = Field(..., min_length=10, max_length=20)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        v = v.strip().replace(" ", "").replace("-", "")
        if not re.match(r"^\+?[1-9]\d{1,14}$", v):
            raise ValueError("Invalid phone number format")
        if not v.startswith("+"):
            if v.startswith("0"):
                v = "+234" + v[1:]
            elif len(v) == 10:
                v = "+234" + v
            else:
                v = "+" + v
        return v
