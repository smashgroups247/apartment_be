"""Apartment Service"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from api.v1.models.apartment import Apartment
from api.v1.schemas.apartment import ApartmentCreate, ApartmentUpdate


class ApartmentService:

    async def create_apartment(self, apartment_data: ApartmentCreate, user_id: str, db: AsyncSession):
        apartment = Apartment(
            user_id=user_id,
            **apartment_data.model_dump()
        )
        db.add(apartment)
        await db.commit()
        await db.refresh(apartment)
        return apartment

    async def get_user_apartments(self, user_id: str, db: AsyncSession, page: int = 1, size: int = 10):
        offset = (page - 1) * size

        count_result = await db.execute(
            select(func.count()).select_from(Apartment).where(Apartment.user_id == user_id)
        )
        total = count_result.scalar()

        result = await db.execute(
            select(Apartment)
            .where(Apartment.user_id == user_id)
            .order_by(Apartment.created_at.desc())
            .offset(offset)
            .limit(size)
        )
        apartments = result.scalars().all()

        return {
            "items": apartments,
            "total": total,
            "page": page,
            "size": size,
            "pages": -(-total // size) if total > 0 else 1,
        }

    async def get_all_apartments(self, db: AsyncSession, page: int = 1, size: int = 10):
        offset = (page - 1) * size

        count_result = await db.execute(select(func.count()).select_from(Apartment))
        total = count_result.scalar()

        result = await db.execute(
            select(Apartment)
            .order_by(Apartment.created_at.desc())
            .offset(offset)
            .limit(size)
        )
        apartments = result.scalars().all()

        return {
            "items": apartments,
            "total": total,
            "page": page,
            "size": size,
            "pages": -(-total // size) if total > 0 else 1,
        }

    async def get_apartment_by_id(self, apartment_id: str, db: AsyncSession):
        result = await db.execute(select(Apartment).where(Apartment.id == apartment_id))
        apartment = result.scalars().first()

        if not apartment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apartment not found")

        return apartment

    async def update_apartment(self, apartment_id: str, update_data: ApartmentUpdate, user_id: str, db: AsyncSession):
        apartment = await self.get_apartment_by_id(apartment_id, db)

        if apartment.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(apartment, key, value)

        await db.commit()
        await db.refresh(apartment)
        return apartment

    async def delete_apartment(self, apartment_id: str, user_id: str, db: AsyncSession):
        apartment = await self.get_apartment_by_id(apartment_id, db)

        if apartment.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        await db.delete(apartment)
        await db.commit()
        return True


apartment_service = ApartmentService()
