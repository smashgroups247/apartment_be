"""
Support Ticket Pydantic Schemas
File: api/v1/schemas/support.py
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

# Valid ticket categories
VALID_CATEGORIES = {
    "Booking Issue",
    "Payment Issue",
    "Account Issue",
    "Other",
}


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

class CreateTicketRequest(BaseModel):
    """Schema for submitting a new support ticket."""

    subject: str = Field(..., min_length=3, max_length=255, description="Brief summary of the issue")
    category: str = Field(..., description="One of: Booking Issue, Payment Issue, Account Issue, Other")
    message: str = Field(..., min_length=10, max_length=5000, description="Full description of the issue")

    @field_validator("subject")
    @classmethod
    def strip_subject(cls, v: str) -> str:
        return v.strip()

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in VALID_CATEGORIES:
            raise ValueError(
                f"Invalid category. Must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
            )
        return v

    @field_validator("message")
    @classmethod
    def strip_message(cls, v: str) -> str:
        return v.strip()


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

class TicketResponse(BaseModel):
    """Full ticket object returned in API responses."""

    id: str
    user_id: str
    subject: str
    category: str
    message: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TicketListResponse(BaseModel):
    """Wrapper for a list of tickets with a total count."""

    total: int
    tickets: List[TicketResponse]