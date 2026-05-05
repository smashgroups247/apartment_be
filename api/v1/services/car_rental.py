"""Car Rental Service"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from api.v1.models.car_rental import CarRental


class CarRentalService:

    async def get_user_car_rentals(self, user_id: str, db: AsyncSession, page: int = 1, size: int = 10):
        offset = (page - 1) * size

        count_result = await db.execute(
            select(func.count()).select_from(CarRental).where(CarRental.user_id == user_id)
        )
        total = count_result.scalar()

        result = await db.execute(
            select(CarRental)
            .where(CarRental.user_id == user_id)
            .order_by(CarRental.created_at.desc())
            .offset(offset)
            .limit(size)
        )
        car_rentals = result.scalars().all()

        return {
            "items": car_rentals,
            "total": total,
            "page": page,
            "size": size,
            "pages": -(-total // size) if total > 0 else 1,
        }

    async def get_car_rental_by_id(self, rental_id: str, user_id: str, db: AsyncSession):
        result = await db.execute(
            select(CarRental).where(CarRental.id == rental_id)
        )
        rental = result.scalars().first()

        if not rental:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car rental not found")

        if rental.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        return rental

    async def cancel_car_rental(self, rental_id: str, user_id: str, db: AsyncSession):
        rental = await self.get_car_rental_by_id(rental_id, user_id, db)

        if rental.status not in ("pending", "confirmed"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel a rental with status '{rental.status}'"
            )

        rental.status = "cancelled"
        await db.commit()
        await db.refresh(rental)
        return rental


car_rental_service = CarRentalService()