"""Payment Method Schemas"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class AddPaymentMethodRequest(BaseModel):
    card_number: str
    expiration: str
    cvv: str
    country: str = "Nigeria"


class PaymentMethodResponse(BaseModel):
    id: str
    user_id: str
    card_number: str
    last_four: str
    card_type: str
    expiration: str
    country: str
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedPaymentMethodsResponse(BaseModel):
    items: List[PaymentMethodResponse]
    total: int
    page: int
    size: int
    pages: int