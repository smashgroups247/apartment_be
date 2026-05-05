"""Payment Service"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from api.v1.models.payment import Payment
from api.v1.schemas.payment import CreatePaymentRequest


class PaymentService:

    async def create_payment(self, user_id: str, schema: CreatePaymentRequest, db: AsyncSession):
        existing = await db.execute(
            select(Payment).where(Payment.reference == schema.reference)
        )
        if existing.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment reference already exists"
            )

        payment = Payment(
            user_id=user_id,
            reference=schema.reference,
            purpose=schema.purpose,
            amount=schema.amount,
            status="pending",
            mode=schema.mode,
            booking_id=schema.booking_id,
            car_rental_id=schema.car_rental_id,
        )
        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        return payment

    async def verify_payment(self, reference: str, user_id: str, db: AsyncSession):
        result = await db.execute(
            select(Payment).where(
                Payment.reference == reference,
                Payment.user_id == user_id
            )
        )
        payment = result.scalars().first()

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        # Manually mark as success for now (Paystack integration later)
        payment.status = "success"
        payment.mode = "Card"

        await db.commit()
        await db.refresh(payment)
        return payment

    async def get_user_payments(self, user_id: str, db: AsyncSession, page: int = 1, size: int = 10):
        offset = (page - 1) * size

        query = select(Payment).where(Payment.user_id == user_id)

        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()

        result = await db.execute(
            query.order_by(Payment.created_at.desc()).offset(offset).limit(size)
        )
        payments = result.scalars().all()

        return {
            "items": payments,
            "total": total,
            "page": page,
            "size": size,
            "pages": -(-total // size) if total > 0 else 1,
        }

    async def get_payment_by_id(self, payment_id: str, user_id: str, db: AsyncSession):
        result = await db.execute(
            select(Payment).where(
                Payment.id == payment_id,
                Payment.user_id == user_id
            )
        )
        payment = result.scalars().first()

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        return payment

    async def handle_webhook(self, reference: str, paystack_status: str, channel: str, db: AsyncSession):
        result = await db.execute(
            select(Payment).where(Payment.reference == reference)
        )
        payment = result.scalars().first()

        if not payment:
            return None

        channel_map = {
            "card": "Card",
            "bank": "Transfer",
            "ussd": "USSD",
            "qr": "QR",
            "mobile_money": "Mobile Money",
            "bank_transfer": "Transfer",
        }

        if paystack_status == "success":
            payment.status = "success"
        else:
            payment.status = "failed"

        payment.mode = channel_map.get(channel, channel.title() if channel else "Paystack")

        await db.commit()
        await db.refresh(payment)
        return payment


payment_service = PaymentService()