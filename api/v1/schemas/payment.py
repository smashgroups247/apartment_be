"""Payment Schemas"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class CreatePaymentRequest(BaseModel):
    reference: str
    purpose: str  # "apartment" or "car_rental"
    amount: float
    mode: Optional[str] = None
    booking_id: Optional[str] = None
    car_rental_id: Optional[str] = None


class VerifyPaymentRequest(BaseModel):
    reference: str


class PaymentResponse(BaseModel):
    id: str
    user_id: str
    reference: str
    purpose: str
    amount: float
    status: str
    mode: Optional[str] = None
    booking_id: Optional[str] = None
    car_rental_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedPaymentsResponse(BaseModel):
    items: List[PaymentResponse]
    total: int
    page: int
    size: int
    pages: int