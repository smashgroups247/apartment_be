"""Payment Method Service"""

import hashlib
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.v1.models.payment_method import PaymentMethod
from api.v1.schemas.payment_method import AddPaymentMethodRequest


def detect_card_type(card_number: str) -> str:
    number = card_number.replace(" ", "")
    if number.startswith("5") or number.startswith("2"):
        return "mastercard"
    elif number.startswith("4"):
        return "visa"
    elif number.startswith("650") or number.startswith("506") or number.startswith("6500"):
        return "verve"
    return "unknown"


def mask_card_number(card_number: str) -> str:
    number = card_number.replace(" ", "")
    last_four = number[-4:]
    return f"{number[:4]} **** **** {last_four}"


def hash_cvv(cvv: str) -> str:
    return hashlib.sha256(cvv.encode()).hexdigest()


class PaymentMethodService:

    async def add_payment_method(self, user_id: str, schema: AddPaymentMethodRequest, db: AsyncSession):
        number = schema.card_number.replace(" ", "")

        if len(number) < 13 or len(number) > 19:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid card number"
            )

        last_four = number[-4:]
        card_type = detect_card_type(number)
        masked = mask_card_number(number)
        hashed_cvv = hash_cvv(schema.cvv)

        # Check if card already exists for this user
        existing = await db.execute(
            select(PaymentMethod).where(
                PaymentMethod.user_id == user_id,
                PaymentMethod.last_four == last_four,
                PaymentMethod.card_type == card_type,
            )
        )
        if existing.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This card has already been added"
            )

        payment_method = PaymentMethod(
            user_id=user_id,
            card_number=masked,
            last_four=last_four,
            card_type=card_type,
            expiration=schema.expiration,
            cvv=hashed_cvv,
            country=schema.country,
            is_default=False,
        )
        db.add(payment_method)
        await db.commit()
        await db.refresh(payment_method)
        return payment_method

    async def get_user_payment_methods(self, user_id: str, db: AsyncSession):
        result = await db.execute(
            select(PaymentMethod)
            .where(PaymentMethod.user_id == user_id)
            .order_by(PaymentMethod.created_at.desc())
        )
        return result.scalars().all()

    async def remove_payment_method(self, payment_method_id: str, user_id: str, db: AsyncSession):
        result = await db.execute(
            select(PaymentMethod).where(
                PaymentMethod.id == payment_method_id,
                PaymentMethod.user_id == user_id,
            )
        )
        payment_method = result.scalars().first()

        if not payment_method:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment method not found"
            )

        await db.delete(payment_method)
        await db.commit()


payment_method_service = PaymentMethodService()