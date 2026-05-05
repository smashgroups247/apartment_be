"""Payment Router"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.database import get_db
from api.utils.jwt_handler import get_current_user
from api.utils.success_response import success_response
from api.v1.models.users import User
from api.v1.schemas.payment import CreatePaymentRequest, VerifyPaymentRequest, PaymentResponse
from api.v1.services.payment import payment_service

payment = APIRouter(prefix="/payments", tags=["Payments"])


@payment.get("", status_code=status.HTTP_200_OK)
async def get_payments(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await payment_service.get_user_payments(
        user_id=current_user.id, db=db, page=page, size=size
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Payments retrieved successfully.",
        data=data,
    )


@payment.post("", status_code=status.HTTP_201_CREATED)
async def create_payment(
    schema: CreatePaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await payment_service.create_payment(
        user_id=current_user.id, schema=schema, db=db
    )
    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Payment created successfully.",
        data=PaymentResponse.model_validate(data).model_dump(),
    )


@payment.post("/verify", status_code=status.HTTP_200_OK)
async def verify_payment(
    schema: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await payment_service.verify_payment(
        reference=schema.reference, user_id=current_user.id, db=db
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Payment verified successfully.",
        data=PaymentResponse.model_validate(data).model_dump(),
    )


@payment.post("/webhook", status_code=status.HTTP_200_OK)
async def payment_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    payload = await request.json()
    event = payload.get("event")

    if event == "charge.success":
        data = payload.get("data", {})
        reference = data.get("reference")
        paystack_status = data.get("status")
        channel = data.get("channel", "")

        await payment_service.handle_webhook(
            reference=reference,
            paystack_status=paystack_status,
            channel=channel,
            db=db
        )

    return {"status": "ok"}


@payment.get("/{payment_id}", status_code=status.HTTP_200_OK)
async def get_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await payment_service.get_payment_by_id(
        payment_id=payment_id, user_id=current_user.id, db=db
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Payment retrieved successfully.",
        data=PaymentResponse.model_validate(data).model_dump(),
    )