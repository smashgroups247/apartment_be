from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.v1.models.review import Review
from api.v1.models.booking import Booking
from api.v1.models.car_rental import CarRental
from api.v1.schemas.review import CreateReviewRequest


class ReviewService:

    async def create_review(self, schema: CreateReviewRequest, user_id: str, db: AsyncSession):

        # Check booking exists depending on type
        if schema.booking_type == "stay":
            result = await db.execute(
                select(Booking).where(Booking.id == schema.booking_id)
            )
            booking = result.scalars().first()

        else:
            result = await db.execute(
                select(CarRental).where(CarRental.id == schema.booking_id)
            )
            booking = result.scalars().first()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )

        if booking.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Check if review already exists
        existing = await db.execute(
            select(Review).where(
                Review.booking_id == schema.booking_id,
                Review.booking_type == schema.booking_type
            )
        )

        if existing.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Review already exists for this booking"
            )

        # Create review
        review = Review(
            user_id=user_id,
            booking_id=schema.booking_id,
            booking_type=schema.booking_type,
            review_text=schema.review_text,
            rating=schema.rating,
            item_image=schema.item_image,
            item_name=schema.item_name,
        )

        db.add(review)
        await db.commit()
        await db.refresh(review)

        return review


    async def get_user_reviews(self, user_id: str, db: AsyncSession, booking_type: str = None):
        query = select(Review).where(Review.user_id == user_id)

        if booking_type:
            query = query.where(Review.booking_type == booking_type)

        result = await db.execute(
            query.order_by(Review.created_at.desc())
        )

        return result.scalars().all()


review_service = ReviewService()