"""Payment Method Router"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.database import get_db
from api.utils.jwt_handler import get_current_user
from api.utils.success_response import success_response
from api.v1.models.users import User
from api.v1.schemas.payment_method import AddPaymentMethodRequest, PaymentMethodResponse
from api.v1.services.payment_method import payment_method_service

payment_method = APIRouter(prefix="/payment-methods", tags=["Payment Methods"])


@payment_method.get("", status_code=status.HTTP_200_OK)
async def get_payment_methods(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await payment_method_service.get_user_payment_methods(
        user_id=current_user.id, db=db
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Payment methods retrieved successfully.",
        data=[PaymentMethodResponse.model_validate(m).model_dump() for m in data],
    )


@payment_method.post("", status_code=status.HTTP_201_CREATED)
async def add_payment_method(
    schema: AddPaymentMethodRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await payment_method_service.add_payment_method(
        user_id=current_user.id, schema=schema, db=db
    )
    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Payment method added successfully.",
        data=PaymentMethodResponse.model_validate(data).model_dump(),
    )


@payment_method.delete("/{payment_method_id}", status_code=status.HTTP_200_OK)
async def remove_payment_method(
    payment_method_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await payment_method_service.remove_payment_method(
        payment_method_id=payment_method_id, user_id=current_user.id, db=db
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Payment method removed successfully.",
        data=None,
    )